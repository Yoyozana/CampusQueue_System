from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from services import auth_service
from utils.rate_limit import limit_by_ip

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.route("/register", methods=["POST"])
@limit_by_ip("register", max_requests=10, per_seconds=3600)
def register():
    data = request.get_json(silent=True) or {}
    result, status = auth_service.register_student(
        data.get("full_name"), data.get("student_number"), data.get("password")
    )
    return jsonify(result), status


@bp.route("/login", methods=["POST"])
@limit_by_ip("login", max_requests=20, per_seconds=60)
def login():
    data = request.get_json(silent=True) or {}
    result, status = auth_service.authenticate(data.get("username"), data.get("password"))
    return jsonify(result), status


@bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims = get_jwt()
    new_access_token = auth_service.issue_refreshed_access_token(identity, claims.get("role"))
    return jsonify({"access_token": new_access_token}), 200


@bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = auth_service.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200
