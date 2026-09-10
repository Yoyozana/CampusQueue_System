import re
from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import get_jwt, verify_jwt_in_request

STUDENT_NUMBER_PATTERN = re.compile(r"^\d{6,10}$")


def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in allowed_roles:
                return jsonify({"error": "Forbidden: insufficient role"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def build_student_email(student_number: str) -> str:
    domain = current_app.config.get("STUDENT_EMAIL_DOMAIN", "mywsu.ac.za")
    return f"{student_number}@{domain}"


def is_valid_student_number(student_number: str) -> bool:
    return bool(STUDENT_NUMBER_PATTERN.match(student_number or ""))
