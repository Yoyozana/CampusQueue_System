from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from services import admin_service
from utils.auth import role_required

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.route("/queues", methods=["GET"])
@role_required("admin")
def list_queues_for_selection():
    return jsonify({"queues": admin_service.list_queues_for_selection()}), 200


@bp.route("/service-points", methods=["GET"])
@role_required("admin")
def list_service_points():
    return jsonify({"service_points": admin_service.list_service_points()}), 200


@bp.route("/tickets", methods=["GET"])
@role_required("admin")
def list_all_tickets():
    return jsonify({"tickets": admin_service.list_all_tickets()}), 200


@bp.route("/users", methods=["GET"])
@role_required("admin")
def list_all_users():
    return jsonify({"users": admin_service.list_all_users()}), 200


@bp.route("/my-queue", methods=["GET"])
@role_required("admin")
def my_current_queue():
    """
    Which queue (if any) this admin is already managing this session.
    The frontend calls this right after login/on page load, so it can
    skip straight to the dashboard instead of forcing the admin through
    "Which service are you managing today?" every single time - only
    showing that screen when this returns null.
    """
    admin_id = int(get_jwt_identity())
    queue = admin_service.get_admin_current_queue(admin_id)
    return jsonify({"queue": queue.to_dict() if queue else None}), 200


@bp.route("/queues/<int:queue_id>/select", methods=["POST"])
@role_required("admin")
def select_todays_queue(queue_id):
    admin_id = int(get_jwt_identity())
    result, status = admin_service.select_todays_queue(admin_id, queue_id)
    return jsonify(result), status


@bp.route("/release", methods=["POST"])
@role_required("admin")
def release_todays_queue():
    admin_id = int(get_jwt_identity())
    result, status = admin_service.release_todays_queue(admin_id)
    return jsonify(result), status


@bp.route("/queues/<int:queue_id>/activity", methods=["GET"])
@role_required("admin")
def queue_activity(queue_id):
    result, status = admin_service.get_queue_activity(queue_id)
    return jsonify(result), status


@bp.route("/queues/<int:queue_id>/status", methods=["PATCH"])
@role_required("admin")
def set_queue_status(queue_id):
    admin_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    result, status = admin_service.set_queue_status(admin_id, queue_id, data.get("status"))
    return jsonify(result), status


@bp.route("/queues/<int:queue_id>/call-next", methods=["POST"])
@role_required("admin")
def call_next(queue_id):
    admin_id = int(get_jwt_identity())
    result, status = admin_service.call_next(admin_id, queue_id)
    return jsonify(result), status


@bp.route("/tickets/<int:ticket_id>/serve", methods=["POST"])
@role_required("admin")
def mark_served(ticket_id):
    admin_id = int(get_jwt_identity())
    result, status = admin_service.mark_served(admin_id, ticket_id)
    return jsonify(result), status


@bp.route("/tickets/<int:ticket_id>/skip", methods=["POST"])
@role_required("admin")
def skip_ticket(ticket_id):
    admin_id = int(get_jwt_identity())
    result, status = admin_service.skip_ticket(admin_id, ticket_id)
    return jsonify(result), status


@bp.route("/actions", methods=["GET"])
@role_required("admin")
def list_admin_actions():
    return jsonify({"actions": admin_service.list_admin_actions()}), 200