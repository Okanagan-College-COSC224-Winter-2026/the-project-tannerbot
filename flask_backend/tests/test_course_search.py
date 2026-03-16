"""Tests for course search endpoint (US17)."""

import json


def test_student_search_by_course_name_returns_result_with_metadata(
    test_client, make_admin, enroll_user_in_course
):
    make_admin(email="teacher@example.com", password="teacher", name="Teacher User")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    create_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Math 101"}),
        headers={"Content-Type": "application/json"},
    )
    course_id = create_response.json["class"]["id"]

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {"name": "Student User", "password": "Password123!", "email": "student@example.com"}
        ),
        headers={"Content-Type": "application/json"},
    )
    login_response = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    student_id = login_response.json["id"]

    enroll_user_in_course(user_id=student_id, course_id=course_id)

    response = test_client.get("/course/search?q=Math", headers={"Content-Type": "application/json"})

    assert response.status_code == 200
    payload = response.json
    assert payload["count"] == 1
    assert payload["msg"] is None

    result = payload["results"][0]
    assert result["id"] == course_id
    assert result["name"] == "Math 101"
    assert result["code"] == "Math101".upper()
    assert result["teacher_name"] == "Teacher User"
    assert result["teacher_id"] is not None
    assert result["enrollment_count"] == 1


def test_student_search_by_course_code_returns_result(
    test_client, make_admin, enroll_user_in_course
):
    make_admin(email="teacher@example.com", password="teacher", name="Teacher User")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    create_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "COSC 404"}),
        headers={"Content-Type": "application/json"},
    )
    course_id = create_response.json["class"]["id"]

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {"name": "Student User", "password": "Password123!", "email": "student@example.com"}
        ),
        headers={"Content-Type": "application/json"},
    )
    login_response = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    student_id = login_response.json["id"]

    enroll_user_in_course(user_id=student_id, course_id=course_id)

    response = test_client.get("/course/search?q=COSC404", headers={"Content-Type": "application/json"})

    assert response.status_code == 200
    payload = response.json
    assert payload["count"] == 1
    assert payload["results"][0]["id"] == course_id


def test_search_no_results_returns_clear_message(test_client, make_admin):
    make_admin(email="teacher@example.com", password="teacher", name="Teacher User")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Math 101"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.get(
        "/course/search?q=biology",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 200
    payload = response.json
    assert payload["count"] == 0
    assert payload["results"] == []
    assert payload["msg"] == "No courses found for your search."


def test_search_requires_query(test_client, make_admin):
    make_admin(email="student@example.com", password="Password123!", name="Student User")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.get("/course/search", headers={"Content-Type": "application/json"})

    assert response.status_code == 400
    assert response.json["msg"] == "Search query is required"
