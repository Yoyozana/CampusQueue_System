from flask import Flask
from database.connection import db
from database.models import User, Service, Queue, QueueCounter, Ticket, ServicePoint, Notification, AdminAction

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test_models_check.db"
db.init_app(app)

with app.app_context():
    queue_cols = [c.name for c in Queue.__table__.columns]
    sp_cols = [c.name for c in ServicePoint.__table__.columns]
    ticket_cols = [c.name for c in Ticket.__table__.columns]

    assert "current_admin_id" in queue_cols
    assert "admin_id" not in sp_cols
    assert "notified_tier" in ticket_cols
    print("PASS: the three critical model fixes are all present")

    db.create_all()
    print("PASS: all tables created successfully with no errors")

    # Quick round-trip test with real data
    service = Service(service_name="Registration", location="Main Admin Building")
    db.session.add(service)
    db.session.commit()

    queue = Queue(service_id=service.id, queue_name="Registration Queue", prefix="REG", status="open")
    db.session.add(queue)
    db.session.commit()

    print("PASS: created a Service and a Queue successfully ->", queue.to_dict())

print("ALL TESTS PASSED")
