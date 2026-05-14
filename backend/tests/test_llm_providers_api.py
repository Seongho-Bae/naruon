import datetime
import base64
import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import IntegrityError

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
        self.commit_error: Exception | None = None

    async def execute(self, stmt):
        stmt_str = str(stmt).lower()
        params = stmt.compile().params
        providers = list(self.providers)
        organization_id = next(
            (value for key, value in params.items() if "organization_id" in key), None
        )
        if organization_id is not None:
            providers = [
                provider
                for provider in providers
                if getattr(provider, "organization_id", None) == organization_id
            ]
        if "llm_providers.id =" in stmt_str:
            provider_id = next(
                (value for key, value in params.items() if key.startswith("id_")), None
            )
            providers = [
                provider for provider in providers if provider.id == provider_id
            ]
        return MockResult(providers)

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
        if self.commit_error is not None:
            error = self.commit_error
            self.commit_error = None
            raise error
        return None

    async def rollback(self):
        self.commit_error = None

    async def refresh(self, obj):
        return None


mock_session = MockSession()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _encode_test_jwt(payload: dict, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_part = _b64url(json.dumps(header, separators=(",", ":")).encode())
    payload_part = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_part}.{payload_part}".encode()
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{header_part}.{payload_part}.{_b64url(signature)}"


def _auth_headers(
    user_id: str, role: str, organization_id: str | None = "org-acme"
) -> dict[str, str]:
    secret = settings.OIDC_SHARED_SECRET
    assert secret is not None
    token = _encode_test_jwt(
        {
            "sub": user_id,
            "iss": settings.OIDC_ISSUER,
            "aud": settings.OIDC_AUDIENCE,
            "exp": int(
                (
                    datetime.datetime.now(datetime.timezone.utc)
                    + datetime.timedelta(minutes=5)
                ).timestamp()
            ),
            "roles": [role],
            **({"organization_id": organization_id} if organization_id else {}),
        },
        secret,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def configure_oidc_auth():
    previous_auth_mode = settings.AUTH_MODE
    previous_secret = settings.OIDC_SHARED_SECRET
    previous_issuer = settings.OIDC_ISSUER
    previous_audience = settings.OIDC_AUDIENCE
    previous_trust = settings.TRUST_DEV_HEADERS
    settings.AUTH_MODE = "oidc"
    settings.OIDC_SHARED_SECRET = "test-secret"
    settings.OIDC_ISSUER = "https://issuer.example.com/realms/naruon"
    settings.OIDC_AUDIENCE = "naruon-web"
    settings.TRUST_DEV_HEADERS = False
    yield
    settings.AUTH_MODE = previous_auth_mode
    settings.OIDC_SHARED_SECRET = previous_secret
    settings.OIDC_ISSUER = previous_issuer
    settings.OIDC_AUDIENCE = previous_audience
    settings.TRUST_DEV_HEADERS = previous_trust


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
        headers=_auth_headers("admin", "organization_admin"),
    ) as client:
        yield client


@pytest.fixture
def member_client():
    with TestClient(
        app,
        headers=_auth_headers("member", "member"),
    ) as client:
        yield client


@pytest.fixture
def org_admin_without_scope_client():
    with TestClient(
        app,
        headers=_auth_headers("org-admin", "organization_admin", organization_id=None),
    ) as client:
        yield client


@pytest.fixture
def second_org_admin_client():
    with TestClient(
        app,
        headers=_auth_headers(
            "beta-admin", "organization_admin", organization_id="org-beta"
        ),
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
    assert mock_session.providers[0].organization_id == "org-acme"

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


def test_llm_provider_member_rejected(member_client):
    response = member_client.get("/api/llm-providers")
    assert response.status_code == 403

    response = member_client.post(
        "/api/llm-providers",
        json={"name": "Malicious", "provider_type": "openai"},
    )
    assert response.status_code == 403


def test_llm_provider_org_admin_without_scope_is_rejected(
    org_admin_without_scope_client,
):
    response = org_admin_without_scope_client.get("/api/llm-providers")
    assert response.status_code == 403

    response = org_admin_without_scope_client.post(
        "/api/llm-providers",
        json={"name": "Scoped", "provider_type": "openai"},
    )
    assert response.status_code == 403


def test_llm_provider_list_is_scoped_to_requesting_organization(
    admin_client, second_org_admin_client
):
    mock_session.providers = [
        LLMProvider(
            id=1,
            name="Acme Provider",
            provider_type="openai",
            api_key="sk-acme",
            is_active=True,
            organization_id="org-acme",
            updated_at=datetime.datetime.now(datetime.timezone.utc),
        ),
        LLMProvider(
            id=2,
            name="Beta Provider",
            provider_type="anthropic",
            api_key="sk-beta",
            is_active=True,
            organization_id="org-beta",
            updated_at=datetime.datetime.now(datetime.timezone.utc),
        ),
    ]

    acme_response = admin_client.get("/api/llm-providers")
    assert acme_response.status_code == 200
    assert [provider["name"] for provider in acme_response.json()] == ["Acme Provider"]

    beta_response = second_org_admin_client.get("/api/llm-providers")
    assert beta_response.status_code == 200
    assert [provider["name"] for provider in beta_response.json()] == ["Beta Provider"]


def test_llm_provider_name_uniqueness_is_scoped_per_organization():
    unique_constraints = [
        constraint
        for constraint in LLMProvider.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        tuple(column.name for column in constraint.columns)
        == ("organization_id", "name")
        for constraint in unique_constraints
    )
    assert not any(
        tuple(column.name for column in constraint.columns) == ("name",)
        for constraint in unique_constraints
    )


def test_llm_provider_update_duplicate_name_returns_conflict(admin_client):
    mock_session.providers = [
        LLMProvider(
            id=1,
            name="Primary OpenAI",
            provider_type="openai",
            api_key="sk-primary",
            is_active=True,
            organization_id="org-acme",
            updated_at=datetime.datetime.now(datetime.timezone.utc),
        ),
        LLMProvider(
            id=2,
            name="Backup OpenAI",
            provider_type="openai",
            api_key="sk-backup",
            is_active=True,
            organization_id="org-acme",
            updated_at=datetime.datetime.now(datetime.timezone.utc),
        ),
    ]
    mock_session.commit_error = IntegrityError(
        "duplicate", params=None, orig=Exception("duplicate")
    )

    response = admin_client.put("/api/llm-providers/2", json={"name": "Primary OpenAI"})

    assert response.status_code == 409
