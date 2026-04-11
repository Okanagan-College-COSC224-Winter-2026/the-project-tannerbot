from ..models import CourseGroup, Group_Members, User, User_Course, db


def clear_assignment_groups(assignment_id):
    Group_Members.query.filter_by(assignmentID=assignment_id).delete(synchronize_session=False)
    CourseGroup.query.filter_by(assignmentID=assignment_id).delete(synchronize_session=False)


def get_course_students(course_id):
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


def serialize_group_members(assignment_id, course, members):
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


def serialize_assignment_groups(assignment, course):
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
                "members": serialize_group_members(
                    assignment.id,
                    course,
                    members_by_group.get(group.id, []),
                ),
            }
        )

    return group_payload


def replace_group_members(assignment, course, group, normalized_student_ids):
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
    return serialize_group_members(assignment.id, course, updated_members)


def build_grouping_student_payload(assignment_id, students):
    memberships = {m.userID: m.groupID for m in Group_Members.get_for_assignment(assignment_id)}
    return [
        {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "student_id": student.student_id,
            "groupID": memberships.get(student.id),
        }
        for student in students
    ]


def auto_assign_students_to_groups(assignment, groups, students):
    """Auto-assign students to groups, favoring even-sized groups when possible."""
    ordered_groups = sorted(groups, key=lambda group: group.id)
    student_ids = [student.id for student in students]

    assignments_by_group = {group.id: [] for group in ordered_groups}

    # Assign in pairs so group sizes stay even where possible.
    for index in range(0, len(student_ids), 2):
        pair = student_ids[index : index + 2]
        target_group_id = min(
            assignments_by_group,
            key=lambda group_id: (len(assignments_by_group[group_id]), group_id),
        )
        assignments_by_group[target_group_id].extend(pair)

    for membership in Group_Members.get_for_assignment(assignment.id):
        db.session.delete(membership)

    for group in ordered_groups:
        for student_id in assignments_by_group[group.id]:
            db.session.add(
                Group_Members(
                    userID=student_id,
                    groupID=group.id,
                    assignmentID=assignment.id,
                )
            )

    db.session.commit()
    return assignments_by_group
