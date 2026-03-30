from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

from ..models import Course, User
from ..services import csv_to_list, enroll_students_in_course
from .auth_controller import jwt_teacher_required

bp = Blueprint("class_enrollment", __name__, url_prefix="/class")


@bp.route("/enroll_students", methods=["POST"])
@jwt_teacher_required
def enroll_students():
    """Enroll students into a class using CSV-formatted student rows."""
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

    enrollment_result, error_message = enroll_students_in_course(students, class_id)
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
