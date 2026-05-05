import pytest
from fastapi.testclient import TestClient
from main import app
from db.session import get_db

# Mock async DB session
class MockResult:
    def __init__(self, obj):
        self.obj = obj

    def scalar_one_or_none(self):
        return self.obj

class MockAsyncSession:
    def __init__(self):
        self.objects = {}

    async def execute(self, query):
        return MockResult(self.objects.get("default"))

    def add(self, obj):
        self.objects[obj.user_id] = obj

    async def commit(self):
        pass

@pytest.fixture
def mock_db():
    return MockAsyncSession()

@pytest.fixture
def client(mock_db):
    async def override_get_db():
        yield mock_db
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_tenant_config_endpoint(client, mock_db):
    post_payload = {
        "user_id": "default",
        "openai_api_key": "sk-123",
        "smtp_server": "smtp.example.com",
        "oauth_client_secret": "secret-456",
    }
    response = client.post("/api/config", json=post_payload, headers={"X-User-Id": "attacker"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    assert "default" in mock_db.objects

    get_response = client.get("/api/config", params={"user_id": "default"}, headers={"X-User-Id": "attacker"})
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["user_id"] == "default"
    assert data["openai_api_key"] == "********"
    assert data["oauth_client_secret"] == "********"
    assert data["smtp_server"] == "smtp.example.com"
    assert data["google_client_secret"] is None


def test_tenant_config_rejects_user_id_impersonation(client):
    response = client.get("/api/config", params={"user_id": "attacker"}, headers={"X-User-Id": "attacker"})

    assert response.status_code == 403
