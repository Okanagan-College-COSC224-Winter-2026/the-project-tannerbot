"""Tests for student assignment submission file uploads."""

import io
import json

from api.models import Submission


def _seed_assignment_with_student(test_client, make_teacher, enroll_user_in_course):
    teacher_email = "teacher-submission@example.com"
    teacher_password = "Password123!"
    student_email = "student-submission@example.com"
    student_password = "Password123!"

    make_teacher(email=teacher_email, password=teacher_password, name="Submission Teacher")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": teacher_email, "password": teacher_password}),
        headers={"Content-Type": "application/json"},
    )

    create_class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Submission Class"}),
        headers={"Content-Type": "application/json"},
    )
    course_id = create_class_response.json["class"]["id"]

    create_assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": course_id, "name": "Submission Assignment", "rubric": "R"}),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = create_assignment_response.json["assignment"]["id"]

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {
                "name": "submission student",
                "password": student_password,
                "email": student_email,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    student_login_response = test_client.post(
        "/auth/login",
        data=json.dumps({"email": student_email, "password": student_password}),
        headers={"Content-Type": "application/json"},
    )
    student_id = student_login_response.json["id"]

    enroll_user_in_course(user_id=student_id, course_id=course_id)

    return {
        "course_id": course_id,
        "assignment_id": assignment_id,
        "student_id": student_id,
        "teacher_email": teacher_email,
        "teacher_password": teacher_password,
        "student_email": student_email,
        "student_password": student_password,
    }


def test_student_can_upload_and_download_submission_any_file_type(
    test_client,
    make_teacher,
    enroll_user_in_course,
):
    seeded = _seed_assignment_with_student(test_client, make_teacher, enroll_user_in_course)

    test_client.post(
        "/auth/login",
        data=json.dumps(
            {"email": seeded["student_email"], "password": seeded["student_password"]}
        ),
        headers={"Content-Type": "application/json"},
    )

    upload_response = test_client.post(
        f"/assignment/{seeded['assignment_id']}/submission",
        data={"attachments": (io.BytesIO(b"student-submission-bytes"), "report.customext")},
        content_type="multipart/form-data",
    )

    assert upload_response.status_code == 200
    assert upload_response.json["msg"] == "Submission uploaded"
    assert upload_response.json["has_submitted"] is True
    assert upload_response.json["submission"]["original_name"] == "report.customext"

    status_response = test_client.get(f"/assignment/{seeded['assignment_id']}/submission")
    assert status_response.status_code == 200
    assert status_response.json["has_submitted"] is True

    download_response = test_client.get(f"/assignment/{seeded['assignment_id']}/submission/download")
    assert download_response.status_code == 200
    assert download_response.data == b"student-submission-bytes"


def test_student_reupload_replaces_existing_submission(
    test_client,
    make_teacher,
    enroll_user_in_course,
):
    seeded = _seed_assignment_with_student(test_client, make_teacher, enroll_user_in_course)

    test_client.post(
        "/auth/login",
        data=json.dumps(
            {"email": seeded["student_email"], "password": seeded["student_password"]}
        ),
        headers={"Content-Type": "application/json"},
    )

    first_upload = test_client.post(
        f"/assignment/{seeded['assignment_id']}/submission",
        data={"submission": (io.BytesIO(b"first-version"), "v1.txt")},
        content_type="multipart/form-data",
    )
    assert first_upload.status_code == 200

    second_upload = test_client.post(
        f"/assignment/{seeded['assignment_id']}/submission",
        data={"submission": (io.BytesIO(b"second-version"), "v2.bin")},
        content_type="multipart/form-data",
    )
    assert second_upload.status_code == 200
    assert second_upload.json["submission"]["original_name"] == "v2.bin"

    download_response = test_client.get(f"/assignment/{seeded['assignment_id']}/submission/download")
    assert download_response.status_code == 200
    assert download_response.data == b"second-version"

    submissions = Submission.query.filter_by(assignmentID=seeded["assignment_id"]).all()
    assert len(submissions) == 1


def test_student_not_enrolled_cannot_upload_submission(test_client, make_teacher):
    teacher_email = "teacher-block-submission@example.com"
    teacher_password = "Password123!"
    make_teacher(email=teacher_email, password=teacher_password, name="Teacher")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": teacher_email, "password": teacher_password}),
        headers={"Content-Type": "application/json"},
    )

    create_class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Blocked Submission Class"}),
        headers={"Content-Type": "application/json"},
    )
    course_id = create_class_response.json["class"]["id"]

    create_assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": course_id, "name": "Blocked Assignment", "rubric": "R"}),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = create_assignment_response.json["assignment"]["id"]

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {
                "name": "unenrolled student",
                "password": "Password123!",
                "email": "unenrolled-submission@example.com",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps(
            {
                "email": "unenrolled-submission@example.com",
                "password": "Password123!",
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    upload_response = test_client.post(
        f"/assignment/{assignment_id}/submission",
        data={"submission": (io.BytesIO(b"not-allowed"), "blocked.txt")},
        content_type="multipart/form-data",
    )

    assert upload_response.status_code == 403
    assert upload_response.json["msg"] == "Insufficient permissions"


def test_teacher_cannot_upload_student_submission(test_client, make_teacher):
    teacher_email = "teacher-no-student-submit@example.com"
    teacher_password = "Password123!"
    make_teacher(email=teacher_email, password=teacher_password, name="Teacher")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": teacher_email, "password": teacher_password}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Teacher Submission Restriction"}),
        headers={"Content-Type": "application/json"},
    )
    course_id = class_response.json["class"]["id"]

    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": course_id, "name": "A1", "rubric": "R"}),
        headers={"Content-Type": "application/json"},
    )

    upload_response = test_client.post(
        f"/assignment/{assignment_response.json['assignment']['id']}/submission",
        data={"submission": (io.BytesIO(b"teacher-cannot-submit"), "teacher.txt")},
        content_type="multipart/form-data",
    )

    assert upload_response.status_code == 403
    assert upload_response.json["msg"] == "Insufficient permissions"


