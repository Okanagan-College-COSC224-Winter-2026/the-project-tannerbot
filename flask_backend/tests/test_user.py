"""
Tests for user account management endpoints.
"""

import json


def test_delete_own_user(test_client):
    """
    GIVEN a logged-in user
    WHEN DELETE /user/<own_id> is called
    THEN the user should be deleted
    """
    # Register and login
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
    # Cookie is automatically stored in test_client

    # Get current user to get ID
    current_user_response = test_client.get("/user/")
    user_id = current_user_response.json["id"]

    # Delete user
    response = test_client.delete(f"/user/{user_id}")

    assert response.status_code == 200
    assert response.json["msg"] == "User deleted successfully"

    # Verify user is deleted by trying to get info
    verify_response = test_client.get("/user/")
    assert verify_response.status_code == 404


def test_change_password_success(test_client):
    """
    GIVEN a logged-in user with a known password
    WHEN PATCH /user/password is called with correct current_password and valid new_password
    THEN password is updated, old password no longer works, and new password works
    """
    email = "password_user@example.com"
    old_password = "Password123!"
    new_password = "NewPass456!"

    # Register and login
    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "password-user", "password": old_password, "email": email}),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": old_password}),
        headers={"Content-Type": "application/json"},
    )

    # Change password while authenticated
    change_response = test_client.patch(
        "/user/password",
        data=json.dumps({"current_password": old_password, "new_password": new_password}),
        headers={"Content-Type": "application/json"},
    )

    assert change_response.status_code == 200
    assert change_response.json["msg"] == "Password updated successfully"

    # Logout and verify old password fails
    test_client.post("/auth/logout")
    old_login_response = test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": old_password}),
        headers={"Content-Type": "application/json"},
    )
    assert old_login_response.status_code == 401
    assert old_login_response.json["msg"] == "Bad email or password"

    # Verify new password succeeds
    new_login_response = test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": new_password}),
        headers={"Content-Type": "application/json"},
    )
    assert new_login_response.status_code == 200
    assert new_login_response.json["name"] == "password-user"


def test_change_password_rejects_weak_password(test_client):
    """
    GIVEN a logged-in user
    WHEN PATCH /user/password is called with a weak new password
    THEN the request is rejected with a validation message
    """
    email = "weak_password_user@example.com"
    old_password = "Password123!"

    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "weak-password-user", "password": old_password, "email": email}),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": email, "password": old_password}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.patch(
        "/user/password",
        data=json.dumps({"current_password": old_password, "new_password": "weakpass"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert "uppercase" in response.json["msg"].lower()


def test_admin_cannot_delete_own_account_via_user_endpoint(test_client, make_admin):
    """
    GIVEN a logged-in admin user
    WHEN DELETE /user/<own_id> is called
    THEN the request is rejected
    """
    make_admin(email="selfdelete-admin@example.com", password="Admin123!", name="Self Delete Admin")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "selfdelete-admin@example.com", "password": "Admin123!"}),
        headers={"Content-Type": "application/json"},
    )

    current_user_response = test_client.get("/user/")
    user_id = current_user_response.json["id"]

    response = test_client.delete(f"/user/{user_id}")

    assert response.status_code == 400
    assert response.json["msg"] == "Cannot delete your own admin account"
