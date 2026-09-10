from flask import Flask
from config import Config
from database.connection import db
from database.models import Service, Queue, ServicePoint, Ticket, User, Notification
from services import admin_service, queue_service

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

app = Flask(__name__)
app.config.from_object(TestConfig)
db.init_app(app)

with app.app_context():
    db.create_all()

    service = Service(service_name="Registration", location="Main Admin Building")
    db.session.add(service); db.session.commit()
    queue = Queue(service_id=service.id, queue_name="Registration Queue", prefix="REG", status="open")
    db.session.add(queue); db.session.commit()
    sp = ServicePoint(point_name="Counter 1", queue_id=queue.id, is_active=True)
    db.session.add(sp); db.session.commit()

    admin1 = User(full_name="Admin One", username="admin1", email="admin1@iws.ac.za", password_hash="x", role="admin")
    admin2 = User(full_name="Admin Two", username="admin2", email="admin2@iws.ac.za", password_hash="x", role="admin")
    student1 = User(full_name="Student One", username="260000001", student_number="260000001",
                     email="260000001@mywsu.ac.za", password_hash="x", role="student")
    student2 = User(full_name="Student Two", username="260000002", student_number="260000002",
                     email="260000002@mywsu.ac.za", password_hash="x", role="student")
    db.session.add_all([admin1, admin2, student1, student2]); db.session.commit()

    # Admin1 claims the queue; Admin2 should be blocked
    result, status = admin_service.select_todays_queue(admin1.id, queue.id)
    assert status == 200
    print("PASS: admin1 selects Registration queue")

    result, status = admin_service.select_todays_queue(admin2.id, queue.id)
    assert status == 409
    print("PASS: admin2 blocked from claiming an already-claimed queue")

    # A student joins; Admin2 (not managing this queue) tries to call next -> blocked
    queue_service.join_queue(queue.id, student1.id)
    result, status = admin_service.call_next(admin2.id, queue.id)
    assert status == 403
    print("PASS: admin2 blocked from calling next on a queue they don't manage")

    # Admin1 (the real manager) calls next -> succeeds
    result, status = admin_service.call_next(admin1.id, queue.id)
    assert status == 200 and result["ticket"]["ticket_number"] == "REG-1"
    ticket1_id = result["ticket"]["id"]
    print("PASS: admin1 calls next -> REG-1")

    notif = Notification.query.filter_by(user_id=student1.id, ticket_id=ticket1_id).first()
    assert notif and "called" in notif.message
    print("PASS: student notified when called ->", notif.message)

    # Calling next with nobody left waiting -> clean message, not an error
    result, status = admin_service.call_next(admin1.id, queue.id)
    assert status == 200 and "No students waiting" in result["message"]
    print("PASS: empty queue -> clean message, not an error")

    # Second student joins; can't be served while still waiting
    queue_service.join_queue(queue.id, student2.id)
    ticket2 = Ticket.query.filter_by(ticket_number="REG-2").first()
    result, status = admin_service.mark_served(admin1.id, ticket2.id)
    assert status == 409
    print("PASS: cannot serve a still-waiting ticket")

    # Serve the actually-called ticket (REG-1)
    result, status = admin_service.mark_served(admin1.id, ticket1_id)
    assert status == 200 and result["ticket"]["status"] == "served"
    print("PASS: REG-1 served")

    sp_refreshed = db.session.get(ServicePoint, sp.id)
    assert sp_refreshed.current_ticket_id is None
    print("PASS: service point cleared after serving")

    # Call and skip REG-2
    result, status = admin_service.call_next(admin1.id, queue.id)
    ticket2_id = result["ticket"]["id"]
    result, status = admin_service.skip_ticket(admin1.id, ticket2_id)
    assert status == 200 and result["ticket"]["status"] == "skipped"
    print("PASS: REG-2 skipped (no-show)")

    all_notifs = Notification.query.filter_by(ticket_id=ticket2_id).order_by(Notification.id).all()
    assert len(all_notifs) == 2 and "missed your turn" in all_notifs[-1].message
    print("PASS: skip notification correctly created ->", all_notifs[-1].message)

    # Closing a queue auto-cancels anyone still waiting
    result3, _ = queue_service.join_queue(queue.id, student1.id)
    ticket3_id = result3["ticket"]["id"]
    result, status = admin_service.set_queue_status(admin1.id, queue.id, "closed")
    assert status == 200
    ticket3 = db.session.get(Ticket, ticket3_id)
    assert ticket3.status == "cancelled"
    print("PASS: closing the queue auto-cancels the still-waiting ticket")

    notif3 = Notification.query.filter_by(ticket_id=ticket3_id).order_by(Notification.id.desc()).first()
    assert "closed" in notif3.message
    print("PASS: student notified of cancellation due to closure ->", notif3.message)

    # Can't call next on a closed queue
    admin_service.set_queue_status(admin1.id, queue.id, "open")
    admin_service.set_queue_status(admin1.id, queue.id, "closed")
    result, status = admin_service.call_next(admin1.id, queue.id)
    assert status == 409
    print("PASS: cannot call next on a closed queue")

    # Invalid status value rejected
    admin_service.set_queue_status(admin1.id, queue.id, "open")
    result, status = admin_service.set_queue_status(admin1.id, queue.id, "bogus")
    assert status == 400
    print("PASS: invalid status value rejected")

    # Switching to a different queue releases the old one
    service2 = Service(service_name="Financial Aid", location="Student Centre")
    db.session.add(service2); db.session.commit()
    queue2 = Queue(service_id=service2.id, queue_name="Financial Aid Queue", prefix="FIN", status="open")
    db.session.add(queue2); db.session.commit()

    admin_service.select_todays_queue(admin1.id, queue2.id)
    queue_refreshed = db.session.get(Queue, queue.id)
    queue2_refreshed = db.session.get(Queue, queue2.id)
    assert queue_refreshed.current_admin_id is None and queue2_refreshed.current_admin_id == admin1.id
    print("PASS: switching queues releases the old one automatically")

    # Audit log actually recorded everything
    actions = admin_service.list_admin_actions(limit=100)
    assert len(actions) > 5
    assert any("Called REG-1" in a["action_description"] for a in actions)
    print(f"PASS: audit log has {len(actions)} correctly recorded entries")

    result, status = admin_service.get_queue_activity(queue.id)
    assert status == 200
    print("PASS: get_queue_activity returns correctly")

print()
print("ALL TESTS PASSED")
