import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from db.session import get_db
from main import app
from tests.conftest import TEST_AUTH_HEADERS


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


@pytest_asyncio.fixture
async def client(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=TEST_AUTH_HEADERS,
    ) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_tenant_config_endpoint(client: AsyncClient, mock_db):
    post_payload = {
        "user_id": "default",
        "openai_api_key": "sk-123",
        "smtp_server": "8.8.8.8",
        "smtp_port": 587,
        "oauth_client_secret": "secret-456",
    }
    response = await client.post(
        "/api/config",
        json=post_payload,
        headers={**TEST_AUTH_HEADERS, "X-User-Id": "attacker"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    assert "default" in mock_db.objects

    get_response = await client.get(
        "/api/config",
        params={"user_id": "default"},
        headers={**TEST_AUTH_HEADERS, "X-User-Id": "attacker"},
    )
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["user_id"] == "default"
    assert data["openai_api_key"] == "********"
    assert data["oauth_client_secret"] == "********"
    assert data["smtp_server"] == "8.8.8.8"
    assert data["smtp_port"] == 587
    assert data["google_client_secret"] is None


@pytest.mark.asyncio
async def test_tenant_config_rejects_user_id_impersonation(client: AsyncClient):
    response = await client.get(
        "/api/config",
        params={"user_id": "attacker"},
        headers={**TEST_AUTH_HEADERS, "X-User-Id": "attacker"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mail_settings",
    [
        {"smtp_server": "127.0.0.1", "smtp_port": 587},
        {"imap_server": "10.0.0.1", "imap_port": 993},
        {"pop3_server": "169.254.169.254", "pop3_port": 995},
        {"smtp_server": "8.8.8.8", "smtp_port": 80},
        {"smtp_server": "http://127.0.0.1", "smtp_port": 587},
    ],
)
async def test_tenant_config_rejects_unsafe_mail_server_targets(
    client: AsyncClient, mock_db, mail_settings: dict[str, object]
):
    response = await client.post(
        "/api/config",
        json={"user_id": "default", **mail_settings},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Mail server target is not allowed"}
    assert "default" not in mock_db.objects
