import pytest
from fastapi.testclient import TestClient
from main import app
from db.session import get_db
from api.auth import get_current_user


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
        return MockResult(self.objects.get("test_user"))

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
    app.dependency_overrides[get_current_user] = lambda: "test_user"
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()


def test_tenant_config_endpoint(client, mock_db):
    post_payload = {
        "user_id": "test_user",
        "openai_api_key": "sk-123",
        "smtp_server": "smtp.example.com",
        "oauth_client_secret": "secret-456",
    }
    response = client.post(
        "/api/config", json=post_payload, headers={"X-User-Id": "test_user"}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    assert "test_user" in mock_db.objects

    get_response = client.get(
        "/api/config",
        params={"user_id": "test_user"},
        headers={"X-User-Id": "test_user"},
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["user_id"] == "test_user"
    assert data["openai_api_key"] == "********"
    assert data["oauth_client_secret"] == "********"
    assert data["smtp_server"] == "smtp.example.com"
    assert data["google_client_secret"] is None