def test_group_assignment_allows_only_one_submission_per_group(
    test_client,
    make_teacher,
    enroll_user_in_course,
):
    seeded = _seed_assignment_with_student(test_client, make_teacher, enroll_user_in_course)

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {
                "name": "group teammate",
                "password": "Password123!",
                "email": "group-teammate@example.com",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    teammate_login = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "group-teammate@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    teammate_id = teammate_login.json["id"]
    enroll_user_in_course(user_id=teammate_id, course_id=seeded["course_id"])

    test_client.post(
        "/auth/login",
        data=json.dumps(
            {"email": seeded["teacher_email"], "password": seeded["teacher_password"]}
        ),
        headers={"Content-Type": "application/json"},
    )

    mode_response = test_client.patch(
        f"/assignment/{seeded['assignment_id']}/mode",
        data=json.dumps({"assignment_mode": "group"}),
        headers={"Content-Type": "application/json"},
    )
    assert mode_response.status_code == 200

    create_group = test_client.post(
        f"/assignment/{seeded['assignment_id']}/groups",
        data=json.dumps({"name": "Team One"}),
        headers={"Content-Type": "application/json"},
    )
    assert create_group.status_code == 201
    group_id = create_group.json["group"]["id"]

    student_login = test_client.post(
        "/auth/login",
        data=json.dumps(
            {"email": seeded["student_email"], "password": seeded["student_password"]}
        ),
        headers={"Content-Type": "application/json"},
    )
    student_id = student_login.json["id"]

    test_client.post(
        "/auth/login",
        data=json.dumps(
            {"email": seeded["teacher_email"], "password": seeded["teacher_password"]}
        ),
        headers={"Content-Type": "application/json"},
    )
    add_members = test_client.put(
        f"/assignment/{seeded['assignment_id']}/groups/{group_id}/members",
        data=json.dumps({"student_ids": [student_id, teammate_id]}),
        headers={"Content-Type": "application/json"},
    )
    assert add_members.status_code == 200

    test_client.post(
        "/auth/login",
        data=json.dumps(
            {"email": seeded["student_email"], "password": seeded["student_password"]}
        ),
        headers={"Content-Type": "application/json"},
    )

    first_upload = test_client.post(
        f"/assignment/{seeded['assignment_id']}/submission",
        data={"submission": (io.BytesIO(b"group-version-1"), "group1.zip")},
        content_type="multipart/form-data",
    )
    assert first_upload.status_code == 200

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "group-teammate@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    second_upload = test_client.post(
        f"/assignment/{seeded['assignment_id']}/submission",
        data={"submission": (io.BytesIO(b"group-version-2"), "group2.zip")},
        content_type="multipart/form-data",
    )
    assert second_upload.status_code == 409
    assert second_upload.json["msg"] == "Your group has already submitted this assignment"

    status_response = test_client.get(f"/assignment/{seeded['assignment_id']}/submission")
    assert status_response.status_code == 200
    assert status_response.json["has_submitted"] is True
    assert status_response.json["submission"]["original_name"] == "group1.zip"

    download_response = test_client.get(f"/assignment/{seeded['assignment_id']}/submission/download")
    assert download_response.status_code == 200
    assert download_response.data == b"group-version-1"


