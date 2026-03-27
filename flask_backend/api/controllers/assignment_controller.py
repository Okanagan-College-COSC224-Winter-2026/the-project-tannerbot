from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from ..models import (
    Assignment,
    AssignmentSchema,
    Course,
    CourseGroup,
    Group_Members,
    User,
    User_Course,
    db,
)
from ..services import build_assignment_progress_payload
from .auth_controller import jwt_teacher_required
from .assignment_attachment_controller import (
    list_assignment_attachments,
    save_assignment_attachments,
)

bp = Blueprint("assignment", __name__, url_prefix="/assignment")
VALID_ASSIGNMENT_MODES = {"solo", "group"}


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


def _parse_assignment_mode(mode):
    if mode is None:
        return None
    if not isinstance(mode, str):
        raise ValueError("assignment_mode must be 'solo' or 'group'")
    normalized = mode.strip().lower()
    if normalized not in VALID_ASSIGNMENT_MODES:
        raise ValueError("assignment_mode must be 'solo' or 'group'")
    return normalized


def _get_authenticated_user():
    email = get_jwt_identity()
    return User.get_by_email(email)


def _get_teacher_managed_assignment(assignment_id):
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return None, None, None, (jsonify({"msg": "Assignment not found"}), 404)

    user = _get_authenticated_user()
    if not user:
        return None, None, None, (jsonify({"msg": "User not found"}), 404)

    course = Course.get_by_id(assignment.courseID)
    if not course:
        return None, None, None, (jsonify({"msg": "Course not found"}), 404)

    if course.teacherID != user.id:
        return None, None, None, (
            jsonify({"msg": "Unauthorized: You are not the teacher of this class"}),
            403,
        )

    return assignment, course, user, None


def _serialize_group_members(assignment_id, course, members):
    student_ids = {
        enrollment.userID
        for enrollment in User_Course.query.filter_by(courseID=course.id).all()
    }
    students = {
        user.id: user
        for user in User.query.filter(User.id.in_(student_ids)).all()
        if user.is_student()
    }

    serialized = []
    for member in members:
        student = students.get(member.userID)
        if not student:
            continue
        serialized.append(
            {
                "userID": student.id,
                "assignmentID": assignment_id,
                "groupID": member.groupID,
                "name": student.name,
                "email": student.email,
                "student_id": student.student_id,
            }
        )
    return serialized


def _serialize_assignment_groups(assignment, course):
    groups = CourseGroup.get_by_assignment_id(assignment.id)
    memberships = Group_Members.get_for_assignment(assignment.id)

    members_by_group = {}
    for membership in memberships:
        members_by_group.setdefault(membership.groupID, []).append(membership)

    group_payload = []
    for group in groups:
        group_payload.append(
            {
                "id": group.id,
                "name": group.name,
                "assignmentID": group.assignmentID,
                "members": _serialize_group_members(
                    assignment.id,
                    course,
                    members_by_group.get(group.id, []),
                ),
            }
        )

    return group_payload


def _clear_assignment_groups(assignment_id):
    Group_Members.query.filter_by(assignmentID=assignment_id).delete(synchronize_session=False)
    CourseGroup.query.filter_by(assignmentID=assignment_id).delete(synchronize_session=False)


def _get_course_students(course_id):
    student_ids = {
        enrollment.userID
        for enrollment in User_Course.query.filter_by(courseID=course_id).all()
    }
    if not student_ids:
        return []

    students = [
        user
        for user in User.query.filter(User.id.in_(student_ids)).order_by(User.name.asc()).all()
        if user.is_student()
    ]
    return students

# Assignment attachment handling function - saving, listing, and downloading attachments.
#not too much changed here except for the addition of start_date when creating and editing an assignment
@bp.route("/create_assignment", methods=["POST"])
@jwt_teacher_required
def create_assignment():
    """Create a new assignment for a class where the authenticated user is the teacher"""
    data = _parse_request_data()
    course_id = data.get("courseID")
    assignment_name = data.get("name")
    rubric_text = data.get("rubric")
    description = data.get("description")
    due_date = data.get("due_date")
    start_date = data.get("start_date")
    assignment_mode = data.get("assignment_mode")

    try:
        due_date = _parse_iso_datetime(due_date, "due_date")
        start_date = _parse_iso_datetime(start_date, "start_date")
        assignment_mode = _parse_assignment_mode(assignment_mode) or "solo"
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
    new_assignment = Assignment(
        courseID=course_id,
        name=assignment_name,
        rubric_text=rubric_text,
        assignment_mode=assignment_mode,
        due_date=due_date,
        start_date=start_date,
        description=description,
    )
    Assignment.create(new_assignment)
    saved_files = save_assignment_attachments(new_assignment.id)

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
    data = request.get_json(silent=True) or {}
    assignment, _, _, error = _get_teacher_managed_assignment(assignment_id)
    if error:
        return error

    if not assignment.can_modify():
        return jsonify({"msg": "Assignment cannot be modified after its due date"}), 400

    assignment.name = data.get("name", assignment.name)
    assignment.rubric_text = data.get("rubric", assignment.rubric_text)
    if "description" in data:
        assignment.description = data.get("description")
    
    # Handle due_date update - only update if the key is present in request
    if "due_date" in data:
        due_date = data.get("due_date")
        try:
            assignment.due_date = _parse_iso_datetime(due_date, "due_date")
        except ValueError as exc:
            return jsonify({"msg": str(exc)}), 400
    
    # Handle start_date update - only update if the key is present in request
    if "start_date" in data:
        start_date = data.get("start_date")
        try:
            assignment.start_date = _parse_iso_datetime(start_date, "start_date")
        except ValueError as exc:
            return jsonify({"msg": str(exc)}), 400

    if "assignment_mode" in data:
        try:
            new_mode = _parse_assignment_mode(data.get("assignment_mode"))
        except ValueError as exc:
            return jsonify({"msg": str(exc)}), 400
        assignment.assignment_mode = new_mode
    
    # Validate that start_date does not exceed due_date
    if assignment.start_date and assignment.due_date:
        if assignment.start_date > assignment.due_date:
            return jsonify({"msg": "Start date cannot be after the due date"}), 400

    if assignment.assignment_mode == "solo":
        _clear_assignment_groups(assignment.id)

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
    assignment, _, _, error = _get_teacher_managed_assignment(assignment_id)
    if error:
        return error

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
        assignment_data["attachments"] = list_assignment_attachments(assignment_data["id"])

    return jsonify(assignments_data), 200


