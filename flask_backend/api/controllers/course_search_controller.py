import re

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Course, User, User_Course

bp = Blueprint("course_search", __name__, url_prefix="/course")


def _derive_course_code(course):
    """Derive a display/searchable code from the course name when a dedicated code field does not exist."""
    name = (course.name or "").strip()
    match = re.search(r"[A-Za-z]{2,}\s*-?\s*\d{2,4}[A-Za-z]?", name)
    if match:
        return re.sub(r"\s+", "", match.group(0)).upper()
    return f"C{course.id}"


def _search_normalize(value):
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def _get_visible_courses_for_user(user):
    if user.is_teacher():
        return Course.get_courses_by_teacher(user.id)
    if user.is_admin():
        return Course.get_all_courses()
    if user.is_student():
        user_courses = User_Course.get_courses_by_student(user.id)
        return [Course.get_by_id(uc.courseID) for uc in user_courses]
    return []


@bp.route("/search", methods=["GET"])
@jwt_required()
def search_courses():
    """Search courses visible to the authenticated user by course name or course code."""
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"msg": "Search query is required"}), 400

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    visible_courses = [course for course in _get_visible_courses_for_user(user) if course is not None]

    normalized_query = _search_normalize(query)
    lower_query = query.lower()

    results = []
    for course in visible_courses:
        course_name = course.name or ""
        course_code = _derive_course_code(course)

        name_match = lower_query in course_name.lower()
        code_match = normalized_query in _search_normalize(course_code)
        id_match = query.isdigit() and int(query) == course.id

        if name_match or code_match or id_match:
            results.append(
                {
                    "id": course.id,
                    "name": course_name,
                    "code": course_code,
                    "teacher_id": course.teacherID,
                    "teacher_name": course.teacher.name if course.teacher else None,
                    "enrollment_count": len(course.students),
                }
            )

    results.sort(key=lambda item: item["name"].lower())

    return (
        jsonify(
            {
                "query": query,
                "count": len(results),
                "results": results,
                "msg": None if results else "No courses found for your search.",
            }
        ),
        200,
    )