def test_group_assignment_requires_group_membership_for_submission(
    test_client,
    make_teacher,
    enroll_user_in_course,
):
    seeded = _seed_assignment_with_student(test_client, make_teacher, enroll_user_in_course)

    test_client.post(
        "/auth/login",
        data=json.dumps(
            {"email": seeded["teacher_email"], "password": seeded["teacher_password"]}
        ),
        headers={"Content-Type": "application/json"},
    )

    mode_response = test_client.patch(
        f"/assignment/{seeded['assignment_id']}/mode",
        data=json.dumps({"assignment_mode": "group"}),
        headers={"Content-Type": "application/json"},
    )
    assert mode_response.status_code == 200

    test_client.post(
        "/auth/login",
        data=json.dumps(
            {"email": seeded["student_email"], "password": seeded["student_password"]}
        ),
        headers={"Content-Type": "application/json"},
    )

    upload_response = test_client.post(
        f"/assignment/{seeded['assignment_id']}/submission",
        data={"submission": (io.BytesIO(b"ungrouped"), "ungrouped.txt")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 400
    assert upload_response.json["msg"] == "You must be assigned to a group before submitting"


def test_teacher_can_download_student_submission(
    test_client,
    make_teacher,
    enroll_user_in_course,
):
    seeded = _seed_assignment_with_student(test_client, make_teacher, enroll_user_in_course)

    test_client.post(
        "/auth/login",
        data=json.dumps(
            {"email": seeded["student_email"], "password": seeded["student_password"]}
        ),
        headers={"Content-Type": "application/json"},
    )
    upload_response = test_client.post(
        f"/assignment/{seeded['assignment_id']}/submission",
        data={"submission": (io.BytesIO(b"teacher-download-bytes"), "deliverable.tar")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    test_client.post(
        "/auth/login",
        data=json.dumps(
            {"email": seeded["teacher_email"], "password": seeded["teacher_password"]}
        ),
        headers={"Content-Type": "application/json"},
    )
    download_response = test_client.get(
        f"/assignment/{seeded['assignment_id']}/submission/{seeded['student_id']}/download"
    )
    assert download_response.status_code == 200
    assert download_response.data == b"teacher-download-bytes"


def test_student_cannot_use_teacher_submission_download_endpoint(
    test_client,
    make_teacher,
    enroll_user_in_course,
):
    seeded = _seed_assignment_with_student(test_client, make_teacher, enroll_user_in_course)

    test_client.post(
        "/auth/login",
        data=json.dumps(
            {"email": seeded["student_email"], "password": seeded["student_password"]}
        ),
        headers={"Content-Type": "application/json"},
    )
    response = test_client.get(
        f"/assignment/{seeded['assignment_id']}/submission/{seeded['student_id']}/download"
    )
    assert response.status_code == 403
    assert response.json["msg"] == "Insufficient permissions"
