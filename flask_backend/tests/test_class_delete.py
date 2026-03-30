"""Tests for class deletion endpoint."""

import json

from api.models import User
from api.models.db import db as _db


def test_teacher_can_delete_own_class(test_client):
    """Teacher can delete a class they own."""
    teacher = User(
        name="teacheruser",
        email="teacher@example.com",
        hash_pass="teacher",
        role="teacher",
    )
    _db.session.add(teacher)
    _db.session.commit()

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    create_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Delete Me 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = create_response.json["class"]["id"]

    delete_response = test_client.delete(
        f"/class/{class_id}",
        headers={"Content-Type": "application/json"},
    )

    assert delete_response.status_code == 200
    assert delete_response.json["msg"] == "Class deleted"


def test_admin_can_delete_any_class(test_client, make_admin):
    """Admin can delete a class owned by a teacher."""
    teacher = User(
        name="teacheruser",
        email="teacher@example.com",
        hash_pass="teacher",
        role="teacher",
    )
    _db.session.add(teacher)
    _db.session.commit()

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    create_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Admin Delete 101"}),
        headers={"Content-Type": "application/json"},
    )
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
    teacher_one = User(
        name="teacherone",
        email="teacher1@example.com",
        hash_pass="teacher",
        role="teacher",
    )
    teacher_two = User(
        name="teachertwo",
        email="teacher2@example.com",
        hash_pass="teacher",
        role="teacher",
    )
    _db.session.add(teacher_one)
    _db.session.add(teacher_two)
    _db.session.commit()

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher1@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    create_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Protected 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = create_response.json["class"]["id"]

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher2@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    delete_response = test_client.delete(
        f"/class/{class_id}",
        headers={"Content-Type": "application/json"},
    )

    assert delete_response.status_code == 403
    assert delete_response.json["msg"] == "Unauthorized: You are not the teacher of this class"


def test_cannot_delete_nonexistent_class(test_client):
    """Deleting a missing class returns 404."""
    teacher = User(
        name="teacheruser",
        email="teacher@example.com",
        hash_pass="teacher",
        role="teacher",
    )
    _db.session.add(teacher)
    _db.session.commit()

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
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
