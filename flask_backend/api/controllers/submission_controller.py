import io
import mimetypes
import os
import tempfile
import uuid

from flask import Blueprint, current_app, jsonify, request, send_file
from sqlalchemy import or_

from ..models import Assignment, Course, Submission, User_Course
from ..models.group_members_model import Group_Members
from .auth_controller import jwt_role_required, jwt_teacher_required
from .helpers import get_authenticated_user

bp = Blueprint("submission", __name__, url_prefix="/assignment")


def _normalize_original_name(filename):
    if not filename:
        return None

    normalized_name = filename.replace("\\", "/").split("/")[-1].strip()
    if not normalized_name:
        return None

    # Keep room for generated prefix and separator in stored file names.
    return normalized_name[:200]


def _serialize_submission(assignment_id, submission):
    original_name = _extract_original_name(submission.path)

    return {
        "id": submission.id,
        "assignment_id": assignment_id,
        "original_name": original_name,
        "download_url": f"/assignment/{assignment_id}/submission/download",
    }


def _extract_original_name(stored_name):
    normalized = os.path.basename(stored_name or "")
    if "__" in normalized:
        _, original_name = normalized.split("__", 1)
        return original_name
    return normalized


def _extract_uploaded_submission_file():
    uploaded_files = []
    for key in ("submission", "file", "files", "attachment", "attachments"):
        uploaded_files.extend(request.files.getlist(key))

    if not uploaded_files:
        for key in request.files.keys():
            uploaded_files.extend(request.files.getlist(key))

    for uploaded_file in uploaded_files:
        if uploaded_file and uploaded_file.filename:
            return uploaded_file

    return None


def _get_submission_storage_root():
    configured_root = current_app.config.get(
        "ASSIGNMENT_UPLOAD_FOLDER",
        os.path.join(current_app.instance_path, "assignment_uploads"),
    )
    if configured_root:
        return configured_root
    return os.path.join(tempfile.gettempdir(), "peer_eval_assignment_uploads")


def _get_submission_file_path(assignment_id, student_id, stored_name):
    safe_name = os.path.basename(stored_name or "")
    return os.path.join(
        _get_submission_storage_root(),
        str(assignment_id),
        str(student_id),
        safe_name,
    )


def _validate_student_assignment_access(assignment_id):
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return None, None, None, (jsonify({"msg": "Assignment not found"}), 404)

    user = get_authenticated_user()
    if not user:
        return None, None, None, (jsonify({"msg": "User not found"}), 404)

    course = Course.get_by_id(assignment.courseID)
    if not course:
        return None, None, None, (jsonify({"msg": "Course not found"}), 404)

    if User_Course.get(user.id, course.id) is None:
        return None, None, None, (jsonify({"msg": "Insufficient permissions"}), 403)

    return assignment, course, user, None


def _validate_teacher_assignment_access(assignment_id):
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return None, None, None, (jsonify({"msg": "Assignment not found"}), 404)

    user = get_authenticated_user()
    if not user:
        return None, None, None, (jsonify({"msg": "User not found"}), 404)

    course = Course.get_by_id(assignment.courseID)
    if not course:
        return None, None, None, (jsonify({"msg": "Course not found"}), 404)

    if course.teacherID != user.id and not user.is_admin():
        return None, None, None, (jsonify({"msg": "Insufficient permissions"}), 403)

    return assignment, course, user, None


def _get_group_member_ids_for_assignment(assignment_id, student_id):
    membership = Group_Members.get_for_assignment_and_user(assignment_id, student_id)
    if not membership:
        return None, (jsonify({"msg": "You must be assigned to a group before submitting"}), 400)

    group_members = (
        Group_Members.query.filter_by(groupID=membership.groupID)
        .filter(
            or_(
                Group_Members.assignmentID == int(assignment_id),
                Group_Members.assignmentID.is_(None),
            )
        )
        .all()
    )
    member_ids = sorted({member.userID for member in group_members})
    if not member_ids:
        return None, (jsonify({"msg": "Group has no members"}), 400)

    return member_ids, None


def _find_group_submission(assignment_id, member_ids):
    if not member_ids:
        return None
    return (
        Submission.query.filter(
            Submission.assignmentID == int(assignment_id),
            Submission.studentID.in_(member_ids),
        )
        .order_by(Submission.id.asc())
        .first()
    )


@bp.route("/<int:assignment_id>/submission", methods=["GET"])
@jwt_role_required("student")
def get_my_submission(assignment_id):
    assignment, _, student, error = _validate_student_assignment_access(assignment_id)
    if error:
        return error

    if assignment.assignment_mode == "group":
        member_ids, membership_error = _get_group_member_ids_for_assignment(assignment.id, student.id)
        if membership_error:
            return jsonify({"has_submitted": False, "submission": None}), 200
        submission = _find_group_submission(assignment.id, member_ids)
    else:
        submission = Submission.get_by_assignment_and_student(assignment.id, student.id)

    if not submission:
        return jsonify({"has_submitted": False, "submission": None}), 200

    return jsonify({"has_submitted": True, "submission": _serialize_submission(assignment.id, submission)}), 200


