from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Course, Assignment, User, AssignmentSchema
from .auth_controller import jwt_teacher_required
from .assignment_attachment_controller import (
    list_assignment_attachments,
    save_assignment_attachments,
)

bp = Blueprint("assignment", __name__, url_prefix="/assignment")


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

# Assignment attachment handling function - saving, listing, and downloading attachments.
#not too much changed here except for the addition of start_date when creating and editing an assignment
@bp.route("/create_assignment", methods=["POST"])
@jwt_teacher_required
def create_assignment():
    """Create a new assignment for a class where the authenticated user is the teacher"""
    data = _parse_request_data()
    course_id = data.get("courseID")
    assignment_name = data.get("name")
    rubric_text = data.get("rubric")
    due_date = data.get("due_date")
    start_date = data.get("start_date")

    try:
        due_date = _parse_iso_datetime(due_date, "due_date")
        start_date = _parse_iso_datetime(start_date, "start_date")
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
#edited line below to include start_date when creating a new assignment
    new_assignment = Assignment(courseID=course_id, name=assignment_name, rubric_text=rubric_text, due_date=due_date, start_date=start_date)
    Assignment.create(new_assignment)
    saved_files = save_assignment_attachments(new_assignment.id)

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
    data = request.get_json()
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    course = Course.get_by_id(assignment.courseID)
    if course is None:
        return jsonify({"msg": "Course not found"}), 404
    
    if course.teacherID != user.id:
        return jsonify({"msg": "Unauthorized: You are not the teacher of this class"}), 403

    if not assignment.can_modify():
        return jsonify({"msg": "Assignment cannot be modified after its due date"}), 400

    assignment.name = data.get("name", assignment.name)
    assignment.rubric_text = data.get("rubric", assignment.rubric_text)
    
    # Handle due_date update - only update if the key is present in request
    if "due_date" in data:
        due_date = data.get("due_date")
        if due_date:
            assignment.due_date = datetime.fromisoformat(due_date)
        else:
            assignment.due_date = None
    
    # Handle start_date update - only update if the key is present in request
    if "start_date" in data:
        start_date = data.get("start_date")
        if start_date:
            assignment.start_date = datetime.fromisoformat(start_date)
        else:
            assignment.start_date = None
    
    # Validate that start_date does not exceed due_date
    if assignment.start_date and assignment.due_date:
        if assignment.start_date > assignment.due_date:
            return jsonify({"msg": "Start date cannot be after the due date"}), 400

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
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    course = Course.get_by_id(assignment.courseID)
    if not course:
        return jsonify({"msg": "Course not found"}), 404
    
    if course.teacherID != user.id:
        return jsonify({"msg": "Unauthorized: You are not the teacher of this class"}), 403

    if not assignment.can_modify():
        return jsonify({"msg": "Assignment cannot be deleted after its due date"}), 400

    assignment.delete()
    return jsonify({"msg": "Assignment deleted"}), 200
    

# the following routes are for getting the assignments for a given course
@bp.route("/<int:class_id>", methods=["GET"])
@jwt_required()
def get_assignments(class_id):
    """Get all assignments for a given class"""
    course = Course.get_by_id(class_id)
    if not course:
        return jsonify({"msg": "Class not found"}), 404

    assignments = Assignment.get_by_class_id(class_id)
    assignments_data = AssignmentSchema(many=True).dump(assignments)
    for assignment_data in assignments_data:
        assignment_data["attachments"] = list_assignment_attachments(assignment_data["id"])

    return jsonify(assignments_data), 200
