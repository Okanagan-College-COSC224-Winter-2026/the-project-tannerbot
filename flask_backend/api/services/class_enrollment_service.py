import csv
import io
import re

from werkzeug.security import generate_password_hash

from ..models import User, User_Course

EMAIL_PATTERN = r"[^@]+@[^@]+\.[^@]+"
REQUIRED_HEADERS = {"id", "name", "email"}


def csv_to_list(csv_text):
    """Convert CSV text to normalized student rows and parse errors."""
    rows = []
    errors = []
    if not csv_text or not csv_text.strip():
        return rows, ["CSV text empty"]

    stream = io.StringIO(csv_text.strip())
    try:
        reader = csv.DictReader(stream)
    except Exception as exc:
        return rows, [f"Failed to read CSV: {exc}"]

    headers = {h.strip() for h in reader.fieldnames or []}
    missing = REQUIRED_HEADERS - headers
    if missing:
        errors.append(f"Missing required headers: {', '.join(sorted(missing))}")
        return rows, errors

    for line_num, row in enumerate(reader, start=2):
        if row is None:
            continue

        normalized = {
            k.strip(): (v.strip() if isinstance(v, str) else "")
            for k, v in row.items()
        }
        if not any(normalized.values()):
            continue

        if any(not normalized[field] for field in REQUIRED_HEADERS):
            errors.append(f"Line {line_num}: Missing required fields")
            continue

        rows.append(
            {
                "id": normalized["id"],
                "name": normalized["name"],
                "email": normalized["email"],
            }
        )

    return rows, errors


def enroll_students_in_course(students, class_id):
    return enroll_students_in_course_with_passwords(
        students,
        class_id,
        default_password="password123",
        student_passwords={},
    )


def enroll_students_in_course_with_passwords(
    students,
    class_id,
    default_password="password123",
    student_passwords=None,
):
    enrolled_students = []
    created_accounts = []
    already_enrolled = []

    default_password = (default_password or "password123").strip() or "password123"
    student_passwords = student_passwords if isinstance(student_passwords, dict) else {}

    for student_info in students:
        email = student_info["email"]
        student_id = student_info["id"]
        if not re.match(EMAIL_PATTERN, email):
            return None, f"Invalid email format: {email}"

        name = student_info["name"]
        student = User.get_by_email(email)
        if not student:
            raw_password = student_passwords.get(email, default_password)
            password_to_use = (
                raw_password.strip() if isinstance(raw_password, str) else default_password
            ) or default_password
            student = User(
                name=name,
                email=email,
                hash_pass=generate_password_hash(password_to_use),
                role="student",
                student_id=student_id,
            )
            try:
                User.create_user(student)
                created_accounts.append(email)
            except Exception as exc:
                return None, f"Error creating user {email}: {str(exc)}"
        elif student.role == "student" and not student.student_id:
            student.student_id = student_id
            student.update()

        enrollment = User_Course.get(student.id, class_id)
        if enrollment:
            already_enrolled.append(email)
            continue

        User_Course.add(student.id, class_id)
        enrolled_students.append(email)

    return {
        "enrolled_students": enrolled_students,
        "created_accounts": created_accounts,
        "already_enrolled": already_enrolled,
    }, None


def build_enrollment_preview(students, class_id):
    rows = []
    new_accounts_count = 0
    existing_accounts_count = 0
    already_enrolled_count = 0

    for student_info in students:
        email = student_info["email"]
        if not re.match(EMAIL_PATTERN, email):
            return None, f"Invalid email format: {email}"

        student = User.get_by_email(email)
        enrollment_exists = bool(student and User_Course.get(student.id, class_id))
        account_exists = student is not None

        if account_exists:
            existing_accounts_count += 1
        else:
            new_accounts_count += 1

        if enrollment_exists:
            already_enrolled_count += 1

        rows.append(
            {
                "id": student_info["id"],
                "name": student_info["name"],
                "email": email,
                "account_exists": account_exists,
                "already_enrolled": enrollment_exists,
            }
        )

    return {
        "students": rows,
        "new_accounts_count": new_accounts_count,
        "existing_accounts_count": existing_accounts_count,
        "already_enrolled_count": already_enrolled_count,
        "total_count": len(rows),
    }, None
