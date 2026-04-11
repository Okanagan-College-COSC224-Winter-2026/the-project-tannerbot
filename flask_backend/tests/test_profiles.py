"""
Tests for profile-related user endpoints.
"""

import io
import json

from werkzeug.security import generate_password_hash

from api.models import User


def test_get_current_user(test_client):
    """
    GIVEN a logged-in user
    WHEN GET /user/ is called
    THEN the current user's information should be returned
    """
    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "testuser", "password": "Password123!", "email": "test@example.com"}),
        headers={"Content-Type": "application/json"},
    )

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "test@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.get("/user/")

    assert response.status_code == 200
    assert response.json["name"] == "testuser"
    assert response.json["email"] == "test@example.com"
    assert response.json["id"] is not None
    assert response.json["role"] == "student"
    assert "password" not in response.json


def test_get_current_user_unauthorized(test_client):
    """
    GIVEN no authentication token
    WHEN GET /user/ is called
    THEN it should return 401
    """
    response = test_client.get("/user/")
    assert response.status_code == 401


def test_update_current_user(test_client):
    """
    GIVEN a logged-in user
    WHEN PUT /user/ is called with updated information
    THEN the user's information should be updated
    """
    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "testuser", "password": "Password123!", "email": "test@example.com"}),
        headers={"Content-Type": "application/json"},
    )

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "test@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.put(
        "/user/", data=json.dumps({"name": "Updated"}), headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 200
    assert response.json["name"] == "Updated"


def test_student_can_update_own_description(test_client):
    """
    GIVEN a logged-in student
    WHEN PUT /user/ is called with a description
    THEN the student's description should be updated
    """
    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "student", "password": "Password123!", "email": "student@example.com"}),
        headers={"Content-Type": "application/json"},
    )

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.put(
        "/user/",
        data=json.dumps({"description": "I enjoy team projects and backend APIs."}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 200
    assert response.json["description"] == "I enjoy team projects and backend APIs."


def test_teacher_cannot_update_description(test_client, dbsession):
    """
    GIVEN a logged-in teacher
    WHEN PUT /user/ is called with a description
    THEN the request should be rejected
    """
    dbsession.add(
        User(
            name="Teacher User",
            email="teacher@example.com",
            hash_pass=generate_password_hash("Password123!"),
            role="teacher",
        )
    )
    dbsession.commit()

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.put(
        "/user/",
        data=json.dumps({"description": "This should not be allowed."}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 403
    assert response.json["msg"] == "Only students can edit profile descriptions"


def test_update_current_user_profile_picture(test_client):
    """
    GIVEN a logged-in user
    WHEN POST /user/profile-picture is called with an image upload
    THEN the user's profile picture should be stored and retrievable
    """
    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "testuser", "password": "Password123!", "email": "test@example.com"}),
        headers={"Content-Type": "application/json"},
    )

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "test@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    upload_response = test_client.post(
        "/user/profile-picture",
        data={"profile_picture": (io.BytesIO(b"fake-image-data"), "avatar.png")},
        content_type="multipart/form-data",
    )

    assert upload_response.status_code == 200
    assert upload_response.json["profile_picture_url"] == f"/user/{upload_response.json['id']}/profile-picture"

    picture_response = test_client.get(upload_response.json["profile_picture_url"])

    assert picture_response.status_code == 200
    assert picture_response.mimetype == "image/png"
    assert picture_response.data == b"fake-image-data"


def test_update_current_user_profile_picture_rejects_non_image(test_client):
    """
    GIVEN a logged-in user
    WHEN POST /user/profile-picture is called with a non-image file
    THEN the upload should be rejected
    """
    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "testuser", "password": "Password123!", "email": "test@example.com"}),
        headers={"Content-Type": "application/json"},
    )

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "test@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.post(
        "/user/profile-picture",
        data={"profile_picture": (io.BytesIO(b"plain-text"), "avatar.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.json["msg"] == "Profile picture must be a PNG, JPEG, GIF, or WebP image"


def test_delete_current_user_profile_picture(test_client):
    """
    GIVEN a logged-in user with a profile picture
    WHEN DELETE /user/profile-picture is called
    THEN the profile picture should be removed
    """
    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "testuser", "password": "Password123!", "email": "test@example.com"}),
        headers={"Content-Type": "application/json"},
    )

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "test@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    upload_response = test_client.post(
        "/user/profile-picture",
        data={"profile_picture": (io.BytesIO(b"fake-image-data"), "avatar.png")},
        content_type="multipart/form-data",
    )

    delete_response = test_client.delete("/user/profile-picture")

    assert delete_response.status_code == 200
    assert delete_response.json["profile_picture_url"] is None

    picture_response = test_client.get(upload_response.json["profile_picture_url"])
    assert picture_response.status_code == 404


def test_get_user_by_id(test_client):
    """
    GIVEN a logged-in user
    WHEN GET /user/<id> is called with their own ID
    THEN their information should be returned
    """
    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "testuser", "password": "Password123!", "email": "test@example.com"}),
        headers={"Content-Type": "application/json"},
    )

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "test@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    current_user_response = test_client.get("/user/")
    user_id = current_user_response.json["id"]

    response = test_client.get(f"/user/{user_id}")

    assert response.status_code == 200
    assert response.json["id"] == user_id
    assert response.json["name"] == "testuser"


def test_get_other_user_by_id_forbidden(test_client):
    """
    GIVEN two users, one logged in
    WHEN the logged-in user tries to access another user's information
    THEN it should return 403 (unless admin)
    """
    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "user1", "password": "Password123!", "email": "user1@example.com"}),
        headers={"Content-Type": "application/json"},
    )

    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "user2", "password": "Password123!", "email": "user2@example.com"}),
        headers={"Content-Type": "application/json"},
    )

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "user1@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.get("/user/2")

    assert response.status_code in [403, 404]
