import time
from database.connection import db
from database.models import Queue, QueueCounter, Ticket
from utils.ticket import format_ticket_number
from sqlalchemy.exc import IntegrityError, OperationalError
from services import notification_service

MAX_COUNTER_INIT_RETRIES = 5


def _get_or_create_counter_locked(queue_id: int) -> QueueCounter:
    """
    Returns the QueueCounter row for this queue, ROW-LOCKED (FOR UPDATE),
    creating it first if it doesn't exist yet.

    IMPORTANT: whether this call creates the row itself, another
    concurrent call creates it, or it already existed, this function
    ALWAYS re-acquires the row through SELECT ... FOR UPDATE before
    returning it - never returns a just-created row directly. A
    freshly INSERTed-and-committed row has no lock held on it (commit
    releases locks), so incrementing it without re-locking first would
    let a second concurrent request read the same last_number before
    the first request's increment is visible - producing duplicate
    ticket numbers. Looping back to the top and re-SELECTing WITH the
    lock is what actually closes that gap.
    """
    last_error = None
    for attempt in range(MAX_COUNTER_INIT_RETRIES):
        counter = (
            db.session.query(QueueCounter)
            .filter_by(queue_id=queue_id)
            .with_for_update()
            .first()
        )
        if counter is not None:
            return counter  # safely locked - fine to increment now

        # Row doesn't exist yet. Try to create it, but regardless of
        # whether this succeeds or another request beats us to it,
        # DO NOT return here - loop back to the top so the row gets
        # picked up through the locked SELECT above instead.
        try:
            db.session.add(QueueCounter(queue_id=queue_id, last_number=0))
            db.session.commit()
        except (IntegrityError, OperationalError) as e:
            db.session.rollback()
            last_error = e

        time.sleep(0.02 * (attempt + 1))  # brief backoff before re-checking

    raise RuntimeError(
        f"Could not initialize queue_counters for queue_id={queue_id} "
        f"after {MAX_COUNTER_INIT_RETRIES} attempts"
    ) from last_error


def generate_ticket(queue: Queue, user_id: int) -> Ticket:
    """
    Atomically issues the next ticket number for a queue.

    Uses SELECT ... FOR UPDATE (via _get_or_create_counter_locked above)
    to lock the queue's counter row for the duration of the transaction,
    so two students joining the same queue at the same moment cannot
    both receive e.g. "FIN-102". The second request waits for the row
    lock to release, then correctly gets 103.
    """
    counter = _get_or_create_counter_locked(queue.id)

    counter.last_number += 1
    next_number = counter.last_number

    ticket = Ticket(
        queue_id=queue.id,
        user_id=user_id,
        sequence_number=next_number,
        ticket_number=format_ticket_number(queue.prefix, next_number),
        status="waiting",
    )
    db.session.add(ticket)
    db.session.commit()
    return ticket


def get_position(ticket: Ticket) -> int:
    """
    Position = number of still-waiting tickets in the same queue created
    before this one, plus 1. Recalculated on demand (never stored) so
    it's always correct, even the instant after another ticket ahead of
    it is served/skipped/cancelled.
    """
    if ticket.status != "waiting":
        return 0

    ahead = Ticket.query.filter(
        Ticket.queue_id == ticket.queue_id,
        Ticket.status == "waiting",
        Ticket.sequence_number < ticket.sequence_number,
    ).count()
    return ahead + 1


def join_queue(queue_id: int, user_id: int):
    """Returns (result_dict, status_code)."""
    queue = Queue.query.get(queue_id)
    if not queue:
        return {"error": "Queue not found"}, 404
    if queue.status != "open":
        return {"error": f"This queue is currently {queue.status} and not accepting new tickets"}, 409

    existing = Ticket.query.filter_by(queue_id=queue_id, user_id=user_id, status="waiting").first()
    if existing:
        return {
            "error": "You already have an active ticket in this queue",
            "ticket": existing.to_dict(),
        }, 409

    ticket = generate_ticket(queue, user_id)
    data = ticket.to_dict()
    data["position"] = get_position(ticket)

    # A new ticket can land directly in proximity tier 1-3 if the queue
    # is already short - check immediately rather than waiting for the
    # next call-next/cancel event to notice. Lives here (service layer),
    # not in the route, so this fires no matter who calls join_queue().
    notification_service.check_proximity_for_queue(queue_id)

    return {"message": "Ticket issued", "ticket": data}, 201


def cancel_ticket(ticket_id: int, user_id: int):
    """Returns (result_dict, status_code). Only the ticket's own owner can cancel it."""
    ticket = Ticket.query.get(ticket_id)
    if not ticket or ticket.user_id != user_id:
        return {"error": "Ticket not found"}, 404
    if ticket.status != "waiting":
        return {"error": f"Cannot cancel a ticket that is already {ticket.status}"}, 409

    queue_id = ticket.queue_id
    ticket.status = "cancelled"
    db.session.commit()

    # Cancelling removes a ticket from 'waiting', shifting everyone behind
    # it up by one position - re-check whether that puts anyone into a
    # new proximity tier they haven't been notified for yet.
    notification_service.check_proximity_for_queue(queue_id)

    return {"message": "Ticket cancelled", "ticket": ticket.to_dict()}, 200


def get_ticket_status(ticket_id: int, user_id: int):
    """Returns (result_dict, status_code). Includes the live-calculated position."""
    ticket = Ticket.query.get(ticket_id)
    if not ticket or ticket.user_id != user_id:
        return {"error": "Ticket not found"}, 404

    data = ticket.to_dict()
    data["position"] = get_position(ticket)
    return {"ticket": data}, 200


def list_active_tickets_for_user(user_id: int):
    """All of a student's currently-waiting tickets, across every queue, with live positions."""
    tickets = Ticket.query.filter_by(user_id=user_id, status="waiting").all()
    result = []
    for t in tickets:
        d = t.to_dict()
        d["position"] = get_position(t)
        d["queue_name"] = t.queue.queue_name
        result.append(d)
    return result


def list_queues():
    """All queues with a live waiting_count, for the student-facing queue list."""
    return [q.to_dict(include_counts=True) for q in Queue.query.all()]