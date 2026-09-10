from datetime import datetime
from database.connection import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column("user_id", db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    student_number = db.Column(db.String(20), unique=True, nullable=True)  # NULL for admin/staff
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("student", "admin", name="user_role"), nullable=False, default="student")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tickets = db.relationship("Ticket", back_populates="user", lazy="dynamic")
    notifications = db.relationship("Notification", back_populates="user", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "student_number": self.student_number,
        }


class Service(db.Model):
    """
    A campus department/service, e.g. "Financial Aid". One service can
    have multiple queues under it (see Queue.service_id below).
    """
    __tablename__ = "services"

    id = db.Column("service_id", db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(150), nullable=True)

    queues = db.relationship("Queue", back_populates="service", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "service_name": self.service_name,
            "description": self.description,
            "location": self.location,
        }


class Queue(db.Model):
    __tablename__ = "queues"

    id = db.Column("queue_id", db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey("services.service_id", ondelete="RESTRICT"), nullable=False)
    queue_name = db.Column(db.String(100), nullable=False)          # e.g. "Financial Aid Queue"
    prefix = db.Column(db.String(5), nullable=False, unique=True)   # e.g. "FIN"
    status = db.Column(db.Enum("open", "paused", "closed", name="queue_status"),
                        nullable=False, default="open")
    current_admin_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )  # who is managing THIS queue this session — set at login when an admin
       # picks "today's service/queue", cleared on logout/"Switch Queue".
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    service = db.relationship("Service", back_populates="queues")
    current_admin = db.relationship("User", foreign_keys=[current_admin_id])
    tickets = db.relationship("Ticket", back_populates="queue", lazy="dynamic")
    service_points = db.relationship("ServicePoint", back_populates="queue", lazy="dynamic")
    counter = db.relationship("QueueCounter", back_populates="queue", uselist=False)

    def to_dict(self, include_counts=False):
        data = {
            "id": self.id,
            "service_id": self.service_id,
            "queue_name": self.queue_name,
            "prefix": self.prefix,
            "status": self.status,
            "current_admin_id": self.current_admin_id,
        }
        if include_counts:
            data["waiting_count"] = self.tickets.filter_by(status="waiting").count()
        return data


class QueueCounter(db.Model):
    """
    One row per queue. last_number is incremented atomically (row-locked)
    each time a ticket is issued, preventing duplicate ticket numbers when
    multiple students join the same queue concurrently.
    """
    __tablename__ = "queue_counters"

    queue_id = db.Column(db.Integer, db.ForeignKey("queues.queue_id", ondelete="CASCADE"), primary_key=True)
    last_number = db.Column(db.Integer, nullable=False, default=0)

    queue = db.relationship("Queue", back_populates="counter")


class Ticket(db.Model):
    __tablename__ = "queue_tickets"

    id = db.Column("ticket_id", db.Integer, primary_key=True)
    queue_id = db.Column(db.Integer, db.ForeignKey("queues.queue_id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    sequence_number = db.Column(db.Integer, nullable=False)     # raw number, e.g. 102
    ticket_number = db.Column(db.String(20), nullable=False)    # formatted, e.g. "FIN-102"
    status = db.Column(
        db.Enum("waiting", "called", "served", "skipped", "cancelled", name="ticket_status"),
        nullable=False, default="waiting"
    )
    notified_tier = db.Column(db.SmallInteger, nullable=False, default=0)
        # Which proximity tier (1, 2, or 3) this ticket has already been
        # notified for — persisted so the tiered "you're almost next"
        # notification fires exactly once per tier.
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    called_at = db.Column(db.DateTime, nullable=True)
    served_at = db.Column(db.DateTime, nullable=True)  # also "resolved at" when status = 'skipped'

    queue = db.relationship("Queue", back_populates="tickets")
    user = db.relationship("User", back_populates="tickets")

    __table_args__ = (
        db.UniqueConstraint("queue_id", "sequence_number", name="uq_queue_sequence"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "queue_id": self.queue_id,
            "ticket_number": self.ticket_number,
            "status": self.status,
            "notified_tier": self.notified_tier,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "called_at": self.called_at.isoformat() if self.called_at else None,
            "served_at": self.served_at.isoformat() if self.served_at else None,
        }


class ServicePoint(db.Model):
    """
    A physical counter/desk. Fixed to a single queue permanently.
    No admin_id column — which admin is working a queue is tracked on
    Queue.current_admin_id instead, since the desk itself never changes.
    """
    __tablename__ = "service_points"

    id = db.Column("service_point_id", db.Integer, primary_key=True)
    point_name = db.Column(db.String(100), nullable=False)  # e.g. "Counter 1"
    queue_id = db.Column(db.Integer, db.ForeignKey("queues.queue_id", ondelete="SET NULL"), nullable=True)
    current_ticket_id = db.Column(
        db.Integer, db.ForeignKey("queue_tickets.ticket_id", ondelete="SET NULL"), nullable=True
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    queue = db.relationship("Queue", back_populates="service_points")
    current_ticket = db.relationship("Ticket", foreign_keys=[current_ticket_id])

    def to_dict(self):
        return {
            "id": self.id,
            "point_name": self.point_name,
            "queue_id": self.queue_id,
            "is_active": self.is_active,
            "current_ticket": self.current_ticket.ticket_number if self.current_ticket else None,
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column("notification_id", db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    ticket_id = db.Column(
        db.Integer, db.ForeignKey("queue_tickets.ticket_id", ondelete="SET NULL"), nullable=True
    )
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum("unread", "read", name="notification_status"), default="unread")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="notifications")
    ticket = db.relationship("Ticket")

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read": self.status == "read",
        }


class AdminAction(db.Model):
    """
    Audit log. Every queue selection, call-next, serve, skip, pause, or
    close inserts a row here.
    """
    __tablename__ = "admin_actions"

    id = db.Column("action_id", db.Integer, primary_key=True)
    admin_id = db.Column(
        db.Integer, db.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )  # nullable so the audit trail survives admin account deletion
    action_description = db.Column(db.Text, nullable=False)
    action_time = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "admin_id": self.admin_id,
            "action_description": self.action_description,
            "action_time": self.action_time.isoformat() if self.action_time else None,
        }
