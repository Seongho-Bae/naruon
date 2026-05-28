import asyncio
import datetime

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from core.config import settings
from db.models import AuditLog, LLMProvider
from db.session import get_db
from main import app

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")


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
            provider_id = stmt.compile().params.get("id_1")
            candidates = [
                provider for provider in self.providers if provider.id == provider_id
            ]
            if "llm_providers.organization_id" in stmt_str:
                organization_id = stmt.compile().params.get("organization_id_1")
                candidates = [
                    provider
                    for provider in candidates
                    if provider.organization_id == organization_id
                ]
            return MockResult(candidates[:1])
        if "llm_providers.organization_id" in stmt_str:
            organization_id = stmt.compile().params.get("organization_id_1")
            return MockResult(
                [
                    provider
                    for provider in self.providers
                    if provider.organization_id == organization_id
                ]
            )
        return MockResult(self.providers)

    def add(self, obj):
        if isinstance(obj, LLMProvider):
            obj.id = len(self.providers) + 1
            obj.updated_at = datetime.datetime.now(datetime.timezone.utc)
            self.providers.append(obj)
        elif isinstance(obj, AuditLog):
            self.audits.append(obj)

    async def delete(self, obj):
        self.providers = [
            provider for provider in self.providers if provider is not obj
        ]

    async def commit(self):
        return None

    async def refresh(self, obj):
        return None


mock_session = MockSession()


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
            "X-User-Role": "tenant_admin",
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
    assert mock_session.providers[0].user_id == "admin"
    assert mock_session.providers[0].organization_id == "org-acme"
    assert mock_session.audits[0].event_name == "llm_provider.create"
    assert mock_session.audits[0].organization_id == "org-acme"
    assert mock_session.audits[0].workspace_id == "workspace-org-acme"

    provider_id = data["id"]

    response = admin_client.get("/api/llm-providers")
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = admin_client.put(
        f"/api/llm-providers/{provider_id}", json={"is_active": True}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True

    response = admin_client.delete(f"/api/llm-providers/{provider_id}")
    assert response.status_code == 204


def test_llm_provider_rejects_internal_base_url_on_create(admin_client):
    response = admin_client.post(
        "/api/llm-providers",
        json={
            "name": "Metadata Target",
            "provider_type": "openai",
            "base_url": "http://169.254.169.254/latest/meta-data/",
            "api_key": "sk-12345",
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "LLM provider base URL is not allowed"}
    assert mock_session.providers == []


def test_llm_provider_rejects_private_base_url_on_update(admin_client):
    response = admin_client.post(
        "/api/llm-providers",
        json={"name": "Primary", "provider_type": "openai"},
    )
    assert response.status_code == 200, response.text

    response = admin_client.put(
        "/api/llm-providers/1",
        json={"base_url": "https://127.0.0.1:8000/v1"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "LLM provider base URL is not allowed"}


def test_llm_provider_rejects_userinfo_base_url(admin_client):
    response = admin_client.post(
        "/api/llm-providers",
        json={
            "name": "Userinfo Target",
            "provider_type": "openai",
            "base_url": "https://user:pass@api.openai.com/v1",
            "api_key": "sk-12345",
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "LLM provider base URL is not allowed"}


def test_llm_provider_accepts_allowlisted_external_https_base_url(
    admin_client, monkeypatch
):
    previous_allowed_hosts = settings.ALLOWED_LLM_BASE_URL_HOSTS
    previous_encryption_key = settings.ENCRYPTION_KEY
    settings.ALLOWED_LLM_BASE_URL_HOSTS = "llm-gateway.example.com"
    settings.ENCRYPTION_KEY = SecretStr("u9HJJ0G6sMCnrbT88ppMuIjEsn4EqH8U9jtw34oZw1c=")

    def fake_getaddrinfo(host, port, type=0):
        assert host == "llm-gateway.example.com"
        assert port == 443
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise AssertionError("LLM provider DNS resolution ran on event loop")
        return [(2, 1, 6, "", ("93.184.216.34", port))]

    monkeypatch.setattr(
        "services.llm_provider_urls.socket.getaddrinfo", fake_getaddrinfo
    )

    try:
        response = admin_client.post(
            "/api/llm-providers",
            json={
                "name": "External Gateway",
                "provider_type": "openai",
                "base_url": "https://llm-gateway.example.com/v1",
                "api_key": "sk-12345",
            },
        )
    finally:
        settings.ALLOWED_LLM_BASE_URL_HOSTS = previous_allowed_hosts
        settings.ENCRYPTION_KEY = previous_encryption_key

    assert response.status_code == 200, response.text
    assert response.json()["base_url"] == "https://llm-gateway.example.com/v1"


def test_llm_provider_member_rejected(member_client):
    response = member_client.get("/api/llm-providers")
    assert response.status_code == 403

    response = member_client.post(
        "/api/llm-providers",
        json={"name": "Malicious", "provider_type": "openai"},
    )
    assert response.status_code == 403


def test_llm_provider_model_declares_owner_scope_columns():
    column_names = {column.name for column in LLMProvider.__table__.columns}

    assert {"user_id", "organization_id"}.issubset(column_names)
    assert any(
        constraint.name == "uq_llm_providers_org_name"
        for constraint in LLMProvider.__table__.constraints
    )


def test_llm_provider_tenant_admin_cannot_access_other_org_provider(
    admin_client,
):
    provider = LLMProvider(
        id=7,
        user_id="rival-admin",
        organization_id="org-rival",
        name="Rival Provider",
        provider_type="openai",
        api_key="sk-rival",
        is_active=True,
        updated_at=datetime.datetime.now(datetime.timezone.utc),
    )
    mock_session.providers.append(provider)

    response = admin_client.get("/api/llm-providers")

    assert response.status_code == 200
    assert response.json() == []

    response = admin_client.put("/api/llm-providers/7", json={"is_active": False})
    assert response.status_code == 404
    assert provider.is_active is True

    response = admin_client.delete("/api/llm-providers/7")
    assert response.status_code == 404
    assert mock_session.providers == [provider]
