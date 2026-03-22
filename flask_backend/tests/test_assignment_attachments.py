"""
Tests for assignment attachment upload/list/download behavior.
"""

import datetime
import io
import json

from api.models import AssignmentAttachment

# This test verifies that a teacher can create an assignment without attachments.
def test_teacher_can_create_assignment_without_attachments(test_client, make_admin):
    """Ensure assignment creation no longer depends on attachment uploads."""
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
        data=json.dumps({
            "courseID": str(class_id),
            "name": "Essay 2",
            "rubric": "Clarity",
            "due_date": datetime.datetime(2027, 1, 10, 12, 0, 0).isoformat(),
            "start_date": datetime.datetime(2027, 1, 1, 12, 0, 0).isoformat(),
        }),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 201
    assert response.json["assignment"]["name"] == "Essay 2"
    assert response.json["attachments"] == []


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
        data=json.dumps({
            "courseID": str(class_id),
            "name": "Download Test",
        }),
        headers={"Content-Type": "application/json"},
    )

    assignment_id = create_response.json["assignment"]["id"]

    add_response = test_client.post(
        f"/assignment/{assignment_id}/attachment",
        data={"attachments": (io.BytesIO(b"download-body"), "download.txt")},
        content_type="multipart/form-data",
    )
    stored_name = add_response.json["added_attachments"][0]["stored_name"]

    download_response = test_client.get(
        f"/assignment/{assignment_id}/attachment/{stored_name}"
    )

    assert download_response.status_code == 200
    assert download_response.data == b"download-body"

# This test verifies that a teacher can delete an attachment after creating an assignment with it
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

# This test verifies that a teacher can delete an attachment after the assignment has been created.
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
        data=json.dumps({
            "courseID": str(class_id),
            "name": "Delete Attachment",
        }),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = create_response.json["assignment"]["id"]

    add_response = test_client.post(
        f"/assignment/{assignment_id}/attachment",
        data={"attachments": (io.BytesIO(b"to-delete"), "delete-me.txt")},
        content_type="multipart/form-data",
    )
    stored_name = add_response.json["added_attachments"][0]["stored_name"]

    delete_response = test_client.delete(
        f"/assignment/{assignment_id}/attachment/{stored_name}"
    )

    assert delete_response.status_code == 200
    assert delete_response.json["msg"] == "Attachment deleted"
    assert AssignmentAttachment.get_by_assignment_and_stored_name(assignment_id, stored_name) is None

# This test verifies that a teacher cannot add attachments after the assignment's due date has passed
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
        data=json.dumps({
            "courseID": str(class_id),
            "name": "Past Due Assignment",
            "due_date": datetime.datetime(2020, 1, 1, 12, 0, 0).isoformat(),
        }),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = create_response.json["assignment"]["id"]

    add_response = test_client.post(
        f"/assignment/{assignment_id}/attachment",
        data={"attachments": (io.BytesIO(b"late-upload"), "late.txt")},
        content_type="multipart/form-data",
    )

    assert add_response.status_code == 400
    assert add_response.json["msg"] == "Assignment cannot be modified after its due date"
