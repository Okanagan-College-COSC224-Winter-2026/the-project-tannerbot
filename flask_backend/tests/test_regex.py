"""
Tests for user registration input validation
"""

import json
import pytest

# ------------------------
# REGISTER TESTS
# ------------------------

@pytest.mark.parametrize(
    "data",
    [
        {},  # completely empty
        {"name": "", "email": "", "password": ""},  # empty strings
        {"name": "Alice"},  # missing email/password
        {"email": "alice@example.com"},  # missing name/password
        {"password": "Password123!"},  # missing name/email
    ],
)
def test_register_missing_fields(test_client, data):
    """Should return validation error for missing fields"""
    response = test_client.post(
        "/auth/register",
        data=json.dumps(data),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    # Marshmallow returns generic 'Validation error'
    assert response.json["msg"] == "Validation error"


def test_register_invalid_email(test_client):
    """Should fail for invalid email formats"""
    data = {"name": "Alice", "email": "not-an-email", "password": "Password123!"}
    response = test_client.post(
        "/auth/register",
        data=json.dumps(data),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "Validation error"


@pytest.mark.parametrize(
    "password",
    [
        "short1!",  # too short
        "nocaps123!",  # no uppercase
        "NOLOWER123!",  # no lowercase
        "NoNumber!",  # no number
        "NoSpecial1",  # no special character
    ],
)
def test_register_invalid_passwords(test_client, password):
    """Should fail for passwords not meeting strength requirements"""
    data = {"name": "Alice", "email": "alice@example.com", "password": password}
    response = test_client.post(
        "/auth/register",
        data=json.dumps(data),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "Validation error"