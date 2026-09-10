from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from services import queue_service

bp = Blueprint("queues", __name__, url_prefix="/api/queues")


@bp.route("", methods=["GET"])
@jwt_required()
def list_queues():
    """All queues, with a live waiting_count - visible to any logged-in user."""
    return jsonify({"queues": queue_service.list_queues()}), 200


@bp.route("/<int:queue_id>/join", methods=["POST"])
@jwt_required()
def join(queue_id):
    user_id = int(get_jwt_identity())
    result, status = queue_service.join_queue(queue_id, user_id)
    return jsonify(result), status


@bp.route("/tickets/<int:ticket_id>", methods=["GET"])
@jwt_required()
def ticket_status(ticket_id):
    user_id = int(get_jwt_identity())
    result, status = queue_service.get_ticket_status(ticket_id, user_id)
    return jsonify(result), status


@bp.route("/tickets/<int:ticket_id>/cancel", methods=["POST"])
@jwt_required()
def cancel(ticket_id):
    user_id = int(get_jwt_identity())
    result, status = queue_service.cancel_ticket(ticket_id, user_id)
    return jsonify(result), status


@bp.route("/my-active-tickets", methods=["GET"])
@jwt_required()
def my_active_tickets():
    user_id = int(get_jwt_identity())
    tickets = queue_service.list_active_tickets_for_user(user_id)
    return jsonify({"tickets": tickets}), 200