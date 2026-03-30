from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from ...models import Assignment, Course, User


def get_authenticated_user():
    email = get_jwt_identity()
    return User.get_by_email(email)


def get_teacher_managed_assignment(assignment_id):
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
        return None, None, None, (
            jsonify({"msg": "Unauthorized: You are not the teacher of this class"}),
            403,
        )

    return assignment, course, user, None
