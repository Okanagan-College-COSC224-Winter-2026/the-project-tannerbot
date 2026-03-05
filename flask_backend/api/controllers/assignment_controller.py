import os
import tempfile
import uuid
from datetime import datetime
from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from ..models import Course, Assignment, User, User_Course, AssignmentSchema
from .auth_controller import jwt_teacher_required

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


def _save_assignment_attachments(assignment_id):
    uploaded_files = []
    for key in ("attachments", "attachment", "files", "file"):
        uploaded_files.extend(request.files.getlist(key))

    # Fallback: accept files from any field name to be resilient to client variations.
    if not uploaded_files:
        for key in request.files.keys():
            uploaded_files.extend(request.files.getlist(key))

    if not uploaded_files:
        return []

    upload_root = _get_writable_upload_root()

    if not upload_root:
        raise OSError("No writable upload directory available")

    assignment_dir = os.path.join(upload_root, str(assignment_id))
    os.makedirs(assignment_dir, exist_ok=True)

    saved_files = []
    for uploaded_file in uploaded_files:
        if not uploaded_file or not uploaded_file.filename:
            continue

        safe_name = secure_filename(uploaded_file.filename)
        if not safe_name:
            continue

        # Prefix with UUID to avoid filename collisions for repeated uploads.
        stored_name = f"{uuid.uuid4().hex}_{safe_name}"
        file_path = os.path.join(assignment_dir, stored_name)
        uploaded_file.save(file_path)
        saved_files.append(
            {
                "original_name": uploaded_file.filename,
                "stored_name": stored_name,
            }
        )

    return saved_files


def _get_upload_roots():
    configured_upload_root = current_app.config.get(
        "ASSIGNMENT_UPLOAD_FOLDER",
        os.path.join(current_app.instance_path, "assignment_uploads"),
    )
    fallback_upload_root = os.path.join(
        tempfile.gettempdir(),
        "peer_eval_assignment_uploads",
    )
    return [configured_upload_root, fallback_upload_root]


def _get_writable_upload_root():
    for candidate in _get_upload_roots():
        try:
            os.makedirs(candidate, exist_ok=True)
            return candidate
        except OSError:
            continue
    return None


def _get_assignment_upload_dir(assignment_id):
    """Return a single canonical attachment directory for this assignment."""
    for upload_root in _get_upload_roots():
        assignment_dir = os.path.join(upload_root, str(assignment_id))
        if os.path.isdir(assignment_dir):
            return assignment_dir
    return None


def _list_assignment_attachments(assignment_id):
    attachments = []
    assignment_dir = _get_assignment_upload_dir(assignment_id)
    if not assignment_dir:
        return attachments

    for stored_name in os.listdir(assignment_dir):
        file_path = os.path.join(assignment_dir, stored_name)
        if not os.path.isfile(file_path):
            continue

        original_name = stored_name.split("_", 1)[1] if "_" in stored_name else stored_name
        attachments.append(
            {
                "stored_name": stored_name,
                "original_name": original_name,
                "download_url": f"/assignment/{assignment_id}/attachment/{stored_name}",
            }
        )

    return attachments


def _can_access_course(user, course):
    if user.is_admin():
        return True
    if course.teacherID == user.id:
        return True
    return User_Course.get(user.id, course.id) is not None


def _resolve_attachment_path(assignment_id, stored_name):
    if os.path.basename(stored_name) != stored_name:
        return None, None

    assignment_dir = _get_assignment_upload_dir(assignment_id)
    if assignment_dir:
        file_path = os.path.join(assignment_dir, stored_name)
        if os.path.isfile(file_path):
            return assignment_dir, file_path

    return None, None


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
    saved_files = _save_assignment_attachments(new_assignment.id)

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
        assignment_data["attachments"] = _list_assignment_attachments(assignment_data["id"])

    return jsonify(assignments_data), 200


@bp.route("/<int:assignment_id>/attachment/<path:stored_name>", methods=["GET"])
@jwt_required()
def download_assignment_attachment(assignment_id, stored_name):
    """Download an assignment attachment for users with access to the assignment's course."""
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    course = Course.get_by_id(assignment.courseID)
    if not course:
        return jsonify({"msg": "Course not found"}), 404

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not _can_access_course(user, course):
        return jsonify({"msg": "Unauthorized to access this attachment"}), 403

    assignment_dir, file_path = _resolve_attachment_path(assignment_id, stored_name)
    if not assignment_dir or not file_path:
        return jsonify({"msg": "Attachment not found"}), 404

    original_name = stored_name.split("_", 1)[1] if "_" in stored_name else stored_name
    return send_from_directory(
        assignment_dir,
        stored_name,
        as_attachment=True,
        download_name=original_name,
    )