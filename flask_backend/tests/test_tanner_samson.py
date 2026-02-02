import pytest
from flask import json

def test_practice_test_get_endpoint(client):
    """Test HTTP GET request to /practice/test endpoint."""
    response = client.get('/practice/test')
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None


def test_practice_test_get_endpoint_content_type(client):
    """Test that /practice/test returns JSON content."""
    response = client.get('/practice/test')
    assert response.content_type == 'application/json'


def test_practice_test_get_endpoint_unauthorized(client):
    """Test that /practice/test is accessible without authentication."""
    response = client.get('/practice/test')
    # Should not return 401 Unauthorized
    assert response.status_code != 401


def test_practice_test_get_endpoint_invalid_method(client):
    """Test that /practice/test does not accept POST requests."""
    response = client.post('/practice/test')
    assert response.status_code == 405  # Method Not Allowed