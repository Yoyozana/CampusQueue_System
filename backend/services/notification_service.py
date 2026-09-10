from database.connection import db
from database.models import Ticket, Notification
from utils.ticket import get_proximity_tier

# Matches the exact table: #1 -> "it's your turn", #2 -> "almost next",
# #3 -> "getting closer". #4+ gets no urgent notification at all.
PROXIMITY_MESSAGES = {
    1: ("🔴", "It's your turn! Please proceed to the service desk now."),
    2: ("🟠", "You're almost next. Please make your way closer to the service area."),
    3: ("🟡", "You're getting closer. Your turn is expected soon."),
}


def notify(user_id: int, ticket_id: int, message: str):
    n = Notification(user_id=user_id, ticket_id=ticket_id, message=message)
    db.session.add(n)
    return n


def check_proximity_for_queue(queue_id: int):
    """
    Recomputes live position for every still-waiting ticket in this queue
    and sends a tiered proximity notification (#1/#2/#3) exactly once per
    tier, using Ticket.notified_tier to avoid ever repeating the same
    tier's notification. Call this after any event that shifts positions
    within a queue - currently that's admin_service.call_next() (pulling
    a ticket out of 'waiting' shifts everyone behind it up by one) and
    queue_service.cancel_ticket() (same reason).

    Deliberately does NOT import queue_service, to avoid a circular
    import (queue_service and admin_service both need to call this) -
    it queries Ticket directly instead.
    """
    waiting = (
        Ticket.query.filter_by(queue_id=queue_id, status="waiting")
        .order_by(Ticket.sequence_number.asc())
        .all()
    )
    for index, ticket in enumerate(waiting):
        position = index + 1
        tier = get_proximity_tier(position)
        if tier and tier != ticket.notified_tier:
            icon, message_text = PROXIMITY_MESSAGES[tier]
            notify(ticket.user_id, ticket.id, f"{icon} {message_text}")
            ticket.notified_tier = tier
    db.session.commit()


def list_notifications_for_user(user_id: int, limit: int = 20):
    notes = (
        Notification.query.filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )
    return [n.to_dict() for n in notes]


def mark_notification_read(notification_id: int, user_id: int):
    note = Notification.query.get(notification_id)
    if not note or note.user_id != user_id:
        return {"error": "Notification not found"}, 404
    note.status = "read"
    db.session.commit()
    return {"message": "Marked as read"}, 200


def mark_all_read(user_id: int):
    Notification.query.filter_by(user_id=user_id, status="unread").update({"status": "read"})
    db.session.commit()
    return {"message": "All notifications marked as read"}, 200
