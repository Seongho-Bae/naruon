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
        # We don't implement full sqlalchemy querying here, just fake it
        # For our test, assume if user_id == "test_user", return a config if we stored one
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
    response = client.post(
        "/api/config", json={"user_id": "test_user", "openai_api_key": "sk-123"}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    get_response = client.get("/api/config", params={"user_id": "test_user"})
    assert get_response.status_code == 200
    assert get_response.json()["user_id"] == "test_user"
    assert get_response.json()["openai_api_key"] == "********"
