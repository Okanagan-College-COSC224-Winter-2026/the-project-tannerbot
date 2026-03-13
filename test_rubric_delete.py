#!/usr/bin/env python3
"""
Quick test script to verify rubric delete functionality
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_rubric_lifecycle():
    """Test creating and deleting a rubric"""
    session = requests.Session()

    # Login first
    login_resp = session.post(f"{BASE_URL}/auth/login", json={
        "email": "teacher@example.com",
        "password": "123456"
    }, headers={'Content-Type': 'application/json'})

    if login_resp.status_code != 200:
        print("Login failed")
        return False

    print("✓ Login successful")

    # Create a rubric
    create_resp = session.post(f"{BASE_URL}/assignment/create_rubric", json={
        "assignmentID": 1,
        "canComment": True
    }, headers={'Content-Type': 'application/json'})

    if create_resp.status_code != 201:
        print(f"Create rubric failed: {create_resp.status_code} - {create_resp.text}")
        return False

    rubric_data = create_resp.json()
    rubric_id = rubric_data.get('id')
    print(f"✓ Rubric created with ID: {rubric_id}")

    # Delete the rubric
    delete_resp = session.delete(f"{BASE_URL}/assignment/delete_rubric/{rubric_id}")

    if delete_resp.status_code != 200:
        print(f"Delete rubric failed: {delete_resp.status_code} - {delete_resp.text}")
        return False

    print("✓ Rubric deleted successfully")
    return True

if __name__ == "__main__":
    print("Testing rubric delete functionality...")
    if test_rubric_lifecycle():
        print("All tests passed!")
    else:
        print("Tests failed!")