#!/usr/bin/env python3
"""
Quick test script to verify assignment description functionality
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_login():
    """Login as teacher to get session"""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "teacher@example.com",
        "password": "123456"
    }, headers={'Content-Type': 'application/json'})
    return response.status_code == 200

def test_create_assignment_with_description():
    """Test creating an assignment with description"""
    session = requests.Session()

    # Login first
    login_resp = session.post(f"{BASE_URL}/auth/login", json={
        "email": "teacher@example.com",
        "password": "123456"
    }, headers={'Content-Type': 'application/json'})

    if login_resp.status_code != 200:
        print("Login failed")
        return False

    # Create assignment with description
    create_resp = session.post(f"{BASE_URL}/assignment/create_assignment", json={
        "courseID": 1,
        "name": "Test Assignment with Description",
        "description": "This is a test description for the assignment",
        "due_date": "2024-12-31T23:59:00"
    }, headers={'Content-Type': 'application/json'})

    print(f"Create assignment status: {create_resp.status_code}")
    if create_resp.status_code == 201:
        data = create_resp.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        assignment_id = data.get('assignment', {}).get('id')
        description = data.get('assignment', {}).get('description')
        if assignment_id and description == "This is a test description for the assignment":
            print("✓ Description field working correctly!")
            return True
        else:
            print("✗ Description not found in response or incorrect value")
            return False
    else:
        print(f"✗ Create failed: {create_resp.text}")
        return False

if __name__ == "__main__":
    print("Testing assignment description functionality...")
    if test_create_assignment_with_description():
        print("All tests passed!")
    else:
        print("Tests failed!")