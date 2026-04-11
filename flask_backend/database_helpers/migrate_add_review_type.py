"""One-off SQLite migration: add Review.review_type column and index.

Run from flask_backend:
    py database_helpers/migrate_add_review_type.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "instance" / "app.sqlite"


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()

        cols = [row[1] for row in cursor.execute("PRAGMA table_info(Review)")]
        added_column = False
        if "review_type" not in cols:
            cursor.execute("ALTER TABLE Review ADD COLUMN review_type VARCHAR(16) NOT NULL DEFAULT 'peer'")
            added_column = True

        cursor.execute("CREATE INDEX IF NOT EXISTS ix_review_review_type ON Review(review_type)")
        conn.commit()

        print("Migration complete")
        print(f"- Column added: {added_column}")
        print("- Index ensured: ix_review_review_type")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
