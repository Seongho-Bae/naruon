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
        self.pop3_username = None
        self.pop3_password = None
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

def test_get_and_update_tenant_config(client: TestClient, monkeypatch):
    monkeypatch.setattr(
        "api.tenant_config.validate_smtp_host",
        lambda host, *, resolve_host=True: host,
    )
    monkeypatch.setattr(
        "api.tenant_config.validate_smtp_destination",
        lambda host, port, *, resolve_host=True: (host, port),
    )
    monkeypatch.setattr(
        "api.tenant_config.validate_pop3_destination",
        lambda host, port, *, resolve_host=True: (host, port),
    )

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
        "pop3_server": "pop3.example.com",
        "pop3_port": 995,
        "pop3_username": "pop3-user",
        "pop3_password": "pop3-secret",
    }
    response = client.put("/api/accounts/config", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["smtp_server"] == "smtp.example.com"
    assert data["smtp_port"] == 587
    assert data["smtp_username"] == "user@example.com"
    assert data["pop3_server"] == "pop3.example.com"
    assert data["pop3_port"] == 995
    assert data["pop3_username"] == "pop3-user"
    assert data["has_pop3_password"] is True


def test_accounts_config_rejects_private_imap_host(client: TestClient):
    response = client.put(
        "/api/accounts/config",
        json={"imap_server": "127.0.0.1", "imap_port": 993},
    )

    assert response.status_code == 400
    assert "imap_server" in response.json()["detail"]


def test_accounts_config_rejects_private_pop3_host(client: TestClient):
    response = client.put(
        "/api/accounts/config",
        json={"pop3_server": "127.0.0.1", "pop3_port": 995},
    )

    assert response.status_code == 400
    assert "pop3_server" in response.json()["detail"]


def test_accounts_config_rejects_unsafe_imap_port(client: TestClient, monkeypatch):
    def reject_imap_port(host, port, *, resolve_host=True):
        from services.email_client import validate_imap_port

        validate_imap_port(port)
        return host, port

    monkeypatch.setattr(
        "api.tenant_config.validate_imap_destination",
        reject_imap_port,
    )

    response = client.put(
        "/api/accounts/config",
        json={"imap_server": "imap.example.com", "imap_port": 22},
    )

    assert response.status_code == 400
    assert "imap_port" in response.json()["detail"]


def test_accounts_config_rejects_unsafe_pop3_port(client: TestClient, monkeypatch):
    def reject_pop3_port(host, port, *, resolve_host=True):
        raise ValueError("POP3 port is not allowed")

    monkeypatch.setattr(
        "api.tenant_config.validate_pop3_destination",
        reject_pop3_port,
    )

    response = client.put(
        "/api/accounts/config",
        json={"pop3_server": "pop3.example.com", "pop3_port": 22},
    )

    assert response.status_code == 400
    assert "pop3_port" in response.json()["detail"]
