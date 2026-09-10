import json
from flask import Flask
from flask_jwt_extended import JWTManager
from config import Config
from database.connection import db
from routes.auth_routes import bp as auth_bp

app = Flask(__name__)
app.config.from_object(Config)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
db.init_app(app)
jwt = JWTManager(app)
app.register_blueprint(auth_bp)

with app.app_context():
    db.create_all()

client = app.test_client()

def post_json(url, data):
    return client.post(url, data=json.dumps(data), content_type="application/json")

resp = post_json("/api/auth/register", {"full_name": "Test Student", "student_number": "260000001", "password": "password123"})
assert resp.status_code == 201
print("PASS: register ->", resp.get_json())

resp = post_json("/api/auth/login", {"username": "260000001", "password": "password123"})
assert resp.status_code == 200
access_token = resp.get_json()["access_token"]
print("PASS: login -> token issued")

resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
assert resp.status_code == 200
print("PASS: /me ->", resp.get_json())

print("ALL TESTS PASSED")
