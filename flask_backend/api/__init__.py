import functools
import os
from datetime import timedelta

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from .cli import init_app
from .controllers import (
    admin_controller,
    assignment_attachment_controller,
    assignment_controller,
    assignment_grouping_controller,
    auth_controller,
    class_controller,
    class_enrollment_controller,
    course_search_controller,
    fake_api_controller,
    practice_tanner_controller,
    profile_picture_controller,
    review_controller,
    rubric_controller,
    submission_controller,
    user_controller,
)
from .models.db import db, ma
from .startup_migrations import (
    ensure_assignment_grouping_schema_for_sqlite,
    ensure_profile_picture_columns_for_sqlite,
    ensure_rubric_schema_for_sqlite,
    ensure_review_schema_for_sqlite,
)


def create_app(test_config=None):
    """Create and configure the Flask application"""
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # Determine if we're in production based on FLASK_ENV or explicit PRODUCTION flag
    is_production = (
        os.environ.get("FLASK_ENV") == "production"
        or os.environ.get("PRODUCTION", "false").lower() == "true"
    )

    # Use an explicit access-token lifetime to avoid Flask-JWT-Extended's 15-minute
    # default causing unexpected session expiration during normal app usage.
    access_token_expires_seconds = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", "3600"))

    # Validate required secrets in production
    if is_production:
        required_secrets = ["SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_URL"]
        missing = [key for key in required_secrets if not os.environ.get(key)]
        if missing:
            raise RuntimeError(
                f"Production mode requires these environment variables: {', '.join(missing)}"
            )

    # Default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        # A local sqlite database stored in the instance folder for development
        # For production, set the DATABASE_URL environment variable to the database URI
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "app.sqlite")
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret"),
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(seconds=access_token_expires_seconds),
        # JWT Cookie settings - secure defaults for production, permissive for development
        JWT_TOKEN_LOCATION=["cookies"],
        JWT_COOKIE_SECURE=is_production,  # True in production (HTTPS required)
        JWT_COOKIE_CSRF_PROTECT=is_production,  # True in production for CSRF protection
        JWT_COOKIE_SAMESITE=(
            "Strict" if is_production else "Lax"
        ),  # Strict in production for maximum security
        JWT_ACCESS_COOKIE_PATH="/",
        JWT_COOKIE_DOMAIN=os.environ.get("JWT_COOKIE_DOMAIN", None),
        MAX_SUBMISSION_FILE_SIZE_BYTES=int(
            os.environ.get("MAX_SUBMISSION_FILE_SIZE_BYTES", str(10 * 1024 * 1024))
        ),
        MAX_ASSIGNMENT_ATTACHMENT_SIZE_BYTES=int(
            os.environ.get("MAX_ASSIGNMENT_ATTACHMENT_SIZE_BYTES", str(10 * 1024 * 1024))
        ),
        RATE_LIMIT_TRUST_PROXY_HEADERS=(
            os.environ.get("RATE_LIMIT_TRUST_PROXY_HEADERS", "false").lower() == "true"
        ),
        LOGIN_ATTEMPT_WINDOW_SECONDS=int(os.environ.get("LOGIN_ATTEMPT_WINDOW_SECONDS", "300")),
        LOGIN_ATTEMPT_MAX_FAILURES=int(os.environ.get("LOGIN_ATTEMPT_MAX_FAILURES", "10")),
        LOGIN_LOCKOUT_SECONDS=int(os.environ.get("LOGIN_LOCKOUT_SECONDS", "120")),
        REGISTER_ATTEMPT_WINDOW_SECONDS=int(os.environ.get("REGISTER_ATTEMPT_WINDOW_SECONDS", "300")),
        REGISTER_ATTEMPT_MAX_ATTEMPTS=int(os.environ.get("REGISTER_ATTEMPT_MAX_ATTEMPTS", "10")),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    ensure_profile_picture_columns_for_sqlite(app.config["SQLALCHEMY_DATABASE_URI"])
    ensure_assignment_grouping_schema_for_sqlite(app.config["SQLALCHEMY_DATABASE_URI"])
    ensure_review_schema_for_sqlite(app.config["SQLALCHEMY_DATABASE_URI"])
    ensure_rubric_schema_for_sqlite(app.config["SQLALCHEMY_DATABASE_URI"])

    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)

    jwt = JWTManager()
    jwt.init_app(app)

    # Configure CORS to allow credentials (cookies)
    # In production, configure allowed origins via CORS_ORIGINS env var (comma-separated)
    cors_origins = (
        os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
        if os.environ.get("CORS_ORIGINS")
        else ["http://localhost:3000", "http://localhost:5173"]
    )
    CORS(
        app,
        origins=cors_origins,
        supports_credentials=True,
        allow_headers=["Content-Type", "X-CSRF-TOKEN"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    # a simple page that says hello
    @app.route("/hello")
    def hello():
        return {"message": "Hello, World!"}

    # Initialize CLI commands
    init_app(app)

    # Register blueprints
    app.register_blueprint(auth_controller.bp)
    app.register_blueprint(user_controller.bp)
    app.register_blueprint(profile_picture_controller.bp)
    app.register_blueprint(admin_controller.bp)
    app.register_blueprint(class_controller.bp)
    app.register_blueprint(class_enrollment_controller.bp)
    app.register_blueprint(course_search_controller.bp)
    app.register_blueprint(assignment_controller.bp)
    app.register_blueprint(assignment_grouping_controller.bp)
    app.register_blueprint(review_controller.bp)
    app.register_blueprint(rubric_controller.bp)
    app.register_blueprint(assignment_attachment_controller.bp)
    app.register_blueprint(submission_controller.bp)
    app.register_blueprint(fake_api_controller.fake)
    app.register_blueprint(practice_tanner_controller.practice)

    return app