@bp.route("/<int:assignment_id>/progress", methods=["GET"])
@jwt_teacher_required
def get_assignment_progress(assignment_id):
    """Get per-student submission/review completion status for one assignment."""
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    course = Course.get_by_id(assignment.courseID)
    if not course:
        return jsonify({"msg": "Class not found"}), 404

    email = get_jwt_identity()
    current_user = User.get_by_email(email)
    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    if course.teacherID != current_user.id and not current_user.is_admin():
        return jsonify({"msg": "Insufficient permissions"}), 403

    payload = build_assignment_progress_payload(assignment)
    return jsonify(payload), 200


@bp.route("/<int:assignment_id>/mode", methods=["PATCH"])
@jwt_teacher_required
def update_assignment_mode(assignment_id):
    """Update assignment collaboration mode (solo/group)."""
    data = request.get_json(silent=True) or {}
    assignment, _, _, error = _get_teacher_managed_assignment(assignment_id)
    if error:
        return error

    try:
        mode = _parse_assignment_mode(data.get("assignment_mode"))
    except ValueError as exc:
        return jsonify({"msg": str(exc)}), 400

    if mode is None:
        return jsonify({"msg": "assignment_mode is required"}), 400

    assignment.assignment_mode = mode
    if mode == "solo":
        _clear_assignment_groups(assignment.id)

    assignment.update()
    return jsonify({"msg": "Assignment mode updated", "assignment": AssignmentSchema().dump(assignment)}), 200


@bp.route("/<int:assignment_id>/grouping", methods=["GET"])
@jwt_teacher_required
def get_assignment_grouping(assignment_id):
    """Return assignment grouping configuration and current groups/members."""
    assignment, course, _, error = _get_teacher_managed_assignment(assignment_id)
    if error:
        return error

    students = _get_course_students(course.id)
    memberships = {m.userID: m.groupID for m in Group_Members.get_for_assignment(assignment.id)}
    student_payload = [
        {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "student_id": student.student_id,
            "groupID": memberships.get(student.id),
        }
        for student in students
    ]

    return (
        jsonify(
            {
                "assignment": AssignmentSchema().dump(assignment),
                "groups": _serialize_assignment_groups(assignment, course),
                "students": student_payload,
            }
        ),
        200,
    )


@bp.route("/<int:assignment_id>/groups", methods=["POST"])
@jwt_teacher_required
def create_assignment_group(assignment_id):
    """Create a named group for a group-mode assignment."""
    data = request.get_json(silent=True) or {}
    assignment, _, _, error = _get_teacher_managed_assignment(assignment_id)
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
    assignment, _, _, error = _get_teacher_managed_assignment(assignment_id)
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
    assignment, _, _, error = _get_teacher_managed_assignment(assignment_id)
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
    assignment, course, _, error = _get_teacher_managed_assignment(assignment_id)
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

    valid_student_ids = {student.id for student in _get_course_students(course.id)}
    invalid_ids = [student_id for student_id in normalized_student_ids if student_id not in valid_student_ids]
    if invalid_ids:
        return jsonify({"msg": "All group members must be students enrolled in the class", "invalid_student_ids": invalid_ids}), 400

    existing_group_members = Group_Members.query.filter_by(
        assignmentID=assignment.id,
        groupID=group.id,
    ).all()
    keep_ids = set(normalized_student_ids)

    for membership in existing_group_members:
        if membership.userID not in keep_ids:
            db.session.delete(membership)

    for student_id in normalized_student_ids:
        existing_membership = Group_Members.get_for_assignment_and_user(assignment.id, student_id)
        if existing_membership and existing_membership.groupID != group.id:
            existing_membership.groupID = group.id
        elif not existing_membership:
            db.session.add(
                Group_Members(
                    userID=student_id,
                    groupID=group.id,
                    assignmentID=assignment.id,
                )
            )

    db.session.commit()

    updated_members = Group_Members.query.filter_by(
        assignmentID=assignment.id,
        groupID=group.id,
    ).all()
    return jsonify({"msg": "Group members updated", "group": {"id": group.id, "name": group.name, "assignmentID": group.assignmentID, "members": _serialize_group_members(assignment.id, course, updated_members)}}), 200
