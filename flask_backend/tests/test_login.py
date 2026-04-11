import json
import os

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def test_register(test_client):
    """
    GIVEN POST /auth/register
    WHEN a username and password are provided
    THEN a new user should be created
    """
    response = test_client.post(
        "/auth/register",
        data=json.dumps({"name": "testuser", "password": "Password123!", "email": "test@example.com"}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 201
    assert response.json["msg"] == "User registered successfully"


def test_register_duplicate(test_client):
    """
    GIVEN POST /auth/register
    WHEN registering a user that already exists
    THEN it should return an error
    """
    # Create first user
    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "testuser", "password": "Password123!", "email": "test@example.com"}),
        headers={"Content-Type": "application/json"},
    )

    # Try to create duplicate
    response = test_client.post(
        "/auth/register",
        data=json.dumps({"name": "testuser", "password": "Password123!", "email": "test@example.com"}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert "already registered" in response.json["msg"]


def test_login(test_client):
    """
    GIVEN POST /auth/login
    WHEN valid credentials are provided
    THEN a JWT cookie should be set and user info returned
    """
    # First register a user
    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "example", "password": "Password123!", "email": "example@example.com"}),
        headers={"Content-Type": "application/json"},
    )

    # Then login
    token_request = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "example@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    assert token_request.status_code == 200
    # Should NOT return access_token in JSON anymore
    assert "access_token" not in token_request.json
    # Should return user info
    assert token_request.json["role"] == "student"
    assert token_request.json["name"] == "example"
    # Should set a cookie
    assert "Set-Cookie" in token_request.headers


def test_login_invalid_credentials(test_client):
    """
    GIVEN POST /auth/login
    WHEN invalid credentials are provided
    THEN it should return 401
    """
    response = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "nonexistent@example.com", "password": "wrong"}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 401
    assert response.json["msg"] == "Bad email or password"


def test_logout(test_client):
    """
    GIVEN POST /auth/logout with valid JWT cookie
    WHEN the logout endpoint is called
    THEN it should return success and clear the cookie
    """
    # Register and login first
    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "example", "password": "Password123!", "email": "example@example.com"}),
        headers={"Content-Type": "application/json"},
    )

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "example@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    # Cookie is automatically stored in test_client

    # Logout
    response = test_client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json["msg"] == "Successfully logged out"
    # Should clear the cookie
    assert "Set-Cookie" in response.headers


def test_login_rate_limit_after_repeated_failures(test_client):
    """Repeated bad passwords should trigger temporary lockout."""
    test_client.post(
        "/auth/register",
        data=json.dumps(
            {"name": "ratelimit-user", "password": "Password123!", "email": "ratelimit@example.com"}
        ),
        headers={"Content-Type": "application/json"},
    )

    # First four failures stay as invalid credentials.
    for _ in range(4):
        response = test_client.post(
            "/auth/login",
            data=json.dumps({"email": "ratelimit@example.com", "password": "WrongPassword1!"}),
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 401
        assert response.json["msg"] == "Bad email or password"

    # Fifth failure triggers lockout.
    blocked_response = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "ratelimit@example.com", "password": "WrongPassword1!"}),
        headers={"Content-Type": "application/json"},
    )
    assert blocked_response.status_code == 429
    assert "Too many failed login attempts" in blocked_response.json["msg"]
    assert blocked_response.json["retry_after_seconds"] > 0

    # Correct password is still blocked during lockout window.
    locked_response = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "ratelimit@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    assert locked_response.status_code == 429


def test_register_rate_limit_after_repeated_attempts(test_client):
    test_client.application.config["REGISTER_ATTEMPT_MAX_ATTEMPTS"] = 3
    test_client.application.config["REGISTER_ATTEMPT_WINDOW_SECONDS"] = 300

    for idx in range(3):
        response = test_client.post(
            "/auth/register",
            data=json.dumps(
                {
                    "name": f"testuser-{idx}",
                    "password": "Password123!",
                    "email": f"register-limit-{idx}@example.com",
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 201

    blocked = test_client.post(
        "/auth/register",
        data=json.dumps(
            {
                "name": "blocked-user",
                "password": "Password123!",
                "email": "register-limit-blocked@example.com",
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assert blocked.status_code == 429
    assert "Too many registration attempts" in blocked.json["msg"]
    assert blocked.json["retry_after_seconds"] > 0


def test_login_rate_limit_ignores_spoofed_forwarded_for_by_default(test_client):
    test_client.application.config["LOGIN_ATTEMPT_MAX_FAILURES"] = 3
    test_client.application.config["LOGIN_ATTEMPT_WINDOW_SECONDS"] = 300
    test_client.application.config["LOGIN_LOCKOUT_SECONDS"] = 300
    test_client.application.config["RATE_LIMIT_TRUST_PROXY_HEADERS"] = False

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {"name": "spoof-user", "password": "Password123!", "email": "spoof@example.com"}
        ),
        headers={"Content-Type": "application/json"},
    )

    response1 = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "spoof@example.com", "password": "WrongPassword1!"}),
        headers={"Content-Type": "application/json", "X-Forwarded-For": "198.51.100.10"},
    )
    response2 = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "spoof@example.com", "password": "WrongPassword1!"}),
        headers={"Content-Type": "application/json", "X-Forwarded-For": "198.51.100.11"},
    )
    response3 = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "spoof@example.com", "password": "WrongPassword1!"}),
        headers={"Content-Type": "application/json", "X-Forwarded-For": "198.51.100.12"},
    )

    assert response1.status_code == 401
    assert response2.status_code == 401
    assert response3.status_code == 429
