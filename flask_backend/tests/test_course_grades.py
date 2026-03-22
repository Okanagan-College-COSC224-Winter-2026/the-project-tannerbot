"""Tests for student course total grade behavior on class listing endpoints."""

import json

from api.models import Assignment, Course, CriteriaDescription, Criterion, Review, Rubric
from api.models.db import db as _db


def _seed_student_course_grade_data(test_client, make_admin, enroll_user_in_course, grade_value=None):
    teacher = make_admin(
        email="teacher-grade@example.com",
        password="Password123!",
        name="teacher",
    )

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {"name": "reviewer", "password": "Password123!", "email": "reviewer-grade@example.com"}
        ),
        headers={"Content-Type": "application/json"},
    )
    reviewer_login = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "reviewer-grade@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    reviewer_id = reviewer_login.json["id"]

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {"name": "student", "password": "Password123!", "email": "student-grade@example.com"}
        ),
        headers={"Content-Type": "application/json"},
    )
    reviewee_login = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student-grade@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    reviewee_id = reviewee_login.json["id"]

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher-grade@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Calculus 101"}),
        headers={"Content-Type": "application/json"},
    )
    course_id = class_response.json["class"]["id"]

    enroll_user_in_course(user_id=reviewer_id, course_id=course_id)
    enroll_user_in_course(user_id=reviewee_id, course_id=course_id)

    course = Course.get_by_id(course_id)

    assignment = Assignment(courseID=course.id, name="Limits", rubric_text="")
    _db.session.add(assignment)
    _db.session.commit()

    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    _db.session.add(rubric)
    _db.session.commit()

    criterion_row = CriteriaDescription(
        rubricID=rubric.id,
        question="Mathematical correctness",
        scoreMax=5,
        hasScore=True,
    )
    _db.session.add(criterion_row)
    _db.session.commit()

    review = Review(assignmentID=assignment.id, reviewerID=reviewer_id, revieweeID=reviewee_id)
    _db.session.add(review)
    _db.session.commit()

    criterion = Criterion(reviewID=review.id, criterionRowID=criterion_row.id, grade=grade_value)
    _db.session.add(criterion)
    _db.session.commit()

    return {
        "reviewee_email": "student-grade@example.com",
        "course": course,
    }


def test_get_courses_for_student_includes_total_grade_when_available(
    test_client, make_admin, enroll_user_in_course
):
    seeded = _seed_student_course_grade_data(
        test_client,
        make_admin,
        enroll_user_in_course,
        grade_value=4,
    )

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": seeded["reviewee_email"], "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.get("/class/classes", headers={"Content-Type": "application/json"})
    assert response.status_code == 200

    course_payload = next(c for c in response.json if c["id"] == seeded["course"].id)
    assert course_payload["name"] == seeded["course"].name
    assert course_payload["total_grade"] == 80.0


def test_get_courses_for_student_marks_total_grade_unavailable_when_missing(
    test_client, make_admin, enroll_user_in_course
):
    seeded = _seed_student_course_grade_data(
        test_client,
        make_admin,
        enroll_user_in_course,
        grade_value=None,
    )

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": seeded["reviewee_email"], "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.get("/class/classes", headers={"Content-Type": "application/json"})
    assert response.status_code == 200

    course_payload = next(c for c in response.json if c["id"] == seeded["course"].id)
    assert course_payload["total_grade"] is None
