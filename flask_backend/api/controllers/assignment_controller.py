from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import (
    Assignment,
    AssignmentSchema,
    Course,
    User,
    User_Course,
)
from ..services import build_assignment_progress_payload, clear_assignment_groups
from .auth_controller import jwt_teacher_required
from .assignment_attachment_controller import (
    list_assignment_attachments,
    save_assignment_attachments,
)
from .helpers import get_teacher_managed_assignment

bp = Blueprint("assignment", __name__, url_prefix="/assignment")
VALID_ASSIGNMENT_MODES = {"solo", "group"}


def _can_access_course(user, course):
    if user.is_admin():
        return True
    if course.teacherID == user.id:
        return True
    return User_Course.get(user.id, course.id) is not None


def _parse_request_data():
    """Support both JSON and multipart/form-data payloads for assignment creation."""
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict()


def _parse_iso_datetime(value, field_name):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(f"Invalid {field_name} format. Use ISO datetime.")


def _parse_assignment_mode(mode):
    if mode is None:
        return None
    if not isinstance(mode, str):
        raise ValueError("assignment_mode must be 'solo' or 'group'")
    normalized = mode.strip().lower()
    if normalized not in VALID_ASSIGNMENT_MODES:
        raise ValueError("assignment_mode must be 'solo' or 'group'")
    return normalized


@bp.route("/create_assignment", methods=["POST"])
@jwt_teacher_required
def create_assignment():
    """Create a new assignment for a class where the authenticated user is the teacher"""
    data = _parse_request_data()
    course_id = data.get("courseID")
    assignment_name = data.get("name")
    rubric_text = data.get("rubric")
    description = data.get("description")
    due_date = data.get("due_date")
    start_date = data.get("start_date")
    assignment_mode = data.get("assignment_mode")

    try:
        due_date = _parse_iso_datetime(due_date, "due_date")
        start_date = _parse_iso_datetime(start_date, "start_date")
        assignment_mode = _parse_assignment_mode(assignment_mode) or "solo"
    except ValueError as exc:
        return jsonify({"msg": str(exc)}), 400

    if not course_id:
        return jsonify({"msg": "Course ID is required"}), 400

    try:
        course_id = int(course_id)
    except (TypeError, ValueError):
        return jsonify({"msg": "Course ID must be an integer"}), 400

    if not assignment_name:
        return jsonify({"msg": "Assignment name is required"}), 400

    if len(assignment_name) > 100:
        return jsonify({"msg": "Assignment name must not exceed 100 characters"}), 400

    if rubric_text and len(rubric_text) > 255:
        return jsonify({"msg": "Rubric must not exceed 255 characters"}), 400

    if description and len(description) > 255:
        return jsonify({"msg": "Description must not exceed 255 characters"}), 400

    # Validate that start_date does not exceed due_date
    if start_date and due_date:
        if start_date > due_date:
            return jsonify({"msg": "Start date cannot be after the due date"}), 400

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    course = Course.get_by_id(course_id)
    if not course:
        return jsonify({"msg": "Class not found"}), 404
    if course.teacherID != user.id:
        return jsonify({"msg": "Unauthorized: You are not the teacher of this class"}), 403
    new_assignment = Assignment(
        courseID=course_id,
        name=assignment_name,
        rubric_text=rubric_text,
        assignment_mode=assignment_mode,
        due_date=due_date,
        start_date=start_date,
        description=description,
    )
    Assignment.create(new_assignment)
    try:
        saved_files = save_assignment_attachments(new_assignment.id)
    except ValueError as exc:
        return jsonify({"msg": str(exc)}), 413

    return (
        jsonify(
            {
                "msg": "Assignment created",
                "assignment": AssignmentSchema().dump(new_assignment),
                "attachments": saved_files,
            }
        ),
        201,
    )

