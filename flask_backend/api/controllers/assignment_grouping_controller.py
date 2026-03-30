from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..models import AssignmentSchema, CourseGroup, db
from ..services import (
    build_grouping_student_payload,
    get_course_students,
    replace_group_members,
    serialize_assignment_groups,
)
from .auth_controller import jwt_teacher_required
from .helpers import get_teacher_managed_assignment


@bp.route("/<int:assignment_id>/grouping", methods=["GET"])
@jwt_teacher_required
def get_assignment_grouping(assignment_id):
    """Return assignment grouping configuration and current groups/members."""
    assignment, course, _, error = get_teacher_managed_assignment(assignment_id)
    if error:
        return error

    students = get_course_students(course.id)
    return (
        jsonify(
            {
                "assignment": AssignmentSchema().dump(assignment),
                "groups": serialize_assignment_groups(assignment, course),
                "students": build_grouping_student_payload(assignment.id, students),
            }
        ),
        200,
    )


@bp.route("/<int:assignment_id>/groups", methods=["POST"])
@jwt_teacher_required
def create_assignment_group(assignment_id):
    """Create a named group for a group-mode assignment."""
    data = request.get_json(silent=True) or {}
    assignment, _, _, error = get_teacher_managed_assignment(assignment_id)
    if error:
        return error

    if assignment.assignment_mode != "group":
        return jsonify({"msg": "Assignment must be in group mode"}), 400

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"msg": "Group name is required"}), 400

    group = CourseGroup(name=name, assignmentID=assignment.id)
    db.session.add(group)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"msg": "Group name already exists for this assignment"}), 400

    return jsonify({"msg": "Group created", "group": {"id": group.id, "name": group.name, "assignmentID": group.assignmentID}}), 201


@bp.route("/<int:assignment_id>/groups/<int:group_id>", methods=["PATCH"])
@jwt_teacher_required
def rename_assignment_group(assignment_id, group_id):
    """Rename an existing assignment group."""
    data = request.get_json(silent=True) or {}
    assignment, _, _, error = get_teacher_managed_assignment(assignment_id)
    if error:
        return error

    group = CourseGroup.get_by_id(group_id)
    if not group or group.assignmentID != assignment.id:
        return jsonify({"msg": "Group not found"}), 404

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"msg": "Group name is required"}), 400

    group.name = name
    try:
        group.update()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"msg": "Group name already exists for this assignment"}), 400

    return jsonify({"msg": "Group updated", "group": {"id": group.id, "name": group.name, "assignmentID": group.assignmentID}}), 200


@bp.route("/<int:assignment_id>/groups/<int:group_id>", methods=["DELETE"])
@jwt_teacher_required
def delete_assignment_group(assignment_id, group_id):
    """Delete an assignment group and all member assignments in that group."""
    assignment, _, _, error = get_teacher_managed_assignment(assignment_id)
    if error:
        return error

    group = CourseGroup.get_by_id(group_id)
    if not group or group.assignmentID != assignment.id:
        return jsonify({"msg": "Group not found"}), 404

    group.delete()
    return jsonify({"msg": "Group deleted"}), 200


@bp.route("/<int:assignment_id>/groups/<int:group_id>/members", methods=["PUT"])
@jwt_teacher_required
def replace_assignment_group_members(assignment_id, group_id):
    """Replace all members for a group with the provided student id list."""
    data = request.get_json(silent=True) or {}
    assignment, course, _, error = get_teacher_managed_assignment(assignment_id)
    if error:
        return error

    if assignment.assignment_mode != "group":
        return jsonify({"msg": "Assignment must be in group mode"}), 400

    group = CourseGroup.get_by_id(group_id)
    if not group or group.assignmentID != assignment.id:
        return jsonify({"msg": "Group not found"}), 404

    student_ids = data.get("student_ids")
    if not isinstance(student_ids, list):
        return jsonify({"msg": "student_ids must be a list"}), 400

    try:
        normalized_student_ids = sorted({int(student_id) for student_id in student_ids})
    except (TypeError, ValueError):
        return jsonify({"msg": "student_ids must contain valid integers"}), 400

    valid_student_ids = {student.id for student in get_course_students(course.id)}
    invalid_ids = [
        student_id
        for student_id in normalized_student_ids
        if student_id not in valid_student_ids
    ]
    if invalid_ids:
        return jsonify({
            "msg": "All group members must be students enrolled in the class",
            "invalid_student_ids": invalid_ids,
        }), 400

    members_payload = replace_group_members(
        assignment,
        course,
        group,
        normalized_student_ids,
    )
    return jsonify({"msg": "Group members updated", "group": {"id": group.id, "name": group.name, "assignmentID": group.assignmentID, "members": members_payload}}), 200
