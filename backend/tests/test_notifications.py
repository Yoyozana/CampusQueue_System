import json
from app import create_app
from config import Config
from database.connection import db
from database.models import Service, Queue, ServicePoint, User
from werkzeug.security import generate_password_hash

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

app = create_app(TestConfig)

with app.app_context():
    db.create_all()
    service = Service(service_name="Registration", location="Main Admin Building")
    db.session.add(service); db.session.commit()
    queue = Queue(service_id=service.id, queue_name="Registration Queue", prefix="REG", status="open")
    db.session.add(queue); db.session.commit()
    queue_id = queue.id
    sp = ServicePoint(point_name="Counter 1", queue_id=queue.id, is_active=True)
    db.session.add(sp); db.session.commit()
    admin = User(full_name="Admin", username="admin", email="admin@iws.ac.za",
                 password_hash=generate_password_hash("AdminPass123"), role="admin")
    db.session.add(admin); db.session.commit()

client = app.test_client()

def post_json(url, data=None, headers=None):
    return client.post(url, data=json.dumps(data or {}), content_type="application/json", headers=headers or {})

def register_and_login(num):
    post_json("/api/auth/register", {"full_name": f"Student {num}", "student_number": f"26000000{num}", "password": "password123"})
    resp = post_json("/api/auth/login", {"username": f"26000000{num}", "password": "password123"})
    return resp.get_json()["access_token"]

# Three students join in order - REG-1 (position 1), REG-2 (position 2), REG-3 (position 3)
tokens = [register_and_login(i) for i in range(1, 4)]
headers = [{"Authorization": f"Bearer {t}"} for t in tokens]

resp = post_json("/api/auth/login", {"username": "admin", "password": "AdminPass123"})
admin_headers = {"Authorization": f"Bearer {resp.get_json()['access_token']}"}
post_json(f"/api/admin/queues/{queue_id}/select", headers=admin_headers)

for i in range(3):
    resp = post_json(f"/api/queues/{queue_id}/join", headers=headers[i])
    assert resp.status_code == 201, resp.get_json()
    print(f"Student {i+1} joined ->", resp.get_json()["ticket"]["ticket_number"], "position", resp.get_json()["ticket"]["position"])

# Check each student's notifications immediately after joining
for i in range(3):
    resp = client.get("/api/notifications", headers=headers[i])
    notes = resp.get_json()["notifications"]
    print(f"Student {i+1} notifications:", [n["message"] for n in notes])

# Admin calls next -> everyone shifts up
resp = post_json(f"/api/admin/queues/{queue_id}/call-next", headers=admin_headers)
print("\nAdmin called:", resp.get_json()["ticket"]["ticket_number"])

# Student 2 should now have a NEW tier-1 notification (they were tier-2 before)
resp = client.get("/api/notifications", headers=headers[1])
notes = resp.get_json()["notifications"]
print("Student 2 notifications after call-next:", [n["message"] for n in notes])

# Mark one read
note_id = notes[0]["id"]
resp = post_json(f"/api/notifications/{note_id}/read", headers=headers[1])
print("\nMark read status:", resp.status_code, resp.get_json())

resp = client.get("/api/notifications", headers=headers[1])
print("After marking read:", resp.get_json()["notifications"])
