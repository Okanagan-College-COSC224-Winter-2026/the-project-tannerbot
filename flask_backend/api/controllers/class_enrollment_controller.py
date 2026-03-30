from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from ..models import Course, User
from ..services import (
    build_enrollment_preview,
    csv_to_list,
    enroll_students_in_course_with_passwords,
)
from .auth_controller import jwt_teacher_required

bp = Blueprint("class_enrollment", __name__, url_prefix="/class")


@bp.route("/enroll_students", methods=["POST"])
@jwt_teacher_required
def enroll_students():
    """Enroll students into a class using CSV-formatted student rows."""
    data = request.get_json() or {}
    class_id = data.get("class_id")
    student_emails_csv = data.get("students", "")
    default_password = data.get("default_password", "password123")
    student_passwords = data.get("student_passwords", {})

    if not class_id or not student_emails_csv:
        return jsonify({"msg": "Class ID and student emails are required"}), 400

    if not isinstance(default_password, str):
        default_password = "password123"
    if not isinstance(student_passwords, dict):
        student_passwords = {}

    course = Course.get_by_id(class_id)
    if not course:
        return jsonify({"msg": "Class not found"}), 404

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if course.teacherID != user.id:
        return jsonify({"msg": "You are not authorized to enroll students in this class"}), 403

    students, parse_errors = csv_to_list(student_emails_csv)
    if parse_errors:
        return jsonify({"msg": "Errors in CSV", "errors": parse_errors}), 400

    enrollment_result, error_message = enroll_students_in_course_with_passwords(
        students,
        class_id,
        default_password=default_password,
        student_passwords=student_passwords,
    )
    if error_message:
        if error_message.startswith("Invalid email format:"):
            return jsonify({"msg": error_message}), 400
        return jsonify({"msg": error_message}), 500

    return jsonify({
        "msg": f"{len(enrollment_result['enrolled_students'])} students added to course {course.name}",
        "added_count": len(enrollment_result["enrolled_students"]),
        "created_accounts_count": len(enrollment_result["created_accounts"]),
        "already_enrolled_count": len(enrollment_result["already_enrolled"]),
        "already_enrolled": enrollment_result["already_enrolled"],
    }), 200


@bp.route("/enroll_students_preview", methods=["POST"])
@jwt_teacher_required
def enroll_students_preview():
    """Build a preview for student enrollment before creating accounts or enrollments."""
    data = request.get_json() or {}
    class_id = data.get("class_id")
    student_emails_csv = data.get("students", "")

    if not class_id or not student_emails_csv:
        return jsonify({"msg": "Class ID and student emails are required"}), 400

    course = Course.get_by_id(class_id)
    if not course:
        return jsonify({"msg": "Class not found"}), 404

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if course.teacherID != user.id:
        return jsonify({"msg": "You are not authorized to enroll students in this class"}), 403

    students, parse_errors = csv_to_list(student_emails_csv)
    if parse_errors:
        return jsonify({"msg": "Errors in CSV", "errors": parse_errors}), 400

    preview_result, error_message = build_enrollment_preview(students, class_id)
    if error_message:
        if error_message.startswith("Invalid email format:"):
            return jsonify({"msg": error_message}), 400
        return jsonify({"msg": error_message}), 500

    return jsonify(preview_result), 200
