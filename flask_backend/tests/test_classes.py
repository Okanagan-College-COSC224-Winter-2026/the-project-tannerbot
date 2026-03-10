"""
Tests for classes endpoints
"""

import json


def test_create_classes(test_client, make_admin):
    """
    GIVEN a logged-in teacher user
    WHEN POST /class/create_class is called with valid data
    THEN a new class should be created
    """
    # Set the admin user by default into the database
    make_admin(email="admin@example.com", password="admin", name="adminuser")

    # Login as teacher/admin
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "admin@example.com", "password": "admin"}),
        headers={"Content-Type": "application/json"},
    )
    response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Math 101"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 201
    assert response.json["msg"] == "Class created"
    assert "id" in response.json["class"]


def test_create_class_not_teacher(test_client):
    """
    GIVEN a logged-in non-teacher user
    WHEN POST /class/create_class is called
    THEN the request should be forbidden
    """
    # Register and login as non-teacher
    test_client.post(
        "/auth/register",
        data=json.dumps(
            {"name": "studentuser", "password": "Password123!", "email": "student@example.com"}
        ),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    # Attempt to create class
    response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Math 101"}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 403
    assert response.json["msg"] == "Insufficient permissions"


def test_get_classes(test_client, make_admin):
    """
    GIVEN a logged-in user
    WHEN GET /class/browse_classes is called
    THEN the list of classes should be returned
    """

    # Set the admin user by default into the database
    make_admin(email="admin@example.com", password="admin", name="adminuser")

    # Login as teacher/admin
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "admin@example.com", "password": "admin"}),
        headers={"Content-Type": "application/json"},
    )
    # Create a class
    test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Math 101"}),
        headers={"Content-Type": "application/json"},
    )
    # Get classes
    response = test_client.get("/class/browse_classes", headers={"Content-Type": "application/json"})
    assert response.status_code == 200
    classes = response.json
    assert any(c["name"] == "Math 101" for c in classes)
    assert len(classes) >= 1

def test_get_classes_not_logged_in(test_client):
    """
    GIVEN a non-logged-in user
    WHEN GET /class/browse_classes is called
    THEN the request should be unauthorized
    """
    response = test_client.get("/class/browse_classes", headers={"Content-Type": "application/json"})
    assert response.status_code == 401

def test_get_courses_for_teacher(test_client, make_admin):
    """
    GIVEN a logged-in teacher user
    WHEN GET /class/classes is called
    THEN the list of classes taught by the teacher should be returned
    """

    # Set the admin user by default into the database
    make_admin(email="admin@example.com", password="admin", name="adminuser")
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Login as teacher/admin
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "admin@example.com", "password": "admin"}),
        headers={"Content-Type": "application/json"},
    )
    # Create a class
    test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Math 101"}),
        headers={"Content-Type": "application/json"},
    )
    # Login other user
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Create a class
    test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "History 201"}),
        headers={"Content-Type": "application/json"},
    )
    # Get classes
    response = test_client.get("/class/classes", headers={"Content-Type": "application/json"})
    assert response.status_code == 200
    classes = response.json
    assert any(c["name"] == "History 201" for c in classes)
    assert len(classes) >= 1

def test_get_courses_for_student(test_client, make_admin, enroll_user_in_course):
    """
    GIVEN a logged-in student user
    WHEN GET /class/classes is called
    THEN the list of classes the student is enrolled in should be returned
    """

    # Set the admin user by default into the database
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Create a class
    response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "History 201"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = response.json["class"]["id"]
    # Register and login as student
    test_client.post(
        "/auth/register",
        data=json.dumps(
            {"name": "studentuser", "password": "Password123!", "email": "student@example.com"}),
        headers={"Content-Type": "application/json"},
    )
    login_response = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    student_id = login_response.json["id"]
    # Enroll student in class
    enrollment = enroll_user_in_course(user_id=student_id, course_id=class_id)
    assert enrollment.userID == student_id and enrollment.courseID == class_id
    # Get classes
    response = test_client.get("/class/classes", headers={"Content-Type": "application/json"})
    assert response.status_code == 200
    classes = response.json
    assert any(c["name"] == "History 201" for c in classes)
    assert len(classes) >= 1

