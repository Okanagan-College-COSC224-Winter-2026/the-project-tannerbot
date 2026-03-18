"""Enable student profile description support for an existing database.

Run from flask_backend:
    py enable_profile_description_support.py

This script is idempotent. It adds the `description` column to the `User`
table only if it does not already exist.
"""

from sqlalchemy import inspect, text

from api import create_app
from api.models.db import db


COLUMN_NAME = "description"


def _column_exists() -> bool:
    inspector = inspect(db.engine)
    if "User" not in inspector.get_table_names():
        raise SystemExit(
            "User table not found. Run 'flask init_db' first if the database has not been initialized."
        )

    existing_columns = {column["name"] for column in inspector.get_columns("User")}
    return COLUMN_NAME in existing_columns


def _add_description_column() -> None:
    # Double quotes around User work across SQLite/PostgreSQL for this table name.
    statement = text('ALTER TABLE "User" ADD COLUMN description TEXT')
    with db.engine.begin() as connection:
        connection.execute(statement)


def main() -> None:
    app = create_app()

    with app.app_context():
        if _column_exists():
            print("Profile description support is already enabled. No changes were needed.")
            return

        _add_description_column()

        if _column_exists():
            print("Profile description support enabled.")
            print("Added column: User.description")
        else:
            raise SystemExit("Migration did not apply successfully. Please inspect your database state.")

    print("Next step: restart the Flask backend if it is already running.")


if __name__ == "__main__":
    main()
