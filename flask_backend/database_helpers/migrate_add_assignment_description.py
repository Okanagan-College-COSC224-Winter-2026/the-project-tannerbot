"""One-off SQLite migration: add Assignment.description column.

Run from flask_backend:
    py database_helpers/migrate_add_assignment_description.py

Optional custom DB path:
    py database_helpers/migrate_add_assignment_description.py --db-path instance/app.sqlite
"""

import argparse
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "instance" / "app.sqlite"


def add_assignment_description_column(db_path: Path) -> int:
    """Add Assignment.description if missing.

    Returns:
        0 when migration succeeds or no-op,
        1 when migration cannot be applied.
    """
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()

        table_names = {row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "Assignment" not in table_names:
            print("Table 'Assignment' does not exist. Nothing to migrate.")
            return 1

        columns = [row[1] for row in cursor.execute("PRAGMA table_info(Assignment)")]
        if "description" in columns:
            print("Column 'description' already exists on Assignment.")
            return 0

        cursor.execute("ALTER TABLE Assignment ADD COLUMN description TEXT")
        conn.commit()

        print("Migration complete")
        print("- Column added: Assignment.description")
        return 0
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add Assignment.description column to an existing SQLite database.",
    )
    parser.add_argument(
        "--db-path",
        default=str(DEFAULT_DB_PATH),
        help="Path to the SQLite database file (default: instance/app.sqlite)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = Path(args.db_path)
    raise SystemExit(add_assignment_description_column(db_path))


if __name__ == "__main__":
    main()
