"""
Tests for assignment description management (added after assignment creation).
"""

import datetime
import json

# This test verifies that a teacher can update assignment description after creating an assignment.
def test_teacher_can_update_assignment_description(test_client, make_admin):
    """Ensure assignment description updates through assignment edit endpoint."""
    make_admin(email="teacher-description-edit@example.com", password="teacher", name="teacher-description-edit")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher-description-edit@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "CompSci 200"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    create_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": str(class_id),
                "name": "Description Edit Assignment",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = create_response.json["assignment"]["id"]

    edit_response = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps(
            {
                "description": "Updated assignment description from manage modal.",
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assert edit_response.status_code == 200
    assert edit_response.json["assignment"]["description"] == "Updated assignment description from manage modal."

# This test verifies that a teacher can add a description to an assignment that was created without one.
def test_teacher_can_add_description_to_existing_assignment(test_client, make_admin):
    """Ensure assignment description can be added to an assignment that was created without one."""
    make_admin(email="teacher-add-desc@example.com", password="teacher", name="teacher-add-desc")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher-add-desc@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "CompSci 201"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    create_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": str(class_id),
                "name": "Assignment Without Description",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = create_response.json["assignment"]["id"]

    # Add description after creation
    edit_response = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps(
            {
                "description": "Description added after creation.",
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assert edit_response.status_code == 200
    assert edit_response.json["assignment"]["description"] == "Description added after creation."
