from fastapi.testclient import TestClient
from main import app
from db.session import get_db

client = TestClient(app)


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
        # Very simple mock, assuming the query filters by user_id
        # We can extract the user_id from the query by looking at the right side of the condition
        # but to keep it simple we just return the stored config for test_user
        return MockResult(self.objects.get("test_user"))

    def add(self, obj):
        self.objects[obj.user_id] = obj

    async def commit(self):
        pass


mock_db = MockAsyncSession()


async def override_get_db():
    yield mock_db


app.dependency_overrides[get_db] = override_get_db


def test_tenant_config_endpoint():
    post_payload = {
        "user_id": "test_user",
        "openai_api_key": "sk-123",
        "smtp_server": "smtp.example.com",
        "oauth_client_secret": "secret-456",
    }
    response = client.post("/api/config", json=post_payload)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # Store it in our mock dict (normally db.add handles this)
    # The endpoint actually adds the TenantConfig object to our mock_db
    assert "test_user" in mock_db.objects

    get_response = client.get("/api/config", params={"user_id": "test_user"})
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["user_id"] == "test_user"
    assert data["openai_api_key"] == "********"
    assert data["oauth_client_secret"] == "********"
    assert data["smtp_server"] == "smtp.example.com"
    assert data["google_client_secret"] is None
