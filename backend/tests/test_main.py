from fastapi.testclient import TestClient
from main import app
from tests.auth_helpers import auth_headers

client = TestClient(app, headers=auth_headers("testuser"))


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "AI Email Client API"}
