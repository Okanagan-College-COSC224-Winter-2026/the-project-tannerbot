"""Tests for class deletion endpoint."""

import json

from api.models import User


def _register_teacher(test_client, email, name, password="Password123!"):
    """Create a valid user via auth/register, then promote to teacher role."""
    register_response = test_client.post(
        "/auth/register",
        data=json.dumps({"name": name, "email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )
    assert register_response.status_code == 201

    user = User.get_by_email(email)
    assert user is not None
    user.role = "teacher"
    user.update()

    login_response = test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": password}),
        headers={"Content-Type": "application/json"},
    )
    assert login_response.status_code == 200


def test_teacher_can_delete_own_class(test_client):
    """Teacher can delete a class they own."""
    _register_teacher(test_client, email="teacher@example.com", name="teacheruser")

    create_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Delete Me 101"}),
        headers={"Content-Type": "application/json"},
    )
    assert create_response.status_code == 201
    class_id = create_response.json["class"]["id"]

    delete_response = test_client.delete(
        f"/class/{class_id}",
        headers={"Content-Type": "application/json"},
    )

    assert delete_response.status_code == 200
    assert delete_response.json["msg"] == "Class deleted"


def test_admin_can_delete_any_class(test_client, make_admin):
    """Admin can delete a class owned by a teacher."""
    _register_teacher(test_client, email="teacher@example.com", name="teacheruser")

    create_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Admin Delete 101"}),
        headers={"Content-Type": "application/json"},
    )
    assert create_response.status_code == 201
    class_id = create_response.json["class"]["id"]

    make_admin(email="admin@example.com", password="admin", name="adminuser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "admin@example.com", "password": "admin"}),
        headers={"Content-Type": "application/json"},
    )

    delete_response = test_client.delete(
        f"/class/{class_id}",
        headers={"Content-Type": "application/json"},
    )

    assert delete_response.status_code == 200
    assert delete_response.json["msg"] == "Class deleted"


def test_teacher_cannot_delete_other_teachers_class(test_client):
    """Teacher cannot delete a class they do not own."""
    _register_teacher(test_client, email="teacher1@example.com", name="teacherone")

    create_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Protected 101"}),
        headers={"Content-Type": "application/json"},
    )
    assert create_response.status_code == 201
    class_id = create_response.json["class"]["id"]

    _register_teacher(test_client, email="teacher2@example.com", name="teachertwo")

    delete_response = test_client.delete(
        f"/class/{class_id}",
        headers={"Content-Type": "application/json"},
    )

    assert delete_response.status_code == 403
    assert delete_response.json["msg"] == "Unauthorized: You are not the teacher of this class"


def test_cannot_delete_nonexistent_class(test_client):
    """Deleting a missing class returns 404."""
    _register_teacher(test_client, email="teacher@example.com", name="teacheruser")

    delete_response = test_client.delete(
        "/class/99999",
        headers={"Content-Type": "application/json"},
    )

    assert delete_response.status_code == 404
    assert delete_response.json["msg"] == "Class not found"


def test_unauthenticated_user_cannot_delete_class(test_client):
    """Unauthenticated users cannot delete classes."""
    delete_response = test_client.delete(
        "/class/1",
        headers={"Content-Type": "application/json"},
    )
    assert delete_response.status_code == 401
