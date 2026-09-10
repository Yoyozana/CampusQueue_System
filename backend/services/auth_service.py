from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token

from database.connection import db
from database.models import User
from utils.auth import build_student_email, is_valid_student_number


def register_student(full_name: str, student_number: str, password: str):
    full_name = (full_name or "").strip()
    student_number = (student_number or "").strip()
    password = password or ""

    if not full_name or not student_number or not password:
        return {"error": "full_name, student_number and password are required"}, 400
    if not is_valid_student_number(student_number):
        return {"error": "Student number must be 6-10 digits"}, 400
    if len(password) < 8:
        return {"error": "Password must be at least 8 characters"}, 400

    username = student_number
    email = build_student_email(student_number)

    if User.query.filter_by(username=username).first():
        return {"error": "An account with this student number already exists"}, 409

    user = User(
        full_name=full_name, username=username, email=email,
        password_hash=generate_password_hash(password),
        role="student", student_number=student_number,
    )
    db.session.add(user)
    db.session.commit()

    return {"message": "Registration successful", "user": user.to_dict()}, 201


def authenticate(username: str, password: str):
    username = (username or "").strip()
    password = password or ""

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return {"error": "Invalid username or password"}, 401

    claims = {"role": user.role}
    access_token = create_access_token(identity=str(user.id), additional_claims=claims)
    refresh_token = create_refresh_token(identity=str(user.id), additional_claims=claims)

    return {"access_token": access_token, "refresh_token": refresh_token, "user": user.to_dict()}, 200


def issue_refreshed_access_token(user_id: str, role: str):
    return create_access_token(identity=user_id, additional_claims={"role": role})


def get_user_by_id(user_id):
    return User.query.get(user_id)
