"""Lightweight startup migrations for local SQLite development databases."""

from pathlib import Path
import sqlite3


PROFILE_PICTURE_COLUMN_STATEMENTS = {
    "description": "ALTER TABLE User ADD COLUMN description TEXT",
    "profile_picture": "ALTER TABLE User ADD COLUMN profile_picture BLOB",
    "profile_picture_mime_type": (
        "ALTER TABLE User ADD COLUMN profile_picture_mime_type VARCHAR(128)"
    ),
}

ASSIGNMENT_GROUPING_COLUMN_STATEMENT = (
    "ALTER TABLE Assignment ADD COLUMN assignment_mode VARCHAR(16) NOT NULL DEFAULT 'solo'"
)

REVIEW_TYPE_COLUMN_STATEMENT = (
    "ALTER TABLE Review ADD COLUMN review_type VARCHAR(16) NOT NULL DEFAULT 'peer'"
)

RUBRIC_TYPE_COLUMN_STATEMENT = (
    "ALTER TABLE Rubric ADD COLUMN rubric_type VARCHAR(16) NOT NULL DEFAULT 'peer'"
)


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
    """Ensure legacy SQLite User tables contain optional profile metadata columns."""
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


def ensure_assignment_grouping_schema_for_sqlite(database_uri: str) -> list[str]:
    """Ensure SQLite databases have assignment grouping structures used by current models."""
    database_path = _sqlite_path_from_uri(database_uri)
    if database_path is None or not database_path.exists():
        return []

    connection = sqlite3.connect(database_path)
    try:
        cursor = connection.cursor()
        tables = {
            row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }

        updated = []

        if "Assignment" in tables:
            assignment_columns = {row[1] for row in cursor.execute("PRAGMA table_info(Assignment)")}
            if "assignment_mode" not in assignment_columns:
                cursor.execute(ASSIGNMENT_GROUPING_COLUMN_STATEMENT)
                updated.append("assignment_mode")

        if "CourseGroup" not in tables:
            cursor.execute(
                """
                CREATE TABLE CourseGroup (
                    id INTEGER NOT NULL,
                    name VARCHAR(255),
                    assignmentID INTEGER NOT NULL,
                    PRIMARY KEY (id),
                    CONSTRAINT uq_course_group_assignment_name UNIQUE (assignmentID, name),
                    FOREIGN KEY(assignmentID) REFERENCES Assignment (id)
                )
                """
            )
            cursor.execute("CREATE INDEX ix_CourseGroup_assignmentID ON CourseGroup (assignmentID)")
            updated.append("CourseGroup")

        if "Group_Members" not in tables:
            cursor.execute(
                """
                CREATE TABLE Group_Members (
                    userID INTEGER NOT NULL,
                    groupID INTEGER NOT NULL,
                    assignmentID INTEGER,
                    PRIMARY KEY (userID, groupID),
                    FOREIGN KEY(userID) REFERENCES User (id),
                    FOREIGN KEY(groupID) REFERENCES CourseGroup (id),
                    FOREIGN KEY(assignmentID) REFERENCES Assignment (id)
                )
                """
            )
            cursor.execute("CREATE INDEX ix_Group_Members_assignmentID ON Group_Members (assignmentID)")
            updated.append("Group_Members")

        if updated:
            connection.commit()

        return updated
    finally:
        connection.close()


def ensure_review_schema_for_sqlite(database_uri: str) -> list[str]:
    """Ensure SQLite databases have review_type support used by current Review model."""
    database_path = _sqlite_path_from_uri(database_uri)
    if database_path is None or not database_path.exists():
        return []

    connection = sqlite3.connect(database_path)
    try:
        cursor = connection.cursor()
        tables = {
            row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }

        updated = []

        if "Review" in tables:
            review_columns = {row[1] for row in cursor.execute("PRAGMA table_info(Review)")}
            if "review_type" not in review_columns:
                cursor.execute(REVIEW_TYPE_COLUMN_STATEMENT)
                updated.append("review_type")

            cursor.execute("CREATE INDEX IF NOT EXISTS ix_Review_review_type ON Review (review_type)")

        if updated:
            connection.commit()

        return updated
    finally:
        connection.close()


def ensure_rubric_schema_for_sqlite(database_uri: str) -> list[str]:
    """Ensure SQLite databases have rubric_type support used by current Rubric model."""
    database_path = _sqlite_path_from_uri(database_uri)
    if database_path is None or not database_path.exists():
        return []

    connection = sqlite3.connect(database_path)
    try:
        cursor = connection.cursor()
        tables = {
            row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }

        updated = []

        if "Rubric" in tables:
            rubric_columns = {row[1] for row in cursor.execute("PRAGMA table_info(Rubric)")}
            if "rubric_type" not in rubric_columns:
                cursor.execute(RUBRIC_TYPE_COLUMN_STATEMENT)
                updated.append("rubric_type")

            cursor.execute("CREATE INDEX IF NOT EXISTS ix_Rubric_rubric_type ON Rubric (rubric_type)")

        if updated:
            connection.commit()

        return updated
    finally:
        connection.close()