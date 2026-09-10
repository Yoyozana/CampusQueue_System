from flask import Flask
from flask_jwt_extended import JWTManager, decode_token
from config import Config
from database.connection import db
from database.models import User
from services import auth_service

app = Flask(__name__)
app.config.from_object(Config)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
db.init_app(app)
jwt = JWTManager(app)

with app.app_context():
    db.create_all()

    result, status = auth_service.register_student("Siya Mbulelo", "260000001", "password123")
    assert status == 201
    print("PASS: registration ->", result["user"])

    result, status = auth_service.register_student("Dup", "260000001", "password123")
    assert status == 409
    print("PASS: duplicate rejected")

    result, status = auth_service.authenticate("260000001", "password123")
    assert status == 200
    decoded = decode_token(result["access_token"])
    assert decoded["role"] == "student"
    print("PASS: login works, JWT role =", decoded["role"])

    result, status = auth_service.authenticate("260000001", "wrongpassword")
    assert status == 401
    print("PASS: wrong password rejected")

print("ALL TESTS PASSED")