@bp.route("/<int:assignment_id>/submission", methods=["POST"])
@jwt_role_required("student")
def upload_submission(assignment_id):
    assignment, _, student, error = _validate_student_assignment_access(assignment_id)
    if error:
        return error

    group_member_ids = None
    existing_group_submission = None
    if assignment.assignment_mode == "group":
        group_member_ids, membership_error = _get_group_member_ids_for_assignment(assignment.id, student.id)
        if membership_error:
            return membership_error
        existing_group_submission = _find_group_submission(assignment.id, group_member_ids)
        if existing_group_submission and existing_group_submission.studentID != student.id:
            return jsonify({"msg": "Your group has already submitted this assignment"}), 409

    uploaded_file = _extract_uploaded_submission_file()
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"msg": "No submission file uploaded"}), 400

    original_name = _normalize_original_name(uploaded_file.filename)
    if not original_name:
        return jsonify({"msg": "Invalid file name"}), 400

    content = uploaded_file.read()
    if not content:
        return jsonify({"msg": "Uploaded submission file is empty"}), 400

    stored_name = f"{uuid.uuid4().hex}__{original_name}"
    file_path = _get_submission_file_path(assignment.id, student.id, stored_name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as output_file:
        output_file.write(content)

    submission = Submission.get_by_assignment_and_student(assignment.id, student.id)
    if assignment.assignment_mode == "group" and existing_group_submission is not None:
        submission = existing_group_submission

    if submission and submission.path:
        previous_path = _get_submission_file_path(assignment.id, submission.studentID, submission.path)
        if os.path.isfile(previous_path):
            os.remove(previous_path)

    if submission:
        submission.path = stored_name
        submission.update()
    else:
        submission = Submission(path=stored_name, studentID=student.id, assignmentID=assignment.id)
        Submission.create_submission(submission)

    return (
        jsonify(
            {
                "msg": "Submission uploaded",
                "has_submitted": True,
                "submission": _serialize_submission(assignment.id, submission),
            }
        ),
        200,
    )


@bp.route("/<int:assignment_id>/submission/download", methods=["GET"])
@jwt_role_required("student")
def download_my_submission(assignment_id):
    assignment, _, student, error = _validate_student_assignment_access(assignment_id)
    if error:
        return error

    if assignment.assignment_mode == "group":
        member_ids, membership_error = _get_group_member_ids_for_assignment(assignment.id, student.id)
        if membership_error:
            return jsonify({"msg": "Submission not found"}), 404
        submission = _find_group_submission(assignment.id, member_ids)
    else:
        submission = Submission.get_by_assignment_and_student(assignment.id, student.id)

    if not submission or not submission.path:
        return jsonify({"msg": "Submission not found"}), 404

    stored_name = os.path.basename(submission.path)
    file_path = _get_submission_file_path(assignment.id, submission.studentID, stored_name)
    if not os.path.isfile(file_path):
        return jsonify({"msg": "Submission file not found"}), 404

    original_name = _extract_original_name(stored_name)

    with open(file_path, "rb") as submission_file:
        content = submission_file.read()

    guessed_mimetype, _ = mimetypes.guess_type(original_name)

    return send_file(
        io.BytesIO(content),
        mimetype=guessed_mimetype or "application/octet-stream",
        as_attachment=True,
        download_name=original_name,
    )


@bp.route("/<int:assignment_id>/submission/<int:student_id>/download", methods=["GET"])
@jwt_teacher_required
def download_student_submission(assignment_id, student_id):
    assignment, _, _, error = _validate_teacher_assignment_access(assignment_id)
    if error:
        return error

    submission = Submission.get_by_assignment_and_student(assignment.id, int(student_id))
    if not submission or not submission.path:
        return jsonify({"msg": "Submission not found"}), 404

    stored_name = os.path.basename(submission.path)
    file_path = _get_submission_file_path(assignment.id, submission.studentID, stored_name)
    if not os.path.isfile(file_path):
        return jsonify({"msg": "Submission file not found"}), 404

    original_name = _extract_original_name(stored_name)

    with open(file_path, "rb") as submission_file:
        content = submission_file.read()

    guessed_mimetype, _ = mimetypes.guess_type(original_name)
    return send_file(
        io.BytesIO(content),
        mimetype=guessed_mimetype or "application/octet-stream",
        as_attachment=True,
        download_name=original_name,
    )