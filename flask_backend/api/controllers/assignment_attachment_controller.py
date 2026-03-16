import os
import tempfile
import uuid

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from ..models import Assignment, Course, User, User_Course

bp = Blueprint("assignment_attachment", __name__, url_prefix="/assignment")


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


def save_assignment_attachments(assignment_id):
    """Persist uploaded assignment files and return metadata for saved files."""
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


def list_assignment_attachments(assignment_id):
    """List attachment metadata for an assignment."""
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
