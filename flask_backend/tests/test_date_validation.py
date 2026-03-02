"""
Tests for date validation in assignments
Tests for ensuring start_date <= due_date
"""

import json
import datetime


def test_create_assignment_with_invalid_date_range(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they try to create an assignment where start_date > due_date
    THEN the API should return a 400 error
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    # Log in as teacher
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    
    # Create a class
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Mathematics 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    # Try to create an assignment where start_date > due_date
    start_date = datetime.datetime(2027, 12, 31, 23, 59, 59)
    due_date = datetime.datetime(2027, 1, 1, 0, 0, 0)  # Earlier than start_date
    
    response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({
            "courseID": class_id,
            "name": "Invalid Assignment",
            "rubric": "Test",
            "start_date": start_date.isoformat(),
            "due_date": due_date.isoformat()
        }),
        headers={"Content-Type": "application/json"},
    )
    
    assert response.status_code == 400
    assert "Start date cannot be after the due date" in response.json["msg"]


def test_edit_assignment_with_invalid_date_range(test_client, make_admin):
    """
    GIVEN a teacher user with an existing assignment
    WHEN they try to edit it so that start_date > due_date
    THEN the API should return a 400 error
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    # Log in as teacher
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    
    # Create a class
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Mathematics 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    # Create an assignment with valid dates
    due_date = datetime.datetime(2027, 12, 31, 23, 59, 59)
    start_date = datetime.datetime(2027, 1, 1, 0, 0, 0)
    
    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({
            "courseID": class_id,
            "name": "Assignment 1",
            "rubric": "Test",
            "start_date": start_date.isoformat(),
            "due_date": due_date.isoformat()
        }),
        headers={"Content-Type": "application/json"},
    )
    
    assignment_id = assignment_response.json["assignment"]["id"]

    # Try to edit to set start_date after due_date
    invalid_start = datetime.datetime(2028, 1, 1, 0, 0, 0)
    response = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps({
            "start_date": invalid_start.isoformat(),
            "due_date": due_date.isoformat()
        }),
        headers={"Content-Type": "application/json"},
    )
    
    assert response.status_code == 400
    assert "Start date cannot be after the due date" in response.json["msg"]


def test_edit_assignment_with_valid_date_range(test_client, make_admin):
    """
    GIVEN a teacher user with an existing assignment
    WHEN they edit it with valid dates where start_date <= due_date
    THEN the assignment should be updated successfully
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    # Log in as teacher
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    
    # Create a class
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Mathematics 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    # Create an assignment
    response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({
            "courseID": class_id,
            "name": "Assignment 1",
            "rubric": "Test",
            "due_date": datetime.datetime(2027, 12, 31, 23, 59, 59).isoformat()
        }),
        headers={"Content-Type": "application/json"},
    )
    
    assignment_id = response.json["assignment"]["id"]

    # Edit with new valid dates
    new_start = datetime.datetime(2027, 6, 1, 0, 0, 0)
    new_due = datetime.datetime(2027, 12, 15, 23, 59, 59)
    
    edit_response = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps({
            "start_date": new_start.isoformat(),
            "due_date": new_due.isoformat()
        }),
        headers={"Content-Type": "application/json"},
    )
    
    assert edit_response.status_code == 200
    assert edit_response.json["assignment"]["start_date"] == "2027-06-01T00:00:00"
    assert edit_response.json["assignment"]["due_date"] == "2027-12-15T23:59:59"


def test_edit_assignment_with_only_due_date(test_client, make_admin):
    """
    GIVEN a teacher user with an existing assignment
    WHEN they edit only the due_date
    THEN the due_date should be updated correctly
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    # Log in as teacher
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    
    # Create a class
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Mathematics 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    # Create an assignment
    original_due = datetime.datetime(2027, 12, 31, 23, 59, 59)
    response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({
            "courseID": class_id,
            "name": "Assignment 1",
            "rubric": "Test",
            "due_date": original_due.isoformat()
        }),
        headers={"Content-Type": "application/json"},
    )
    
    assignment_id = response.json["assignment"]["id"]

    # Edit only the due_date
    new_due = datetime.datetime(2027, 11, 30, 23, 59, 59)
    
    edit_response = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps({
            "due_date": new_due.isoformat()
        }),
        headers={"Content-Type": "application/json"},
    )
    
    assert edit_response.status_code == 200
    assert edit_response.json["assignment"]["due_date"] == "2027-11-30T23:59:59"
    assert edit_response.json["assignment"]["name"] == "Assignment 1"  # Unchanged


def test_edit_assignment_with_only_start_date(test_client, make_admin):
    """
    GIVEN a teacher user with an existing assignment
    WHEN they edit only the start_date
    THEN the start_date should be updated correctly
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    # Log in as teacher
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    
    # Create a class
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Mathematics 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    # Create an assignment
    due_date = datetime.datetime(2027, 12, 31, 23, 59, 59)
    response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({
            "courseID": class_id,
            "name": "Assignment 1",
            "rubric": "Test",
            "due_date": due_date.isoformat()
        }),
        headers={"Content-Type": "application/json"},
    )
    
    assignment_id = response.json["assignment"]["id"]

    # Edit only the start_date
    new_start = datetime.datetime(2027, 1, 15, 8, 0, 0)
    
    edit_response = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps({
            "start_date": new_start.isoformat()
        }),
        headers={"Content-Type": "application/json"},
    )
    
    assert edit_response.status_code == 200
    assert edit_response.json["assignment"]["start_date"] == "2027-01-15T08:00:00"
    assert edit_response.json["assignment"]["due_date"] == due_date.isoformat()
