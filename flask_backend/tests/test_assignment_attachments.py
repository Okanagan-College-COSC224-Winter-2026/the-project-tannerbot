"""
Tests for assignment attachment upload/list/download behavior.
"""

import datetime
import io
import json
import os

from api.models import AssignmentAttachment


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
    unexpected_path = os.path.join(
        test_client.application.instance_path,
        "assignment_uploads",
        str(assignment_id),
        stored_name,
    )
    attachment = AssignmentAttachment.get_by_assignment_and_stored_name(assignment_id, stored_name)
    assert attachment is not None
    assert attachment.original_name == "spec.txt"
    assert attachment.content == b"file-contents"
    assert not os.path.exists(unexpected_path)


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

    assignment_id = response.json["assignment"]["id"]
    attachments = AssignmentAttachment.get_for_assignment(assignment_id)
    assert len(attachments) == 2


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


def test_teacher_can_add_attachment_after_assignment_creation(test_client, make_admin):
    make_admin(email="teacher5@example.com", password="teacher", name="teacheruser5")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher5@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "CompSci 105"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    create_response = test_client.post(
        "/assignment/create_assignment",
        data={
            "courseID": str(class_id),
            "name": "Post Create Upload",
            "rubric": "Completeness",
            "due_date": datetime.datetime(2028, 1, 10, 12, 0, 0).isoformat(),
            "start_date": datetime.datetime(2028, 1, 1, 12, 0, 0).isoformat(),
        },
        content_type="multipart/form-data",
    )
    assignment_id = create_response.json["assignment"]["id"]

    add_response = test_client.post(
        f"/assignment/{assignment_id}/attachment",
        data={"attachments": (io.BytesIO(b"post-create-content"), "added-later.txt")},
        content_type="multipart/form-data",
    )

    assert add_response.status_code == 200
    assert add_response.json["msg"] == "Attachments updated"
    assert len(add_response.json["added_attachments"]) == 1
    assert add_response.json["added_attachments"][0]["original_name"] == "added-later.txt"


def test_teacher_can_delete_attachment_after_assignment_creation(test_client, make_admin):
    make_admin(email="teacher6@example.com", password="teacher", name="teacheruser6")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher6@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "CompSci 106"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    create_response = test_client.post(
        "/assignment/create_assignment",
        data={
            "courseID": str(class_id),
            "name": "Delete Attachment",
            "attachments": (io.BytesIO(b"to-delete"), "delete-me.txt"),
        },
        content_type="multipart/form-data",
    )
    assignment_id = create_response.json["assignment"]["id"]
    stored_name = create_response.json["attachments"][0]["stored_name"]

    delete_response = test_client.delete(
        f"/assignment/{assignment_id}/attachment/{stored_name}"
    )

    assert delete_response.status_code == 200
    assert delete_response.json["msg"] == "Attachment deleted"
    assert AssignmentAttachment.get_by_assignment_and_stored_name(assignment_id, stored_name) is None


def test_teacher_cannot_edit_attachments_after_due_date(test_client, make_admin):
    make_admin(email="teacher7@example.com", password="teacher", name="teacheruser7")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher7@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "CompSci 107"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    create_response = test_client.post(
        "/assignment/create_assignment",
        data={
            "courseID": str(class_id),
            "name": "Past Due Assignment",
            "due_date": datetime.datetime(2020, 1, 1, 12, 0, 0).isoformat(),
        },
        content_type="multipart/form-data",
    )
    assignment_id = create_response.json["assignment"]["id"]

    add_response = test_client.post(
        f"/assignment/{assignment_id}/attachment",
        data={"attachments": (io.BytesIO(b"late-upload"), "late.txt")},
        content_type="multipart/form-data",
    )

    assert add_response.status_code == 400
    assert add_response.json["msg"] == "Assignment cannot be modified after its due date"
