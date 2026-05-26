import pytest
from fastapi.testclient import TestClient
from main import app
from db.session import get_db

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")


class MockTenantConfig:
    def __init__(self, user_id):
        self.user_id = user_id
        self.smtp_server = None
        self.smtp_port = None
        self.smtp_username = None
        self.smtp_password = None
        self.imap_server = None
        self.imap_port = None
        self.imap_username = None
        self.imap_password = None
        self.pop3_server = None
        self.pop3_port = None
        self.oauth_client_id = None
        self.oauth_client_secret = None
        self.oauth_redirect_uri = None


class MockResult:
    def __init__(self, config=None):
        self.config = config

    def scalar_one_or_none(self):
        return self.config


class MockSession:
    def __init__(self):
        self.config = None

    async def execute(self, stmt):
        return MockResult(self.config)

    def add(self, obj):
        self.config = obj

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass


async def override_get_db():
    yield MockSession()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"X-User-Id": "testuser"}) as c:
        yield c
    app.dependency_overrides.clear()


def test_get_and_update_tenant_config(client: TestClient):
    # Get config (should create empty one)
    response = client.get("/api/accounts/config")
    assert response.status_code == 200
    data = response.json()
    assert data["smtp_server"] is None

    # Update config
    update_data = {
        "smtp_server": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "user@example.com",
    }
    response = client.put("/api/accounts/config", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["smtp_server"] == "smtp.example.com"
    assert data["smtp_port"] == 587
    assert data["smtp_username"] == "user@example.com"
