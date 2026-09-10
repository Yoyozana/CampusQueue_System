from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from services import notification_service

bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@bp.route("", methods=["GET"])
@jwt_required()
def list_notifications():
    user_id = int(get_jwt_identity())
    notes = notification_service.list_notifications_for_user(user_id)
    return jsonify({"notifications": notes}), 200


@bp.route("/<int:notification_id>/read", methods=["POST"])
@jwt_required()
def mark_read(notification_id):
    user_id = int(get_jwt_identity())
    result, status = notification_service.mark_notification_read(notification_id, user_id)
    return jsonify(result), status


@bp.route("/read-all", methods=["POST"])
@jwt_required()
def mark_all_read():
    user_id = int(get_jwt_identity())
    result, status = notification_service.mark_all_read(user_id)
    return jsonify(result), status
