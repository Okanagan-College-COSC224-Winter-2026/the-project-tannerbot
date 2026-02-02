import pytest
import json

@pytest.fixture
def client(app):
    """Flask test client fixture."""
    return app.test_client()


def test_practice_get_endpoint(client):
    """Test HTTP GET request to /example/test endpoint."""
    response = client.get('/example/test')
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data['course'] == 'cosc224'