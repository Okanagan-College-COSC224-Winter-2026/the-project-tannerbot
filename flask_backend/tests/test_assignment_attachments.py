"""
Tests for assignment attachment upload/list/download behavior.
"""

import datetime
import io
import json
import os


def test_teacher_can_create_assignment_with_multipart_without_attachments(test_client, make_admin):
    """Ensure multipart form submissions still create assignments successfully."""
    make_admin(email="admin@example.com", password="admin", name="adminuser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "admin@example.com", "password": "admin"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "History 201"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    response = test_client.post(
        "/assignment/create_assignment",
        data={
            "courseID": str(class_id),
            "name": "Essay 2",
            "rubric": "Clarity",
            "due_date": datetime.datetime(2027, 1, 10, 12, 0, 0).isoformat(),
            "start_date": datetime.datetime(2027, 1, 1, 12, 0, 0).isoformat(),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    assert response.json["assignment"]["name"] == "Essay 2"
    assert response.json["attachments"] == []

# This test verifies that a teacher can create an assignment with a file attachment
def test_teacher_can_create_assignment_with_attachment(test_client, make_admin):
    """Ensure assignment creation supports optional file attachments."""
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "CompSci 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    response = test_client.post(
        "/assignment/create_assignment",
        data={
            "courseID": str(class_id),
            "name": "Project Spec",
            "rubric": "Completeness",
            "attachments": (io.BytesIO(b"file-contents"), "spec.txt"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    assert len(response.json["attachments"]) == 1
    assert response.json["attachments"][0]["original_name"] == "spec.txt"

    assignment_id = response.json["assignment"]["id"]
    stored_name = response.json["attachments"][0]["stored_name"]
    expected_path = os.path.join(
        test_client.application.instance_path,
        "assignment_uploads",
        str(assignment_id),
        stored_name,
    )
    assert os.path.exists(expected_path)


def test_teacher_can_create_assignment_with_multiple_attachments(test_client, make_admin):
    """Ensure multiple files can be attached in a single assignment create request."""
    make_admin(email="teacher_multi@example.com", password="teacher", name="teacher_multi")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher_multi@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "CompSci Multi"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    response = test_client.post(
        "/assignment/create_assignment",
        data={
            "courseID": str(class_id),
            "name": "Multi File Assignment",
            "attachments": [
                (io.BytesIO(b"first-file"), "file1.txt"),
                (io.BytesIO(b"second-file"), "file2.txt"),
            ],
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    assert len(response.json["attachments"]) == 2
    original_names = {a["original_name"] for a in response.json["attachments"]}
    assert original_names == {"file1.txt", "file2.txt"}


def test_teacher_can_create_assignment_with_attachment_file_field_name(test_client, make_admin):
    """Support clients that submit a single file under field name 'file'."""
    make_admin(email="teacher2@example.com", password="teacher", name="teacheruser2")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher2@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "CompSci 102"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    response = test_client.post(
        "/assignment/create_assignment",
        data={
            "courseID": str(class_id),
            "name": "Project Plan",
            "file": (io.BytesIO(b"plan-contents"), "plan.txt"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    assert len(response.json["attachments"]) == 1
    assert response.json["attachments"][0]["original_name"] == "plan.txt"


def test_teacher_can_download_assignment_attachment(test_client, make_admin):
    make_admin(email="teacher4@example.com", password="teacher", name="teacheruser4")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher4@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "CompSci 104"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    create_response = test_client.post(
        "/assignment/create_assignment",
        data={
            "courseID": str(class_id),
            "name": "Download Test",
            "attachments": (io.BytesIO(b"download-body"), "download.txt"),
        },
        content_type="multipart/form-data",
    )

    assignment_id = create_response.json["assignment"]["id"]
    stored_name = create_response.json["attachments"][0]["stored_name"]

    download_response = test_client.get(
        f"/assignment/{assignment_id}/attachment/{stored_name}"
    )

    assert download_response.status_code == 200
    assert download_response.data == b"download-body"
