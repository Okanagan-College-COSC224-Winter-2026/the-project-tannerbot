"""Enable profile picture support for an existing local SQLite dev database.

Run from flask_backend:
    py enable_profile_picture_support.py

This script is intended for teammates who already have instance/app.sqlite and
need the new User profile picture columns added without resetting their data.
Fresh databases created after pulling the new code already include the columns.
"""

from pathlib import Path

from api.startup_migrations import ensure_profile_picture_columns_for_sqlite


DB_PATH = Path(__file__).resolve().parent.parent / "instance" / "app.sqlite"


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(
            "Database not found at instance/app.sqlite. "
            "Run 'flask init_db' first if you have not created the local database yet."
        )

    added_columns = ensure_profile_picture_columns_for_sqlite(f"sqlite:///{DB_PATH.resolve()}")

    if added_columns:
        print("Profile picture support enabled.")
        print(f"Added columns: {', '.join(added_columns)}")
    else:
        print("Profile picture support is already enabled. No changes were needed.")

    print("Next step: restart the Flask backend if it is already running.")


if __name__ == "__main__":
    main()