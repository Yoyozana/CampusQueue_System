from datetime import datetime

from database.connection import db
from database.models import Queue, Ticket, ServicePoint, AdminAction, User
from services import notification_service


def _log_action(admin_id: int, description: str):
    db.session.add(AdminAction(admin_id=admin_id, action_description=description))


def get_admin_current_queue(admin_id: int):
    """Which queue (if any) this admin is currently managing this session."""
    return Queue.query.filter_by(current_admin_id=admin_id).first()


def list_queues_for_selection():
    """
    Queues an admin can pick from at login, showing whether each is
    already being managed by someone this session (current_admin_id set)
    so the frontend can grey out queues someone else is actively working.
    """
    return [q.to_dict() for q in Queue.query.all()]


def select_todays_queue(admin_id: int, queue_id: int):
    """
    An admin picks which queue they're managing for this session.
    Clears any queue they were previously managing first (an admin can
    only actively manage one queue at a time), then claims the new one -
    but only if nobody else currently has it claimed.

    Returns (result_dict, status_code).
    """
    queue = Queue.query.get(queue_id)
    if not queue:
        return {"error": "Queue not found"}, 404

    if queue.current_admin_id is not None and queue.current_admin_id != admin_id:
        return {"error": "This queue is already being managed by another admin this session"}, 409

    # Release whatever queue this admin was previously managing.
    previous = get_admin_current_queue(admin_id)
    if previous and previous.id != queue.id:
        previous.current_admin_id = None
        _log_action(admin_id, f"Switched away from {previous.queue_name}")

    queue.current_admin_id = admin_id
    _log_action(admin_id, f"Selected {queue.queue_name} for this session")
    db.session.commit()

    return {"message": f"Now managing {queue.queue_name}", "queue": queue.to_dict()}, 200


def release_todays_queue(admin_id: int):
    """Called on logout or 'Switch Queue' - clears this admin's current session claim."""
    queue = get_admin_current_queue(admin_id)
    if queue:
        queue.current_admin_id = None
        _log_action(admin_id, f"Released {queue.queue_name} (logout/switch)")
        db.session.commit()
    return {"message": "Session queue released"}, 200


def _require_managing_admin(queue: Queue, admin_id: int):
    """Returns an error tuple if this admin isn't the one currently managing this queue, else None."""
    if queue.current_admin_id != admin_id:
        return {"error": "You are not currently managing this queue. Select it first."}, 403
    return None


def list_service_points():
    """
    All physical desks/counters, with which queue each is fixed to and
    what ticket (if any) each is currently serving.
    """
    return [sp.to_dict() for sp in ServicePoint.query.all()]


def list_all_tickets(limit: int = 200):
    """
    Every ticket across every queue, most recent first - backs an admin
    'Tickets' page showing the full picture, not just one queue at a time
    (that's what get_queue_activity is for). Includes the queue's name
    directly on each row so the frontend doesn't need a second lookup.
    """
    tickets = Ticket.query.order_by(Ticket.joined_at.desc()).limit(limit).all()
    result = []
    for t in tickets:
        d = t.to_dict()
        d["queue_name"] = t.queue.queue_name
        d["student_name"] = t.user.full_name
        result.append(d)
    return result


def list_all_users():
    """
    Full user roster (students and admins) - backs an admin 'Users' page.
    User.to_dict() already excludes password_hash, so nothing sensitive
    leaks here.
    """
    return [u.to_dict() for u in User.query.order_by(User.role, User.full_name).all()]


def get_queue_activity(queue_id: int):
    """Live monitoring view: the currently-called ticket and everyone still waiting, in order."""
    queue = Queue.query.get(queue_id)
    if not queue:
        return {"error": "Queue not found"}, 404

    waiting = (
        Ticket.query.filter_by(queue_id=queue_id, status="waiting")
        .order_by(Ticket.sequence_number.asc())
        .all()
    )
    called = (
        Ticket.query.filter_by(queue_id=queue_id, status="called")
        .order_by(Ticket.called_at.asc())
        .all()
    )
    return {
        "queue": queue.to_dict(),
        "waiting": [t.to_dict() for t in waiting],
        "called": [t.to_dict() for t in called],
    }, 200


