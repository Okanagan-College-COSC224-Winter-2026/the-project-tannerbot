"""Tests for assignment grouping mode and group membership management."""

import json

from werkzeug.security import generate_password_hash

from api.models import User
from api.models.db import db as _db


def _login(test_client, email, password):
    return test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )


def _register_student(test_client, name, email, password="Password123!"):
    return test_client.post(
        "/auth/register",
        data=json.dumps({"name": name, "email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )


def _create_class_and_assignment(test_client, teacher_email, teacher_password):
    _login(test_client, teacher_email, teacher_password)

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Grouping Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Project 1",
                "assignment_mode": "group",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]

    return class_id, assignment_id


def test_teacher_can_set_group_mode_create_groups_and_assign_students(
    test_client, make_admin, enroll_user_in_course
):
    teacher_email = "teacher-grouping@example.com"
    make_admin(email=teacher_email, password="teacher", name="teacher-grouping")

    class_id, assignment_id = _create_class_and_assignment(test_client, teacher_email, "teacher")

    _register_student(test_client, "Student One", "student-group-1@example.com")
    _register_student(test_client, "Student Two", "student-group-2@example.com")

    with test_client.application.app_context():
        student_one = User.get_by_email("student-group-1@example.com")
        student_two = User.get_by_email("student-group-2@example.com")
        student_one_id = student_one.id
        student_two_id = student_two.id
        enroll_user_in_course(student_one.id, class_id)
        enroll_user_in_course(student_two.id, class_id)

    create_group_response = test_client.post(
        f"/assignment/{assignment_id}/groups",
        data=json.dumps({"name": "Team Alpha"}),
        headers={"Content-Type": "application/json"},
    )
    assert create_group_response.status_code == 201
    group_id = create_group_response.json["group"]["id"]

    assign_members_response = test_client.put(
        f"/assignment/{assignment_id}/groups/{group_id}/members",
        data=json.dumps({"student_ids": [student_one_id, student_two_id]}),
        headers={"Content-Type": "application/json"},
    )
    assert assign_members_response.status_code == 200
    assert len(assign_members_response.json["group"]["members"]) == 2

    grouping_response = test_client.get(f"/assignment/{assignment_id}/grouping")
    assert grouping_response.status_code == 200
    assert grouping_response.json["assignment"]["assignment_mode"] == "group"
    assert len(grouping_response.json["groups"]) == 1
    assert grouping_response.json["groups"][0]["name"] == "Team Alpha"


def test_switching_assignment_to_solo_clears_groups(test_client, make_admin):
    teacher_email = "teacher-solo-switch@example.com"
    make_admin(email=teacher_email, password="teacher", name="teacher-solo-switch")

    _, assignment_id = _create_class_and_assignment(test_client, teacher_email, "teacher")

    create_group_response = test_client.post(
        f"/assignment/{assignment_id}/groups",
        data=json.dumps({"name": "Team Beta"}),
        headers={"Content-Type": "application/json"},
    )
    assert create_group_response.status_code == 201

    mode_response = test_client.patch(
        f"/assignment/{assignment_id}/mode",
        data=json.dumps({"assignment_mode": "solo"}),
        headers={"Content-Type": "application/json"},
    )
    assert mode_response.status_code == 200
    assert mode_response.json["assignment"]["assignment_mode"] == "solo"

    grouping_response = test_client.get(f"/assignment/{assignment_id}/grouping")
    assert grouping_response.status_code == 200
    assert grouping_response.json["groups"] == []


def test_group_members_must_be_enrolled_students(test_client, make_admin):
    teacher_email = "teacher-enrollment-check@example.com"
    make_admin(email=teacher_email, password="teacher", name="teacher-enrollment-check")

    _, assignment_id = _create_class_and_assignment(test_client, teacher_email, "teacher")

    outsider = User(
        name="Outside Student",
        email="outside-student@example.com",
        hash_pass=generate_password_hash("Password123!"),
        role="student",
    )
    User.create_user(outsider)

    create_group_response = test_client.post(
        f"/assignment/{assignment_id}/groups",
        data=json.dumps({"name": "Team Gamma"}),
        headers={"Content-Type": "application/json"},
    )
    group_id = create_group_response.json["group"]["id"]

    assign_members_response = test_client.put(
        f"/assignment/{assignment_id}/groups/{group_id}/members",
        data=json.dumps({"student_ids": [outsider.id]}),
        headers={"Content-Type": "application/json"},
    )
    assert assign_members_response.status_code == 400
    assert assign_members_response.json["msg"] == "All group members must be students enrolled in the class"


def test_student_cannot_manage_assignment_grouping(test_client, make_admin):
    teacher_email = "teacher-lock-grouping@example.com"
    make_admin(email=teacher_email, password="teacher", name="teacher-lock-grouping")

    _, assignment_id = _create_class_and_assignment(test_client, teacher_email, "teacher")

    _register_student(test_client, "Student Locked", "student-locked@example.com")
    _login(test_client, "student-locked@example.com", "Password123!")

    forbidden_response = test_client.post(
        f"/assignment/{assignment_id}/groups",
        data=json.dumps({"name": "Team Locked"}),
        headers={"Content-Type": "application/json"},
    )
    assert forbidden_response.status_code == 403


# Silence lint warning for imported db alias used by fixture side effects.
assert _db is not None
