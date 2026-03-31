import functools
import threading
import time

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)
from marshmallow import ValidationError
from werkzeug.security import check_password_hash, generate_password_hash

from ..models import User, UserLoginSchema, UserRegistrationSchema, UserSchema

bp = Blueprint("auth", __name__, url_prefix="/auth")

LOGIN_ATTEMPT_WINDOW_SECONDS = 5 * 60
LOGIN_ATTEMPT_MAX_FAILURES = 5
LOGIN_LOCKOUT_SECONDS = 10 * 60
REGISTER_ATTEMPT_WINDOW_SECONDS = 5 * 60
REGISTER_ATTEMPT_MAX_ATTEMPTS = 10

_failed_login_attempts = {}
_lockout_until = {}
_register_attempts = {}
_login_attempt_lock = threading.Lock()

# Create schema instances once (reusable)
registration_schema = UserRegistrationSchema()
login_schema = UserLoginSchema()
user_schema = UserSchema()


def _get_config_int(name, default_value):
    value = current_app.config.get(name, default_value)
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default_value)


def _get_rate_limit_client_ip():
    client_ip = request.remote_addr or "unknown"
    if not current_app.config.get("RATE_LIMIT_TRUST_PROXY_HEADERS", False):
        return client_ip

    # Only trusted deployments should enable this; otherwise a client can spoof it.
    forwarded_for = (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    return forwarded_for or client_ip


def _get_login_throttle_key(email):
    client_ip = _get_rate_limit_client_ip()
    normalized_email = (email or "").strip().lower()
    return f"{client_ip}:{normalized_email}"


def _get_register_throttle_key():
    return _get_rate_limit_client_ip()


def _prune_attempts(attempts, now, window_seconds):
    return [ts for ts in attempts if now - ts <= window_seconds]


def _get_lockout_remaining_seconds(key, now):
    locked_until = _lockout_until.get(key)
    if not locked_until:
        return 0

    remaining = int(locked_until - now)
    if remaining > 0:
        return remaining

    _lockout_until.pop(key, None)
    return 0


def _record_failed_login_attempt(key, now):
    window_seconds = _get_config_int("LOGIN_ATTEMPT_WINDOW_SECONDS", LOGIN_ATTEMPT_WINDOW_SECONDS)
    max_failures = _get_config_int("LOGIN_ATTEMPT_MAX_FAILURES", LOGIN_ATTEMPT_MAX_FAILURES)
    lockout_seconds = _get_config_int("LOGIN_LOCKOUT_SECONDS", LOGIN_LOCKOUT_SECONDS)

    attempts = _prune_attempts(_failed_login_attempts.get(key, []), now, window_seconds)
    attempts.append(now)
    _failed_login_attempts[key] = attempts

    if len(attempts) >= max_failures:
        _lockout_until[key] = now + lockout_seconds
        _failed_login_attempts.pop(key, None)
        return int(lockout_seconds)

    return 0


def _clear_login_failures(key):
    _failed_login_attempts.pop(key, None)
    _lockout_until.pop(key, None)


def _register_rate_limit_retry_after_seconds(key, now):
    window_seconds = _get_config_int("REGISTER_ATTEMPT_WINDOW_SECONDS", REGISTER_ATTEMPT_WINDOW_SECONDS)
    max_attempts = _get_config_int("REGISTER_ATTEMPT_MAX_ATTEMPTS", REGISTER_ATTEMPT_MAX_ATTEMPTS)

    attempts = _prune_attempts(_register_attempts.get(key, []), now, window_seconds)
    if len(attempts) >= max_attempts:
        _register_attempts[key] = attempts
        oldest_attempt = attempts[0]
        return max(1, int(window_seconds - (now - oldest_attempt)))

    attempts.append(now)
    _register_attempts[key] = attempts
    return 0


@bp.route("/register", methods=["POST"])
def register():
    """Register a new user account (student only - teachers/admins created by admins)"""
    now = time.time()
    throttle_key = _get_register_throttle_key()
    with _login_attempt_lock:
        retry_after = _register_rate_limit_retry_after_seconds(throttle_key, now)
    if retry_after > 0:
        return (
            jsonify(
                {
                    "msg": f"Too many registration attempts. Try again in {retry_after} seconds.",
                    "retry_after_seconds": retry_after,
                    "locked_until_unix": int(now + retry_after),
                }
            ),
            429,
        )

    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    # Validate input with Marshmallow
    try:
        data = registration_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"msg": "Validation error", "errors": err.messages}), 400

    # Check if user already exists
    existing_user = User.get_by_email(data["email"])
    if existing_user:
        return jsonify({"msg": f"User with email {data['email']} is already registered"}), 400

    # Create new user (always student role for public registration)
    new_user = User(
        name=data["name"],
        hash_pass=generate_password_hash(data["password"]),
        email=data["email"],
        role="student",  # Public registration only creates students
    )
    User.create_user(new_user)

    return jsonify({"msg": "User registered successfully"}), 201


@bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return JWT token in httponly cookie"""
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    # Validate input with Marshmallow
    try:
        data = login_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"msg": "Validation error", "errors": err.messages}), 400

    throttle_key = _get_login_throttle_key(data.get("email"))
    now = time.time()
    with _login_attempt_lock:
        retry_after = _get_lockout_remaining_seconds(throttle_key, now)
    if retry_after > 0:
        return (
            jsonify(
                {
                    "msg": f"Too many failed login attempts. Try again in {retry_after} seconds.",
                    "retry_after_seconds": retry_after,
                    "locked_until_unix": int(now + retry_after),
                }
            ),
            429,
        )

    # Verify credentials
    user = User.get_by_email(data["email"])
    if user is None or not check_password_hash(user.hash_pass, data["password"]):
        now = time.time()
        with _login_attempt_lock:
            lockout_seconds = _record_failed_login_attempt(throttle_key, now)
        if lockout_seconds > 0:
            return (
                jsonify(
                    {
                        "msg": f"Too many failed login attempts. Try again in {lockout_seconds} seconds.",
                        "retry_after_seconds": lockout_seconds,
                        "locked_until_unix": int(now + lockout_seconds),
                    }
                ),
                429,
            )
        return jsonify({"msg": "Bad email or password"}), 401

    with _login_attempt_lock:
        _clear_login_failures(throttle_key)

    # Generate access token and set as httponly cookie
    access_token = create_access_token(identity=data["email"])
    response = jsonify(user_schema.dump(user))
    set_access_cookies(response, access_token)
    return response, 200


@bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Logout endpoint - clears the JWT cookie
    """
    response = jsonify({"msg": "Successfully logged out"})
    unset_jwt_cookies(response)
    return response, 200


# JWT-based decorators for API protection
def jwt_role_required(*roles):
    """Decorator to require specific role(s) for JWT-protected endpoints

    Usage:
        @jwt_role_required('admin')  # Only admins
        @jwt_role_required('teacher', 'admin')  # Teachers or admins
        @jwt_role_required('student', 'teacher', 'admin')  # Any authenticated user
    """

    def decorator(view):
        @functools.wraps(view)
        @jwt_required()
        def wrapped_view(*args, **kwargs):
            current_email = get_jwt_identity()
            user = User.get_by_email(current_email)

            if not user:
                return jsonify({"msg": "User not found"}), 404

            # Check if user has one of the required roles
            if roles and not user.has_role(*roles):
                return jsonify({"msg": "Insufficient permissions"}), 403

            return view(*args, **kwargs)

        return wrapped_view

    return decorator


def jwt_admin_required(view):
    """Decorator to require admin role for JWT-protected endpoints"""
    return jwt_role_required("admin")(view)


def jwt_teacher_required(view):
    """Decorator to require teacher or admin role for JWT-protected endpoints"""
    return jwt_role_required("teacher", "admin")(view)
