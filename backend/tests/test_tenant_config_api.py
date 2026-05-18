import pytest
from fastapi.testclient import TestClient
from main import app
from db.session import get_db

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")


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
    with TestClient(app, headers={"X-User-Id": "testuser"}) as c:
        yield c
    app.dependency_overrides.clear()


def test_tenant_config_endpoint(client, mock_db, monkeypatch):
    host_resolve_calls = []
    destination_resolve_calls = []

    def fake_validate_smtp_host(smtp_server, *, resolve_host=True):
        host_resolve_calls.append(resolve_host)
        return smtp_server

    def fake_validate_smtp_destination(smtp_server, smtp_port, *, resolve_host=True):
        destination_resolve_calls.append(resolve_host)
        return smtp_server, smtp_port

    monkeypatch.setattr("api.tenant_config.validate_smtp_host", fake_validate_smtp_host)
    monkeypatch.setattr(
        "api.tenant_config.validate_smtp_destination",
        fake_validate_smtp_destination,
    )

    post_payload = {
        "user_id": "test_user",
        "openai_api_key": "sk-123",
        "smtp_server": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "sender@example.com",
        "smtp_password": "smtp-secret",
        "imap_server": "imap.example.com",
        "imap_port": 993,
        "imap_username": "imap-user",
        "imap_password": "imap-secret",
        "oauth_client_secret": "secret-456",
    }
    response = client.post(
        "/api/config", json=post_payload, headers={"X-User-Id": "test_user"}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert host_resolve_calls == [True]
    assert destination_resolve_calls == [True]

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
    assert data["smtp_password"] == "********"
    assert data["imap_password"] == "********"
    assert data["smtp_server"] == "smtp.example.com"
    assert data["smtp_port"] == 587
    assert data["smtp_username"] == "sender@example.com"
    assert data["imap_server"] == "imap.example.com"
    assert data["imap_port"] == 993
    assert data["imap_username"] == "imap-user"
    assert data["google_client_secret"] is None


def test_tenant_config_stays_user_owned_even_for_admin_headers(client):
    response = client.post(
        "/api/config",
        json={"user_id": "member-user", "smtp_server": "smtp.example.com"},
        headers={
            "X-User-Id": "admin",
            "X-User-Role": "organization_admin",
            "X-Organization-Id": "org-acme",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Mailbox settings are personal and can only be managed by the authenticated user"
    }


def test_tenant_config_rejects_private_smtp_host(client):
    response = client.post(
        "/api/config",
        json={
            "user_id": "test_user",
            "smtp_server": "127.0.0.1",
            "smtp_port": 587,
        },
        headers={"X-User-Id": "test_user"},
    )

    assert response.status_code == 400
    assert "SMTP server is not allowed" in response.json()["detail"]


def test_tenant_config_rejects_metadata_smtp_host(client):
    response = client.post(
        "/api/config",
        json={
            "user_id": "test_user",
            "smtp_server": "169.254.169.254",
            "smtp_port": 587,
        },
        headers={"X-User-Id": "test_user"},
    )

    assert response.status_code == 400
    assert "SMTP server is not allowed" in response.json()["detail"]


def test_tenant_config_rejects_unsafe_smtp_port(client, monkeypatch):
    def fake_getaddrinfo(host, port=None, *args, **kwargs):
        return [(2, 1, 6, "", ("93.184.216.34", port or 587))]

    monkeypatch.setattr("services.email_client.socket.getaddrinfo", fake_getaddrinfo)

    response = client.post(
        "/api/config",
        json={
            "user_id": "test_user",
            "smtp_server": "smtp.example.com",
            "smtp_port": 22,
        },
        headers={"X-User-Id": "test_user"},
    )

    assert response.status_code == 400
    assert "SMTP port is not allowed" in response.json()["detail"]


def test_tenant_config_get_rejects_cross_user_access(client):
    response = client.get(
        "/api/config",
        params={"user_id": "member-user"},
        headers={
            "X-User-Id": "admin",
            "X-User-Role": "platform_admin",
            "X-Organization-Id": "org-acme",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Mailbox settings are personal and can only be viewed by the authenticated user"
    }
