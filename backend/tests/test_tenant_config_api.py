import pytest
from fastapi.testclient import TestClient
from main import app
from db.session import get_db


PUBLIC_RESOLVER_RESULTS = [(2, 1, 6, "", ("93.184.216.34", 587))]

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
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_tenant_config_endpoint(client, mock_db):
    post_payload = {
        "user_id": "test_user",
        "openai_api_key": "sk-123",
        "smtp_server": "smtp.example.com",
        "oauth_client_secret": "secret-456",
    }
    response = client.post("/api/config", json=post_payload, headers={"X-User-Id": "test_user"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    assert "test_user" in mock_db.objects

    get_response = client.get("/api/config", params={"user_id": "test_user"}, headers={"X-User-Id": "test_user"})
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["user_id"] == "test_user"
    assert data["openai_api_key"] == "********"
    assert data["oauth_client_secret"] == "********"
    assert data["smtp_server"] == "smtp.example.com"
    assert data["google_client_secret"] is None


@pytest.mark.parametrize(
    ("field", "host", "port_field", "port"),
    [
        ("smtp_server", "127.0.0.1", "smtp_port", 587),
        ("smtp_server", "localhost", "smtp_port", 587),
        ("smtp_server", "::1", "smtp_port", 587),
        ("imap_server", "10.0.0.1", "imap_port", 993),
        ("pop3_server", "169.254.169.254", "pop3_port", 995),
    ],
)
def test_tenant_config_rejects_private_mail_hosts(
    client,
    field,
    host,
    port_field,
    port,
):
    response = client.post(
        "/api/config",
        json={
            "user_id": "test_user",
            field: host,
            port_field: port,
        },
        headers={"X-User-Id": "test_user"},
    )

    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]


@pytest.mark.parametrize(
    ("field", "host", "port_field", "port"),
    [
        ("smtp_server", "smtp.example.com", "smtp_port", 0),
        ("smtp_server", "smtp.example.com", "smtp_port", 70000),
        ("imap_server", "imap.example.com", "imap_port", 22),
        ("pop3_server", "pop3.example.com", "pop3_port", 587),
    ],
)
def test_tenant_config_rejects_invalid_mail_ports(
    client,
    field,
    host,
    port_field,
    port,
):
    response = client.post(
        "/api/config",
        json={
            "user_id": "test_user",
            field: host,
            port_field: port,
        },
        headers={"X-User-Id": "test_user"},
    )

    assert response.status_code == 400
    assert "port" in response.json()["detail"]


def test_tenant_config_accepts_resolvable_public_mail_hosts(client, monkeypatch):
    monkeypatch.setattr(
        "services.mail_endpoint_policy.socket.getaddrinfo",
        lambda *args, **kwargs: PUBLIC_RESOLVER_RESULTS,
    )

    response = client.post(
        "/api/config",
        json={
            "user_id": "test_user",
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "imap_server": "imap.example.com",
            "imap_port": 993,
            "pop3_server": "pop3.example.com",
            "pop3_port": 995,
        },
        headers={"X-User-Id": "test_user"},
    )

    assert response.status_code == 200
