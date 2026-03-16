"""Lightweight startup migrations for local SQLite development databases."""

from pathlib import Path
import sqlite3


PROFILE_PICTURE_COLUMN_STATEMENTS = {
    "profile_picture": "ALTER TABLE User ADD COLUMN profile_picture BLOB",
    "profile_picture_mime_type": (
        "ALTER TABLE User ADD COLUMN profile_picture_mime_type VARCHAR(128)"
    ),
}


def _sqlite_path_from_uri(database_uri: str) -> Path | None:
    if database_uri == "sqlite:///:memory:":
        return None

    prefix = "sqlite:///"
    if not database_uri.startswith(prefix):
        return None

    raw_path = database_uri[len(prefix) :]
    if not raw_path:
        return None

    return Path(raw_path)


def ensure_profile_picture_columns_for_sqlite(database_uri: str) -> list[str]:
    """Ensure legacy SQLite User tables contain the profile picture columns."""
    database_path = _sqlite_path_from_uri(database_uri)
    if database_path is None or not database_path.exists():
        return []

    connection = sqlite3.connect(database_path)
    try:
        cursor = connection.cursor()
        tables = {row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "User" not in tables:
            return []

        existing_columns = {row[1] for row in cursor.execute("PRAGMA table_info(User)")}
        added_columns = []

        for column_name, statement in PROFILE_PICTURE_COLUMN_STATEMENTS.items():
            if column_name not in existing_columns:
                cursor.execute(statement)
                added_columns.append(column_name)

        if added_columns:
            connection.commit()

        return added_columns
    finally:
        connection.close()