import pytest
from fastapi.testclient import TestClient
from main import app
from db.session import get_db

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")

class MockTenantConfig:
    def __init__(self, user_id, organization_id=None):
        self.user_id = user_id
        self.organization_id = organization_id
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
        self.configs = {}
        self.commits = 0

    def _query_key(self, stmt):
        params = dict(stmt.compile().params)
        user_id = params.get("user_id_1")
        organization_id = params.get("organization_id_1")
        return user_id, organization_id

    async def execute(self, stmt):
        return MockResult(self.configs.get(self._query_key(stmt)))

    def add(self, obj):
        self.configs[(obj.user_id, obj.organization_id)] = obj

    async def commit(self):
        self.commits += 1

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

    # Get config returns an empty response without creating a row.
    response = client.get("/api/accounts/config")
    assert response.status_code == 200
    data = response.json()
    assert data["smtp_server"] is None
    assert data["user_id"] == "testuser"

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


def test_accounts_config_uses_signed_session_organization_scope(monkeypatch):
    monkeypatch.setattr(
        "api.tenant_config.validate_smtp_host",
        lambda host, *, resolve_host=True: host,
    )
    monkeypatch.setattr(
        "api.tenant_config.validate_smtp_destination",
        lambda host, port, *, resolve_host=True: (host, port),
    )
    session = MockSession()

    async def scoped_db():
        yield session

    app.dependency_overrides[get_db] = scoped_db
    try:
        with TestClient(app, headers={"X-User-Id": "shared-user"}) as c:
            first = c.put(
                "/api/accounts/config",
                json={"smtp_server": "smtp.example.com", "smtp_port": 587},
                headers={"X-Organization-Id": "org-acme"},
            )
            second = c.put(
                "/api/accounts/config",
                json={"smtp_server": "smtp.other.com", "smtp_port": 587},
                headers={"X-Organization-Id": "org-rival"},
            )
            acme_read = c.get(
                "/api/accounts/config",
                headers={"X-Organization-Id": "org-acme"},
            )
            rival_read = c.get(
                "/api/accounts/config",
                headers={"X-Organization-Id": "org-rival"},
            )
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 200
    assert second.status_code == 200
    assert acme_read.json()["smtp_server"] == "smtp.example.com"
    assert rival_read.json()["smtp_server"] == "smtp.other.com"
    assert ("shared-user", "org-acme") in session.configs
    assert ("shared-user", "org-rival") in session.configs


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
