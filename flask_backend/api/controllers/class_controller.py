from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Course, User, User_Course
from ..services import build_class_progress_payload, calculate_student_course_total_grade
from .auth_controller import jwt_teacher_required

bp = Blueprint("class", __name__, url_prefix="/class")


@bp.route("/create_class", methods=["POST"])
@jwt_teacher_required
def create_class():
    """Create a new class where the authenticated user is the teacher"""
    data = request.get_json()
    class_name = data.get("name")
    if not class_name:
        return jsonify({"msg": "Class name is required"}), 400

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    existing_class = Course.get_by_name(class_name)
    if existing_class:
        return jsonify({"msg": "Class already exists"}), 400

    new_class = Course(teacherID=user.id, name=class_name)
    Course.create_course(new_class)
    return jsonify({"msg": "Class created", "class": {"id": new_class.id}}), 201


@bp.route("/browse_classes", methods=["GET"])
@jwt_required()
def get_classes():
    """Retrieve all classes"""
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    classes = Course.get_all_courses()
    return jsonify([{"id": c.id, "name": c.name} for c in classes]), 200


@bp.route("/classes", methods=["GET"])
@jwt_required()
def get_user_classes():
    """Retrieve classes for the authenticated user (if user is a student look up User_Course, if teacher look up Course, else return empty)"""
    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if user.is_teacher():
        courses = Course.get_courses_by_teacher(user.id)
    elif user.is_admin():
        courses = Course.get_all_courses()
    elif user.is_student():
        user_courses = User_Course.get_courses_by_student(user.id)
        courses = [Course.get_by_id(uc.courseID) for uc in user_courses]
    else:
        courses = []

    payload = []
    for course in courses:
        if not course:
            continue

        row = {"id": course.id, "name": course.name}
        if user.is_student():
            row["total_grade"] = calculate_student_course_total_grade(user.id, course.id)

        payload.append(row)

    return jsonify(payload), 200


@bp.route("/members", methods=["POST"])
@jwt_required()
def get_class_members():
    """Retrieve members for a given class.

    Access allowed for:
    - class teacher
    - admins
    - students enrolled in that class
    """
    data = request.get_json() or {}
    class_id = data.get("id")

    if not class_id:
        return jsonify({"msg": "Class ID is required"}), 400

    course = Course.get_by_id(class_id)
    if not course:
        return jsonify({"msg": "Class not found"}), 404

    email = get_jwt_identity()
    current_user = User.get_by_email(email)
    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    is_teacher_of_class = course.teacherID == current_user.id
    is_admin = current_user.is_admin()
    is_enrolled_student = current_user.is_student() and User_Course.get(current_user.id, class_id)

    if not (is_teacher_of_class or is_admin or is_enrolled_student):
        return jsonify({"msg": "Insufficient permissions"}), 403

    members = course.students
    instructor = course.teacher

    member_rows = []
    seen_ids = set()

    if instructor:
        seen_ids.add(instructor.id)
        member_rows.append(
            {
                "id": instructor.id,
                "student_id": instructor.student_id,
                "name": instructor.name,
                "email": instructor.email,
                "role": instructor.role,
                "is_instructor": True,
                "profile_picture_url": (
                    f"/user/{instructor.id}/profile-picture" if instructor.profile_picture else None
                ),
            }
        )

    for m in members:
        if m.id in seen_ids:
            continue

        member_rows.append(
            {
                "id": m.id,
                "student_id": m.student_id,
                "name": m.name,
                "email": m.email,
                "role": m.role,
                "is_instructor": False,
                "profile_picture_url": f"/user/{m.id}/profile-picture" if m.profile_picture else None,
            }
        )

    return jsonify(member_rows), 200


@bp.route("/<int:class_id>/progress", methods=["GET"])
@jwt_teacher_required
def get_class_progress(class_id):
    """Return comprehensive per-student and per-assignment progress for a class."""
    course = Course.get_by_id(class_id)
    if not course:
        return jsonify({"msg": "Class not found"}), 404

    email = get_jwt_identity()
    current_user = User.get_by_email(email)
    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    if course.teacherID != current_user.id and not current_user.is_admin():
        return jsonify({"msg": "Insufficient permissions"}), 403

    payload = build_class_progress_payload(course)
    return jsonify(payload), 200