def test_get_courses_for_student_not_enrolled(test_client):
    """
    GIVEN a logged-in student user not enrolled in any classes
    WHEN GET /class/classes is called
    THEN an empty list should be returned
    """
    # Register and login as student
    test_client.post(
        "/auth/register",
        data=json.dumps(
            {"name": "studentuser2", "password": "Password123!", "email": "student2@example.com"}),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student2@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    # Get classes
    response = test_client.get("/class/classes", headers={"Content-Type": "application/json"})
    assert response.status_code == 200
    classes = response.json
    assert classes == []


def test_get_courses_for_student_returns_only_enrolled_classes(
    test_client, make_admin, enroll_user_in_course
):
    """
    GIVEN a student enrolled in one of multiple classes
    WHEN GET /class/classes is called
    THEN only enrolled classes are returned
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    enrolled_course_resp = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "History 201"}),
        headers={"Content-Type": "application/json"},
    )
    not_enrolled_course_resp = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Physics 301"}),
        headers={"Content-Type": "application/json"},
    )

    enrolled_course_id = enrolled_course_resp.json["class"]["id"]
    not_enrolled_course_id = not_enrolled_course_resp.json["class"]["id"]

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {"name": "studentuser", "password": "Password123!", "email": "student@example.com"}
        ),
        headers={"Content-Type": "application/json"},
    )
    login_response = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    student_id = login_response.json["id"]

    enrollment = enroll_user_in_course(user_id=student_id, course_id=enrolled_course_id)
    assert enrollment.userID == student_id and enrollment.courseID == enrolled_course_id

    response = test_client.get("/class/classes", headers={"Content-Type": "application/json"})
    assert response.status_code == 200

    classes = response.json
    class_ids = {course["id"] for course in classes}
    class_names = {course["name"] for course in classes}

    assert enrolled_course_id in class_ids
    assert "History 201" in class_names
    assert not_enrolled_course_id not in class_ids
    assert "Physics 301" not in class_names


def test_get_courses_not_logged_in(test_client):
    """
    GIVEN a non-logged-in user
    WHEN GET /class/classes is called
    THEN the request should be unauthorized
    """
    response = test_client.get("/class/classes", headers={"Content-Type": "application/json"})
    assert response.status_code == 401


def test_get_class_members_for_teacher(test_client, make_admin, enroll_user_in_course):
    """
    GIVEN a teacher with an enrolled student in their class
    WHEN POST /class/members is called
    THEN the teacher receives the class member list including the student
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "COSC 404"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {
                "name": "studentuser",
                "password": "Password123!",
                "email": "student@example.com",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    student_login = test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    student_id = student_login.json["id"]
    enroll_user_in_course(user_id=student_id, course_id=class_id)

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.post(
        "/class/members",
        data=json.dumps({"id": class_id}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 200
    members = response.json
    assert any(m["email"] == "student@example.com" for m in members)

# US19 test cases start (needs to be cleaned up)
def test_get_class_members_returns_student_id_from_csv(test_client, make_admin):
    """
    GIVEN a teacher who enrolls students via CSV with student IDs
    WHEN POST /class/members is called
    THEN the student_id field is returned for enrolled students
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "COSC 404"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    csv_text = (
        "id,name,email\n"
        "300325853,Gregory Bigglesworth,gbizzle@example.com\n"
        "300325854,Sarah Connor,sconnor@example.com\n"
    )
    enroll_response = test_client.post(
        "/class/enroll_students",
        data=json.dumps({"class_id": class_id, "students": csv_text}),
        headers={"Content-Type": "application/json"},
    )
    assert enroll_response.status_code == 200

    members_response = test_client.post(
        "/class/members",
        data=json.dumps({"id": class_id}),
        headers={"Content-Type": "application/json"},
    )
    assert members_response.status_code == 200

    members_by_email = {member["email"]: member for member in members_response.json}
    assert members_by_email["gbizzle@example.com"]["student_id"] == "300325853"
    assert members_by_email["sconnor@example.com"]["student_id"] == "300325854"

def test_enroll_in_class(test_client, make_admin):
    """
    GIVEN a logged-in teacher user
    WHEN POST /class/enroll_students is called with valid data
    THEN the teacher should enroll students in the class
    """
    # Set the admin user by default into the database
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Login as teacher/admin
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Create a class
    response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Science 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = response.json["class"]["id"]
    # Enroll students
    csv_text = (
        "id,name,email\n"
        "300325853,Gregory Bigglesworth,gbizzle@yandex.ru\n"
        "300325854,Sarah Connor,sconnor@example.com\n"
    )
    response = test_client.post(
        "/class/enroll_students",
        data=json.dumps({"class_id": class_id, "students": csv_text}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json["msg"] == "2 students added to course Science 101"

def test_enroll_in_class_not_teacher(test_client):
    """
    GIVEN a logged-in non-teacher user
    WHEN POST /class/enroll_students is called
    THEN the request should be forbidden
    """
    # Register and login as non-teacher
    test_client.post(
        "/auth/register",
        data=json.dumps(
            {"name": "studentuser", "password": "Password123!", "email": "student@example.com"}),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student@example.com", "password": "Password123!"}),
        headers={"Content-Type": "application/json"},
    )
    # Attempt to enroll students
    csv_text = (
        "id,name,email\n"
        "300325853,Gregory Bigglesworth,gbizzle@yandex.ru\n"
        "300325854,Sarah Connor,sconnor@example.com\n"
    )
    response = test_client.post(
        "/class/enroll_students",
        data=json.dumps({"class_id": 1, "students": csv_text}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 403
    assert response.json["msg"] == "Insufficient permissions"

def test_enroll_in_class_missing_data(test_client, make_admin):
    """
    GIVEN a logged-in teacher user
    WHEN POST /class/enroll_students is called with missing data
    THEN the request should return a 400 error
    """
    # Set the admin user by default into the database
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Login as teacher/admin
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Attempt to enroll students with missing data
    response = test_client.post(
        "/class/enroll_students",
        data=json.dumps({"class_id": 1}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "Class ID and student emails are required"

def test_enroll_in_class_not_found(test_client, make_admin):
    """
    GIVEN a logged-in teacher user
    WHEN POST /class/enroll_students is called with a non-existent class ID
    THEN the request should return a 404 error
    """
    # Set the admin user by default into the database
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Login as teacher/admin
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Attempt to enroll students in a non-existent class
    csv_text = (
        "id,name,email\n"
        "300325853,Gregory Bigglesworth,gbizzle@yandex.ru\n"
        "300325854,Sarah Connor,sconnor@example.com\n"
    )
    response = test_client.post(
        "/class/enroll_students",
        data=json.dumps({"class_id": 9999, "students": csv_text}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 404
    assert response.json["msg"] == "Class not found"

def test_enroll_in_class_unauthorized(test_client, make_admin):
    """
    GIVEN a logged-in teacher user who is not the teacher of the class
    WHEN POST /class/enroll_students is called
    THEN the request should return a 403 error
    """
    # Set the admin user by default into the database
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    make_admin(email="otherteacher@example.com", password="teacher", name="otherteacheruser")
    # Login as teacher/admin
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "otherteacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Create a class as the first teacher
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Science 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = response.json["class"]["id"]
    # Login as other teacher
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "otherteacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Attempt to enroll students
    csv_text = (
        "id,name,email\n"
        "300325853,Gregory Bigglesworth,gbizzle@yandex.ru\n"
        "300325854,Sarah Connor,sconnor@example.com\n"
    )
    response = test_client.post(
        "/class/enroll_students",
        data=json.dumps({"class_id": class_id, "students": csv_text}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 403
    assert response.json["msg"] == "You are not authorized to enroll students in this class"

def test_enroll_in_class_not_logged_in(test_client):
    """
    GIVEN a non-logged-in user
    WHEN POST /class/enroll_students is called
    THEN the request should be unauthorized
    """
    csv_text = (
        "id,name,email\n"
        "300325853,Gregory Bigglesworth,gbizzle@yandex.ru\n"
        "300325854,Sarah Connor,sconnor@example.com\n"
    )
    response = test_client.post(
        "/class/enroll_students",
        data=json.dumps({"class_id": 1, "students": csv_text}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 401

def test_enroll_in_class_empty_csv(test_client, make_admin):
    """
    GIVEN a logged-in teacher user
    WHEN POST /class/enroll_students is called with an empty CSV
    THEN no students should be enrolled
    """
    # Set the admin user by default into the database
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Login as teacher/admin
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Create a class
    response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Science 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = response.json["class"]["id"]
    # Enroll students with empty CSV
    csv_text = ""
    response = test_client.post(
        "/class/enroll_students",
        data=json.dumps({"class_id": class_id, "students": csv_text}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "Class ID and student emails are required"

def test_enroll_in_class_malformed_csv(test_client, make_admin):
    """
    GIVEN a logged-in teacher user
    WHEN POST /class/enroll_students is called with a malformed CSV
    THEN the request should return a 400 error
    """
    # Set the admin user by default into the database
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Login as teacher/admin
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Create a class
    response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Science 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = response.json["class"]["id"]
    # Enroll students with malformed CSV
    csv_text = (
        "id,name,email\n"
        "300325853,Gregory Bigglesworth\n"  # Missing email
        "300325854,Sarah Connor,sconnor@example.com\n"
    )
    response = test_client.post(
        "/class/enroll_students",
        data=json.dumps({"class_id": class_id, "students": csv_text}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "Errors in CSV"

def test_enroll_in_class_existing_student(test_client, make_admin):
    """
    GIVEN a logged-in teacher user
    WHEN POST /class/enroll_students is called with a student already enrolled
    THEN the student should not be enrolled again
    """
    # Set the admin user by default into the database
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Login as teacher/admin
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Create a class
    response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Science 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = response.json["class"]["id"]
    # Enroll a student
    csv_text = (
        "id,name,email\n"
        "300325854,Sarah Connor,sconnor@example.com\n"
    )
    test_client.post(
        "/class/enroll_students",
        data=json.dumps({"class_id": class_id, "students": csv_text}),
        headers={"Content-Type": "application/json"},
    )
    # Enroll the same student again
    response = test_client.post(
        "/class/enroll_students",
        data=json.dumps({"class_id": class_id, "students": csv_text}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json["msg"] == "0 students added to course Science 101"
    assert response.json["added_count"] == 0
    assert response.json["already_enrolled_count"] == 1
    assert response.json["created_accounts_count"] == 0

def test_enroll_in_class_invalid_email_format(test_client, make_admin):
    """
    GIVEN a logged-in teacher user
    WHEN POST /class/enroll_students is called with an invalid email format
    THEN the request should return a 400 error
    """
    # Set the admin user by default into the database
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Login as teacher/admin
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Create a class
    response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Science 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = response.json["class"]["id"]
    # Enroll students with invalid email format
    csv_text = (
        "id,name,email\n"
        "300500123,John Doe,johndoeatexample.com\n"
        "300325853,Gregory Bigglesworth,gbizzle-at-yandex.ru\n"  # Invalid email
        "300325854,Sarah Connor,sconnor@example.com\n"
    )
    response = test_client.post(
        "/class/enroll_students",
        data=json.dumps({"class_id": class_id, "students": csv_text}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "Invalid email format: johndoeatexample.com"