def call_next(admin_id: int, queue_id: int):
    """
    Pulls the next WAITING ticket (lowest sequence_number) for this queue,
    marks it CALLED, assigns it to the queue's fixed service point, and
    notifies the student.
    """
    queue = Queue.query.get(queue_id)
    if not queue:
        return {"error": "Queue not found"}, 404

    auth_error = _require_managing_admin(queue, admin_id)
    if auth_error:
        return auth_error

    if queue.status != "open":
        return {"error": f"Queue is currently {queue.status} - reopen it to call the next student"}, 409

    service_point = ServicePoint.query.filter_by(queue_id=queue_id).first()
    if not service_point:
        return {"error": "No service point (desk) is assigned to this queue"}, 400

    next_ticket = (
        Ticket.query.filter_by(queue_id=queue_id, status="waiting")
        .order_by(Ticket.sequence_number.asc())
        .first()
    )
    if not next_ticket:
        return {"message": "No students waiting in this queue"}, 200

    next_ticket.status = "called"
    next_ticket.called_at = datetime.utcnow()
    service_point.current_ticket_id = next_ticket.id

    _log_action(admin_id, f"Called {next_ticket.ticket_number} in {queue.queue_name}")
    notification_service.notify(
        next_ticket.user_id, next_ticket.id,
        f"Your turn is approaching. Ticket {next_ticket.ticket_number} has been called "
        f"- please proceed to {service_point.point_name}."
    )
    db.session.commit()

    # Pulling this ticket out of 'waiting' shifts everyone behind it up
    # by one position - re-check whether that puts anyone into a new
    # proximity tier (#1/#2/#3) they haven't been notified for yet.
    notification_service.check_proximity_for_queue(queue_id)

    return {"message": "Ticket called", "ticket": next_ticket.to_dict()}, 200


def mark_served(admin_id: int, ticket_id: int):
    """Marks a called ticket as served, clearing the desk it was at."""
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return {"error": "Ticket not found"}, 404

    queue = Queue.query.get(ticket.queue_id)
    auth_error = _require_managing_admin(queue, admin_id)
    if auth_error:
        return auth_error

    if ticket.status != "called":
        return {"error": "Only a called ticket can be marked served"}, 409

    ticket.status = "served"
    ticket.served_at = datetime.utcnow()

    service_point = ServicePoint.query.filter_by(current_ticket_id=ticket.id).first()
    if service_point:
        service_point.current_ticket_id = None

    _log_action(admin_id, f"Served {ticket.ticket_number} in {queue.queue_name}")
    notification_service.notify(ticket.user_id, ticket.id, f"You have been served for {ticket.ticket_number}. Thank you!")
    db.session.commit()

    return {"message": "Ticket served", "ticket": ticket.to_dict()}, 200


def skip_ticket(admin_id: int, ticket_id: int):
    """Marks a called-but-unresponsive ticket as skipped (no-show)."""
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return {"error": "Ticket not found"}, 404

    queue = Queue.query.get(ticket.queue_id)
    auth_error = _require_managing_admin(queue, admin_id)
    if auth_error:
        return auth_error

    if ticket.status != "called":
        return {"error": "Only a called ticket can be skipped"}, 409

    ticket.status = "skipped"
    ticket.served_at = datetime.utcnow()  # reused as "resolved at" for skips too

    service_point = ServicePoint.query.filter_by(current_ticket_id=ticket.id).first()
    if service_point:
        service_point.current_ticket_id = None

    _log_action(admin_id, f"Skipped {ticket.ticket_number} in {queue.queue_name} (no-show)")
    notification_service.notify(ticket.user_id, ticket.id,
            f"You missed your turn for {ticket.ticket_number}. Please rejoin the queue.")
    db.session.commit()

    return {"message": "Ticket skipped", "ticket": ticket.to_dict()}, 200


def set_queue_status(admin_id: int, queue_id: int, new_status: str):
    """
    Transitions a queue between open / paused / closed. Closing a queue
    auto-cancels all still-waiting tickets and notifies those students,
    so no one is left waiting on a queue that no longer exists.
    """
    if new_status not in ("open", "paused", "closed"):
        return {"error": "status must be one of: open, paused, closed"}, 400

    queue = Queue.query.get(queue_id)
    if not queue:
        return {"error": "Queue not found"}, 404

    auth_error = _require_managing_admin(queue, admin_id)
    if auth_error:
        return auth_error

    queue.status = new_status
    action_verb = {"open": "Opened", "paused": "Paused", "closed": "Closed"}[new_status]
    _log_action(admin_id, f"{action_verb} {queue.queue_name}")

    if new_status == "closed":
        waiting_tickets = Ticket.query.filter_by(queue_id=queue.id, status="waiting").all()
        for t in waiting_tickets:
            t.status = "cancelled"
            notification_service.notify(t.user_id, t.id,
                    f"{queue.queue_name} has been closed. Your ticket {t.ticket_number} was cancelled.")

    db.session.commit()
    return {"message": f"Queue status set to {new_status}", "queue": queue.to_dict()}, 200


def list_admin_actions(limit: int = 20):
    actions = AdminAction.query.order_by(AdminAction.action_time.desc()).limit(limit).all()
    return [a.to_dict() for a in actions]