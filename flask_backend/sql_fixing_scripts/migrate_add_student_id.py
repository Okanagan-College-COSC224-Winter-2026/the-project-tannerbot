"""One-off SQLite migration: add User.student_id column and index.

Run from flask_backend:
    py migrate_add_student_id.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("instance") / "app.sqlite"


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()

        cols = [row[1] for row in cursor.execute("PRAGMA table_info(User)")]
        added_column = False
        if "student_id" not in cols:
            cursor.execute("ALTER TABLE User ADD COLUMN student_id VARCHAR(64)")
            added_column = True

        cursor.execute("CREATE INDEX IF NOT EXISTS ix_user_student_id ON User(student_id)")
        conn.commit()

        print("Migration complete")
        print(f"- Column added: {added_column}")
        print("- Index ensured: ix_user_student_id")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
