import io
import uuid

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Assignment, AssignmentAttachment, Course, User, User_Course
from .auth_controller import jwt_teacher_required

bp = Blueprint("assignment_attachment", __name__, url_prefix="/assignment")
DEFAULT_MAX_ASSIGNMENT_ATTACHMENT_SIZE_BYTES = 10 * 1024 * 1024


def _can_access_course(user, course):
    if user.is_admin():
        return True
    if course.teacherID == user.id:
        return True
    return User_Course.get(user.id, course.id) is not None


def _normalize_original_name(filename):
    if not filename:
        return None

    normalized_name = filename.replace("\\", "/").split("/")[-1].strip()
    if not normalized_name:
        return None

    return normalized_name[:255]


def _serialize_attachment_metadata(assignment_id, attachment):
    return {
        "stored_name": attachment.stored_name,
        "original_name": attachment.original_name,
        "download_url": f"/assignment/{assignment_id}/attachment/{attachment.stored_name}",
    }


def _read_attachment_with_limit(uploaded_file):
    max_file_size = int(
        current_app.config.get(
            "MAX_ASSIGNMENT_ATTACHMENT_SIZE_BYTES",
            DEFAULT_MAX_ASSIGNMENT_ATTACHMENT_SIZE_BYTES,
        )
    )
    content = uploaded_file.read(max_file_size + 1)
    if len(content) > max_file_size:
        raise ValueError(
            f"Attachment exceeds maximum size ({max_file_size} bytes)"
        )
    return content


def _get_assignment_for_teacher_edit(assignment_id):
    """Validate assignment ownership/modification rights for teacher/admin attachment edits."""
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return None, None, (jsonify({"msg": "Assignment not found"}), 404)

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return None, None, (jsonify({"msg": "User not found"}), 404)

    course = Course.get_by_id(assignment.courseID)
    if not course:
        return None, None, (jsonify({"msg": "Course not found"}), 404)

    if course.teacherID != user.id and not user.is_admin():
        return (
            None,
            None,
            (jsonify({"msg": "Unauthorized: You are not the teacher of this class"}), 403),
        )

    if not assignment.can_modify():
        return (
            None,
            None,
            (jsonify({"msg": "Assignment cannot be modified after its due date"}), 400),
        )

    return assignment, user, None


def save_assignment_attachments(assignment_id):
    """Persist uploaded assignment files in the database and return metadata."""
    uploaded_files = []
    for key in ("attachments", "attachment", "files", "file"):
        uploaded_files.extend(request.files.getlist(key))

    # Fallback: accept files from any field name to be resilient to client variations.
    if not uploaded_files:
        for key in request.files.keys():
            uploaded_files.extend(request.files.getlist(key))

    if not uploaded_files:
        return []

    attachments_to_create = []
    for uploaded_file in uploaded_files:
        if not uploaded_file or not uploaded_file.filename:
            continue

        original_name = _normalize_original_name(uploaded_file.filename)
        if not original_name:
            continue

        content = _read_attachment_with_limit(uploaded_file)
        stored_name = uuid.uuid4().hex
        attachment = AssignmentAttachment(
            assignmentID=assignment_id,
            stored_name=stored_name,
            original_name=original_name,
            mime_type=uploaded_file.mimetype,
            size_bytes=len(content),
            content=content,
        )
        attachments_to_create.append(attachment)

    saved_attachments = AssignmentAttachment.create_attachments(attachments_to_create)

    return [
        _serialize_attachment_metadata(assignment_id, attachment)
        for attachment in saved_attachments
    ]


def list_assignment_attachments(assignment_id):
    """List attachment metadata for an assignment."""
    return [
        _serialize_attachment_metadata(assignment_id, attachment)
        for attachment in AssignmentAttachment.get_for_assignment(assignment_id)
    ]


@bp.route("/<int:assignment_id>/attachment", methods=["POST"])
@jwt_teacher_required
def add_assignment_attachments(assignment_id):
    """Add one or more attachments to an existing assignment."""
    assignment, _, error = _get_assignment_for_teacher_edit(assignment_id)
    if error:
        return error

    try:
        saved_files = save_assignment_attachments(assignment.id)
    except ValueError as exc:
        return jsonify({"msg": str(exc)}), 413

    if not saved_files:
        return jsonify({"msg": "No attachments uploaded"}), 400

    return (
        jsonify(
            {
                "msg": "Attachments updated",
                "assignment_id": assignment.id,
                "added_attachments": saved_files,
                "attachments": list_assignment_attachments(assignment.id),
            }
        ),
        200,
    )


@bp.route("/<int:assignment_id>/attachment/<path:stored_name>", methods=["DELETE"])
@jwt_teacher_required
def delete_assignment_attachment(assignment_id, stored_name):
    """Delete an attachment from an existing assignment."""
    assignment, _, error = _get_assignment_for_teacher_edit(assignment_id)
    if error:
        return error

    attachment = AssignmentAttachment.get_by_assignment_and_stored_name(assignment.id, stored_name)
    if not attachment:
        return jsonify({"msg": "Attachment not found"}), 404

    attachment.delete()

    return (
        jsonify(
            {
                "msg": "Attachment deleted",
                "assignment_id": assignment.id,
                "attachments": list_assignment_attachments(assignment.id),
            }
        ),
        200,
    )


@bp.route("/<int:assignment_id>/attachment/<path:stored_name>", methods=["GET"])
@jwt_required()
def download_assignment_attachment(assignment_id, stored_name):
    """Download an assignment attachment stored in the database."""
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

    attachment = AssignmentAttachment.get_by_assignment_and_stored_name(assignment_id, stored_name)
    if not attachment:
        return jsonify({"msg": "Attachment not found"}), 404

    return send_file(
        io.BytesIO(attachment.content),
        mimetype=attachment.mime_type or "application/octet-stream",
        as_attachment=True,
        download_name=attachment.original_name,
    )
