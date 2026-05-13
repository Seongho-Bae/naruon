import datetime

import pytest
from fastapi.testclient import TestClient

from core.config import settings
from db.models import AuditLog, LLMProvider
from db.session import get_db
from main import app


class MockScalars:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items

    def first(self):
        return self._items[0] if self._items else None


class MockResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return MockScalars(self._items)


class MockSession:
    def __init__(self):
        self.providers: list[LLMProvider] = []
        self.audits: list[AuditLog] = []

    async def execute(self, stmt):
        stmt_str = str(stmt).lower()
        if "llm_providers.id =" in stmt_str:
            return MockResult(self.providers[:1])
        return MockResult(self.providers)

    def add(self, obj):
        if isinstance(obj, LLMProvider):
            obj.id = len(self.providers) + 1
            obj.updated_at = datetime.datetime.now(datetime.timezone.utc)
            self.providers.append(obj)
        elif isinstance(obj, AuditLog):
            self.audits.append(obj)

    async def delete(self, obj):
        self.providers = [provider for provider in self.providers if provider is not obj]

    async def commit(self):
        return None

    async def refresh(self, obj):
        return None


mock_session = MockSession()


@pytest.fixture(autouse=True)
def enable_dev_headers():
    previous = settings.TRUST_DEV_HEADERS
    settings.TRUST_DEV_HEADERS = True
    yield
    settings.TRUST_DEV_HEADERS = previous


@pytest.fixture(autouse=True)
def override_get_db():
    async def override_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_db
    yield
    app.dependency_overrides.clear()
    mock_session.providers = []
    mock_session.audits = []


@pytest.fixture
def admin_client():
    with TestClient(
        app,
        headers={
            "X-User-Id": "admin",
            "X-User-Role": "organization_admin",
            "X-Organization-Id": "org-acme",
        },
    ) as client:
        yield client


@pytest.fixture
def member_client():
    with TestClient(
        app,
        headers={
            "X-User-Id": "member",
            "X-User-Role": "member",
            "X-Organization-Id": "org-acme",
        },
    ) as client:
        yield client


def test_llm_provider_crud_admin(admin_client):
    response = admin_client.post(
        "/api/llm-providers",
        json={
            "name": "Primary OpenAI",
            "provider_type": "openai",
            "api_key": "sk-12345",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Primary OpenAI"
    assert data["configured"] is True
    assert data["fingerprint"] is not None
    assert "api_key" not in data

    provider_id = data["id"]

    response = admin_client.get("/api/llm-providers")
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = admin_client.put(f"/api/llm-providers/{provider_id}", json={"is_active": True})
    assert response.status_code == 200
    assert response.json()["is_active"] is True

    response = admin_client.delete(f"/api/llm-providers/{provider_id}")
    assert response.status_code == 204


def test_llm_provider_member_rejected(member_client):
    response = member_client.get("/api/llm-providers")
    assert response.status_code == 200

    response = member_client.post(
        "/api/llm-providers",
        json={"name": "Malicious", "provider_type": "openai"},
    )
    assert response.status_code == 403
