from datetime import datetime, timedelta

from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token

from database.connection import db
from database.models import User
from utils.auth import (build_student_email, is_valid_student_number,
                        is_valid_username, is_valid_full_name)


def register_student(full_name: str, student_number: str, password: str):
    full_name = (full_name or "").strip()
    student_number = (student_number or "").strip()
    password = password or ""

    if not full_name or not student_number or not password:
        return {"error": "full_name, student_number and password are required"}, 400
    if not is_valid_full_name(full_name):
        return {"error": "Full name may only contain letters, spaces, hyphens and apostrophes"}, 400
    if not is_valid_student_number(student_number):
        return {"error": "Student number must be 6-10 digits"}, 400
    if len(password) < 8 or len(password) > 128:
        return {"error": "Password must be 8-128 characters"}, 400

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

    # Reject junk before touching the database. (All queries go through
    # SQLAlchemy with bound parameters, so input is never pasted into SQL.)
    if not is_valid_username(username) or not password:
        return {"error": "Invalid username or password"}, 401

    max_attempts = current_app.config.get("MAX_FAILED_LOGINS", 5)
    lock_minutes = current_app.config.get("LOCKOUT_MINUTES", 15)
    now = datetime.utcnow()

    user = User.query.filter_by(username=username).first()
    if not user:
        # Same message as a wrong password, so attackers can't find valid usernames.
        return {"error": "Invalid username or password"}, 401

    if user.locked_until and user.locked_until > now:
        minutes = max(1, int((user.locked_until - now).total_seconds() // 60) + 1)
        return {"error": f"Your account is locked after too many failed sign-ins. ",
                "locked_until": user.locked_until.isoformat() + "Z"}, 423

    if user.locked_until and user.locked_until <= now:
        # Lock has run out: start counting afresh.
        user.locked_until = None
        user.failed_login_attempts = 0

    if not check_password_hash(user.password_hash, password):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= max_attempts:
            user.locked_until = now + timedelta(minutes=lock_minutes)
            db.session.commit()
            return {"error": f"Too many failed sign-ins. Your account is locked for {lock_minutes} minutes.",
                    "locked_until": user.locked_until.isoformat() + "Z"}, 423
        db.session.commit()
        return {"error": "Invalid username or password",
                "attempts_left": max_attempts - user.failed_login_attempts}, 401

    user.failed_login_attempts = 0
    user.locked_until = None
    db.session.commit()

    claims = {"role": user.role}
    access_token = create_access_token(identity=str(user.id), additional_claims=claims)
    refresh_token = create_refresh_token(identity=str(user.id), additional_claims=claims)

    return {"access_token": access_token, "refresh_token": refresh_token, "user": user.to_dict()}, 200


def issue_refreshed_access_token(user_id: str, role: str):
    return create_access_token(identity=user_id, additional_claims={"role": role})


def get_user_by_id(user_id):
    return User.query.get(user_id)
