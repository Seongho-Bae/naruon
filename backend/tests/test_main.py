from fastapi.testclient import TestClient
from main import app

client = TestClient(app, headers={"X-User-Id": "testuser"})


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "AI Email Client API"}
