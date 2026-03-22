"""Tests for assignment progress endpoint."""

import json

from api.models import Assignment, CriteriaDescription, Criterion, Review, Rubric, Submission
from api.models.db import db as _db


def _seed_assignment_progress_data(test_client, make_admin, enroll_user_in_course):
    make_admin(
        email="teacher-assignment-progress@example.com",
        password="Password123!",
        name="teacher",
    )

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {
                "name": "student one",
                "password": "Password123!",
                "email": "student-one-assignment-progress@example.com",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    student_one_login = test_client.post(
        "/auth/login",
        data=json.dumps(
            {
                "email": "student-one-assignment-progress@example.com",
                "password": "Password123!",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    student_one_id = student_one_login.json["id"]

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {
                "name": "student two",
                "password": "Password123!",
                "email": "student-two-assignment-progress@example.com",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    student_two_login = test_client.post(
        "/auth/login",
        data=json.dumps(
            {
                "email": "student-two-assignment-progress@example.com",
                "password": "Password123!",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    student_two_id = student_two_login.json["id"]

    test_client.post(
        "/auth/login",
        data=json.dumps(
            {"email": "teacher-assignment-progress@example.com", "password": "Password123!"}
        ),
        headers={"Content-Type": "application/json"},
    )

    create_class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Assignment Progress Class"}),
        headers={"Content-Type": "application/json"},
    )
    course_id = create_class_response.json["class"]["id"]

    enroll_user_in_course(user_id=student_one_id, course_id=course_id)
    enroll_user_in_course(user_id=student_two_id, course_id=course_id)

    assignment = Assignment(courseID=course_id, name="Progress Assignment", rubric_text="")
    _db.session.add(assignment)
    _db.session.commit()

    _db.session.add(
        Submission(
            path="/tmp/student-one-submission.pdf",
            studentID=student_one_id,
            assignmentID=assignment.id,
        )
    )
    _db.session.commit()

    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    _db.session.add(rubric)
    _db.session.commit()

    criterion_row = CriteriaDescription(
        rubricID=rubric.id,
        question="Quality",
        scoreMax=5,
        hasScore=True,
    )
    _db.session.add(criterion_row)
    _db.session.commit()

    complete_review = Review(
        assignmentID=assignment.id,
        reviewerID=student_one_id,
        revieweeID=student_two_id,
    )
    incomplete_review = Review(
        assignmentID=assignment.id,
        reviewerID=student_two_id,
        revieweeID=student_one_id,
    )
    _db.session.add_all([complete_review, incomplete_review])
    _db.session.commit()

    _db.session.add_all(
        [
            Criterion(reviewID=complete_review.id, criterionRowID=criterion_row.id, grade=5),
            Criterion(reviewID=incomplete_review.id, criterionRowID=criterion_row.id, grade=None),
        ]
    )
    _db.session.commit()

    return {
        "assignment_id": assignment.id,
        "teacher_email": "teacher-assignment-progress@example.com",
        "student_one_email": "student-one-assignment-progress@example.com",
        "student_two_email": "student-two-assignment-progress@example.com",
    }


def test_teacher_can_view_assignment_progress(test_client, make_admin, enroll_user_in_course):
    seeded = _seed_assignment_progress_data(test_client, make_admin, enroll_user_in_course)

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": seeded["teacher_email"], "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.get(
        f"/assignment/{seeded['assignment_id']}/progress",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200

    payload = response.json
    assert payload["assignment"]["id"] == seeded["assignment_id"]

    students_by_email = {student["email"]: student for student in payload["students"]}

    student_one = students_by_email[seeded["student_one_email"]]
    assert student_one["has_submitted"] is True
    assert student_one["review_status"] == {
        "has_reviewed": True,
        "completed_assigned_reviews": 1,
        "total_assigned_reviews": 1,
        "pending_assigned_reviews": 0,
        "is_complete": True,
    }

    student_two = students_by_email[seeded["student_two_email"]]
    assert student_two["has_submitted"] is False
    assert student_two["review_status"] == {
        "has_reviewed": False,
        "completed_assigned_reviews": 0,
        "total_assigned_reviews": 1,
        "pending_assigned_reviews": 1,
        "is_complete": False,
    }


def test_student_cannot_view_assignment_progress(test_client, make_admin):
    make_admin(
        email="teacher-assignment-progress-lock@example.com",
        password="Password123!",
        name="teacher",
    )

    test_client.post(
        "/auth/login",
        data=json.dumps(
            {"email": "teacher-assignment-progress-lock@example.com", "password": "Password123!"}
        ),
        headers={"Content-Type": "application/json"},
    )

    create_class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Assignment Progress Lock Class"}),
        headers={"Content-Type": "application/json"},
    )
    course_id = create_class_response.json["class"]["id"]

    create_assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": course_id, "name": "A1", "rubric": "R"}),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = create_assignment_response.json["assignment"]["id"]

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {
                "name": "student-viewer",
                "password": "Password123!",
                "email": "student-view-assignment-progress@example.com",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps(
            {
                "email": "student-view-assignment-progress@example.com",
                "password": "Password123!",
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.get(
        f"/assignment/{assignment_id}/progress",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 403
    assert response.json["msg"] == "Insufficient permissions"
