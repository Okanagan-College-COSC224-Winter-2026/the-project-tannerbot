import pytest


@pytest.fixture
def client(app):
    return app.test_client()


def test_practice_get_endpoint(client):
    response = client.get('/practice/test')
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data['course'] == 'cosc 224'