@bp.route("/edit_assignment/<int:assignment_id>", methods=["PATCH"])
@jwt_teacher_required
def edit_assignment(assignment_id):
    """Edit an existing assignment if the authenticated user is the teacher of the class and the due date has not passed"""
    data = request.get_json(silent=True) or {}
    assignment, _, _, error = get_teacher_managed_assignment(assignment_id)
    if error:
        return error

    if not assignment.can_modify():
        return jsonify({"msg": "Assignment cannot be modified after its due date"}), 400

    # Validate name length if provided
    if "name" in data:
        name = data.get("name")
        if name and len(name) > 100:
            return jsonify({"msg": "Assignment name must not exceed 100 characters"}), 400
        assignment.name = name

    # Validate rubric length if provided
    if "rubric" in data:
        rubric = data.get("rubric")
        if rubric and len(rubric) > 255:
            return jsonify({"msg": "Rubric must not exceed 255 characters"}), 400
        assignment.rubric_text = rubric

    # Validate description length if provided
    if "description" in data:
        description = data.get("description")
        if description and len(description) > 255:
            return jsonify({"msg": "Description must not exceed 255 characters"}), 400
        assignment.description = description

    # Handle due_date update - only update if the key is present in request
    if "due_date" in data:
        due_date = data.get("due_date")
        try:
            assignment.due_date = _parse_iso_datetime(due_date, "due_date")
        except ValueError as exc:
            return jsonify({"msg": str(exc)}), 400

    # Handle start_date update - only update if the key is present in request
    if "start_date" in data:
        start_date = data.get("start_date")
        try:
            assignment.start_date = _parse_iso_datetime(start_date, "start_date")
        except ValueError as exc:
            return jsonify({"msg": str(exc)}), 400

    if "assignment_mode" in data:
        if data["assignment_mode"] is None:
            return jsonify({"msg": "assignment_mode cannot be null"}), 400
        try:
            new_mode = _parse_assignment_mode(data["assignment_mode"])
        except ValueError as exc:
            return jsonify({"msg": str(exc)}), 400
        assignment.assignment_mode = new_mode

    # Validate that start_date does not exceed due_date
    if assignment.start_date and assignment.due_date:
        if assignment.start_date > assignment.due_date:
            return jsonify({"msg": "Start date cannot be after the due date"}), 400

    if assignment.assignment_mode == "solo":
        clear_assignment_groups(assignment.id)

    assignment.update()
    return (
        jsonify(
            {
                "msg": "Assignment updated",
                "assignment": AssignmentSchema().dump(assignment),
            }
        ),
        200,
    )


@bp.route("/delete_assignment/<int:assignment_id>", methods=["DELETE"])
@jwt_teacher_required
def delete_assignment(assignment_id):
    """Delete an existing assignment if the authenticated user is the teacher of the class and the due date has not passed"""
    assignment, _, _, error = get_teacher_managed_assignment(assignment_id)
    if error:
        return error

    if not assignment.can_modify():
        return jsonify({"msg": "Assignment cannot be deleted after its due date"}), 400

    assignment.delete()
    return jsonify({"msg": "Assignment deleted"}), 200


@bp.route("/<int:class_id>", methods=["GET"])
@jwt_required()
def get_assignments(class_id):
    """Get all assignments for a given class"""
    course = Course.get_by_id(class_id)
    if not course:
        return jsonify({"msg": "Class not found"}), 404

    email = get_jwt_identity()
    current_user = User.get_by_email(email)
    if not current_user:
        return jsonify({"msg": "User not found"}), 404
    if not _can_access_course(current_user, course):
        return jsonify({"msg": "Insufficient permissions"}), 403

    assignments = Assignment.get_by_class_id(class_id)
    assignments_data = AssignmentSchema(many=True).dump(assignments)
    for assignment_data in assignments_data:
        assignment_data["attachments"] = list_assignment_attachments(assignment_data["id"])

    return jsonify(assignments_data), 200


@bp.route("/<int:assignment_id>/progress", methods=["GET"])
@jwt_teacher_required
def get_assignment_progress(assignment_id):
    """Get per-student submission/review completion status for one assignment."""
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    course = Course.get_by_id(assignment.courseID)
    if not course:
        return jsonify({"msg": "Class not found"}), 404

    email = get_jwt_identity()
    current_user = User.get_by_email(email)
    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    if course.teacherID != current_user.id and not current_user.is_admin():
        return jsonify({"msg": "Insufficient permissions"}), 403

    payload = build_assignment_progress_payload(assignment)
    return jsonify(payload), 200


@bp.route("/<int:assignment_id>/mode", methods=["PATCH"])
@jwt_teacher_required
def update_assignment_mode(assignment_id):
    """Update assignment collaboration mode (solo/group)."""
    data = request.get_json(silent=True) or {}
    assignment, _, _, error = get_teacher_managed_assignment(assignment_id)
    if error:
        return error

    try:
        mode = _parse_assignment_mode(data.get("assignment_mode"))
    except ValueError as exc:
        return jsonify({"msg": str(exc)}), 400

    if mode is None:
        return jsonify({"msg": "assignment_mode is required"}), 400

    assignment.assignment_mode = mode
    if mode == "solo":
        clear_assignment_groups(assignment.id)

    assignment.update()
    return jsonify({"msg": "Assignment mode updated", "assignment": AssignmentSchema().dump(assignment)}), 200
