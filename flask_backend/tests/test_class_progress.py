"""Tests for instructor class progress view endpoint."""

import json

from api.models import Assignment, CriteriaDescription, Criterion, Review, Rubric, Submission
from api.models.db import db as _db


def _seed_progress_data(test_client, make_admin, enroll_user_in_course):
    instructor = make_admin(
        email="instructor-progress@example.com",
        password="Password123!",
        name="instructor",
    )

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {"name": "student-one", "password": "Password123!", "email": "student-one@example.com"}
        ),
        headers={"Content-Type": "application/json"},
    )
    student_one_login = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student-one@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    student_one_id = student_one_login.json["id"]

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {"name": "student-two", "password": "Password123!", "email": "student-two@example.com"}
        ),
        headers={"Content-Type": "application/json"},
    )
    student_two_login = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student-two@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    student_two_id = student_two_login.json["id"]

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "instructor-progress@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    create_class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Progress Analytics 101"}),
        headers={"Content-Type": "application/json"},
    )
    course_id = create_class_response.json["class"]["id"]

    enroll_user_in_course(user_id=student_one_id, course_id=course_id)
    enroll_user_in_course(user_id=student_two_id, course_id=course_id)

    assignment_one = Assignment(courseID=course_id, name="Assignment 1", rubric_text="")
    assignment_two = Assignment(courseID=course_id, name="Assignment 2", rubric_text="")
    _db.session.add_all([assignment_one, assignment_two])
    _db.session.commit()

    # Student one has submitted assignment one only.
    _db.session.add(
        Submission(
            path="/tmp/submissions/student-one-assignment-one.pdf",
            studentID=student_one_id,
            assignmentID=assignment_one.id,
        )
    )
    _db.session.commit()

    rubric = Rubric(assignmentID=assignment_one.id, canComment=True)
    _db.session.add(rubric)
    _db.session.commit()

    criterion_row = CriteriaDescription(
        rubricID=rubric.id,
        question="Correctness",
        scoreMax=5,
        hasScore=True,
    )
    _db.session.add(criterion_row)
    _db.session.commit()

    review_complete = Review(
        assignmentID=assignment_one.id,
        reviewerID=student_one_id,
        revieweeID=student_two_id,
    )
    review_incomplete = Review(
        assignmentID=assignment_one.id,
        reviewerID=student_two_id,
        revieweeID=student_one_id,
    )
    _db.session.add_all([review_complete, review_incomplete])
    _db.session.commit()

    _db.session.add_all(
        [
            Criterion(reviewID=review_complete.id, criterionRowID=criterion_row.id, grade=4),
            Criterion(reviewID=review_incomplete.id, criterionRowID=criterion_row.id, grade=None),
        ]
    )
    _db.session.commit()

    return {
        "course_id": course_id,
        "instructor_email": instructor.email,
        "student_one_email": "student-one@example.com",
        "student_two_email": "student-two@example.com",
    }


def test_instructor_can_view_class_progress_statuses(test_client, make_admin, enroll_user_in_course):
    seeded = _seed_progress_data(test_client, make_admin, enroll_user_in_course)

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": seeded["instructor_email"], "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.get(
        f"/class/{seeded['course_id']}/progress",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200

    payload = response.json
    assert payload["class"]["id"] == seeded["course_id"]

    students_by_email = {student["email"]: student for student in payload["students"]}
    student_one = students_by_email[seeded["student_one_email"]]
    student_two = students_by_email[seeded["student_two_email"]]

    assert student_one["submission_status"] == {
        "submitted_assignments": 1,
        "total_assignments": 2,
        "pending_assignments": 1,
        "is_complete": False,
    }
    assert student_two["submission_status"] == {
        "submitted_assignments": 0,
        "total_assignments": 2,
        "pending_assignments": 2,
        "is_complete": False,
    }

    assert student_one["review_completion_status"] == {
        "completed_reviews": 1,
        "total_reviews": 1,
        "pending_reviews": 0,
        "is_complete": True,
    }
    assert student_two["review_completion_status"] == {
        "completed_reviews": 0,
        "total_reviews": 1,
        "pending_reviews": 1,
        "is_complete": False,
    }

    assignments_by_name = {assignment["name"]: assignment for assignment in payload["assignments"]}
    assert assignments_by_name["Assignment 1"]["submission_status"] == {
        "submitted_students": 1,
        "total_students": 2,
        "missing_students": 1,
        "is_complete": False,
    }
    assert assignments_by_name["Assignment 2"]["submission_status"] == {
        "submitted_students": 0,
        "total_students": 2,
        "missing_students": 2,
        "is_complete": False,
    }


def test_student_cannot_access_class_progress(test_client, make_admin):
    make_admin(
        email="instructor-lock@example.com",
        password="Password123!",
        name="instructor",
    )

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "instructor-lock@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    create_class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Restricted Progress 101"}),
        headers={"Content-Type": "application/json"},
    )
    course_id = create_class_response.json["class"]["id"]

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {
                "name": "student-viewer",
                "password": "Password123!",
                "email": "student-viewer@example.com",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student-viewer@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.get(f"/class/{course_id}/progress", headers={"Content-Type": "application/json"})
    assert response.status_code == 403
    assert response.json["msg"] == "Insufficient permissions"
