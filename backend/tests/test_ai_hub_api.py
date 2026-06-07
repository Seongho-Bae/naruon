import base64
import datetime
import hashlib
import hmac
import json
import time
import uuid

import asyncpg
import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from api.auth import SESSION_AUDIENCE, SESSION_ISSUER
from core.config import settings
from db.models import Base, LLMProvider, PromptTemplate, SecurityAuditEvent
from db.session import get_db
from main import app

TEST_SESSION_HMAC_SECRET = "ai-hub-surface-hmac-value-20260529-32"  # noqa: S105


class MockScalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class MockResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return MockScalars(self._rows)


class MockSession:
    def __init__(self):
        self.prompts: list[PromptTemplate] = []
        self.providers: list[LLMProvider] = []
        self.audit_events: list[SecurityAuditEvent] = []

    async def execute(self, stmt):
        descriptions = getattr(stmt, "column_descriptions", [])
        entity = descriptions[0].get("entity") if descriptions else None
        params = stmt.compile().params
        if entity is PromptTemplate:
            owner_id = params.get("created_by_1")
            return MockResult(
                [prompt for prompt in self.prompts if prompt.created_by == owner_id]
            )
        if entity is LLMProvider:
            organization_id = params.get("organization_id_1")
            return MockResult(
                [
                    provider
                    for provider in self.providers
                    if provider.organization_id == organization_id
                ]
            )
        if entity is SecurityAuditEvent:
            organization_id = params.get("organization_id_1")
            workspace_id = params.get("workspace_id_1")
            actor_user_id = params.get("actor_user_id_1")
            rows = [
                event
                for event in self.audit_events
                if event.organization_id == organization_id
                and event.workspace_id == workspace_id
                and event.resource_type == "llm_provider"
            ]
            if actor_user_id:
                rows = [event for event in rows if event.actor_user_id == actor_user_id]
            return MockResult(rows)
        return MockResult([])


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _signed_session_token(
    payload: dict[str, object],
    *,
    header: dict[str, object] | None = None,
) -> str:
    header_segment = _base64url_encode(
        json.dumps(
            header or {"alg": "HS256", "typ": "JWT"},
            separators=(",", ":"),
        ).encode()
    )
    payload_segment = _base64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    )
    signing_input = f"{header_segment}.{payload_segment}"
    signature = hmac.new(
        TEST_SESSION_HMAC_SECRET.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_base64url_encode(signature)}"


def _valid_session_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "ver": 1,
        "iss": SESSION_ISSUER,
        "aud": SESSION_AUDIENCE,
        "sub": "alice",
        "role": "tenant_admin",
        "org": "org-acme",
        "groups": ["group-ai"],
        "workspace": "workspace-org-acme",
        "exp": int(time.time()) + 300,
    }
    payload.update(overrides)
    return payload


def _now() -> datetime.datetime:
    return datetime.datetime(2026, 5, 29, 9, 30, tzinfo=datetime.timezone.utc)


def _prompt(prompt_id: int, title: str, owner_id: str = "alice") -> PromptTemplate:
    prompt = PromptTemplate(
        title=title,
        description="메일에서 판단 포인트를 추출합니다.",
        content="Summarize {{email}}",
        is_shared=False,
        created_by=owner_id,
    )
    prompt.id = prompt_id
    prompt.created_at = _now()
    prompt.updated_at = _now()
    return prompt


def _provider(provider_id: int, *, active: bool = True) -> LLMProvider:
    provider = LLMProvider(
        user_id="alice",
        organization_id="org-acme",
        name="Primary OpenAI",
        provider_type="openai",
        api_key="credential material",
        is_active=active,
    )
    provider.id = provider_id
    provider.updated_at = _now()
    return provider


def _audit_event() -> SecurityAuditEvent:
    return SecurityAuditEvent(
        event_uid="audit_evt_provider_update",
        actor_user_id="alice",
        actor_role="tenant_admin",
        organization_id="org-acme",
        workspace_id="workspace-org-acme",
        event_action="update",
        resource_type="llm_provider",
        resource_uid="llm_provider:abc123",
        evidence_source="api.llm_providers",
        detail_text="Updated provider configuration",
        observed_at=_now(),
    )


def _request_with_signed_session(
    db_session: MockSession,
    header: dict[str, object] | None = None,
    **payload_overrides: object,
):
    previous_secret = settings.AUTH_SESSION_HMAC_SECRET
    original_overrides = dict(app.dependency_overrides)

    async def scoped_db():
        yield db_session

    settings.AUTH_SESSION_HMAC_SECRET = SecretStr(TEST_SESSION_HMAC_SECRET)
    app.dependency_overrides[get_db] = scoped_db
    try:
        token = _signed_session_token(
            _valid_session_payload(**payload_overrides),
            header=header,
        )
        with TestClient(app) as client:
            return client.get(
                "/api/ai-hub/surface",
                headers={"Authorization": f"Bearer {token}"},
            )
    finally:
        settings.AUTH_SESSION_HMAC_SECRET = previous_secret
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)


def test_ai_hub_surface_uses_signed_source_evidence():
    session = MockSession()
    session.prompts = [
        _prompt(1, "의사결정 로그 요약"),
        _prompt(2, "공유 프롬프트", owner_id="other-user"),
    ]
    session.prompts[1].is_shared = True
    session.providers = [_provider(1)]
    session.audit_events = [_audit_event()]

    response = _request_with_signed_session(session)

    assert response.status_code == 200
    data = response.json()
    assert data["summary_cards"][0]["value_text"] == "1"
    assert data["prompt_cards"][0]["prompt_title"] == "의사결정 로그 요약"
    assert all(card["owner_label"] == "alice" for card in data["prompt_cards"])
    assert data["prompt_cards"][0]["prompt_key"].startswith("prompt_")
    assert "id" not in data["prompt_cards"][0]
    assert data["workflow_cards"][0]["state_code"] == "ready"
    assert data["agent_cards"][0]["configured"] is True
    assert data["agent_cards"][0]["state_code"] == "active"
    assert data["evaluation_metrics"][1]["score_value"] == 100
    assert data["run_events"][0]["evidence_source"] == "api.llm_providers"
    assert "credential material" not in response.text


def test_ai_hub_surface_hides_provider_metadata_for_members():
    session = MockSession()
    session.prompts = [_prompt(1, "멤버 프롬프트")]
    session.providers = [_provider(1)]

    response = _request_with_signed_session(session, role="member")

    assert response.status_code == 200
    data = response.json()
    assert data["prompt_cards"][0]["prompt_title"] == "멤버 프롬프트"
    assert data["agent_cards"] == []
    assert data["summary_cards"][2]["value_text"] == "0/0"


def test_ai_hub_surface_rejects_public_identity_headers_without_signed_session():
    session = MockSession()
    original_overrides = dict(app.dependency_overrides)

    async def scoped_db():
        yield session

    app.dependency_overrides[get_db] = scoped_db
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get(
                "/api/ai-hub/surface",
                headers={
                    "X-User-Id": "alice",
                    "X-User-Role": "tenant_admin",
                    "X-Organization-Id": "org-acme",
                },
            )
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_ai_hub_surface_rejects_unsupported_signed_session_crit_header():
    session = MockSession()

    response = _request_with_signed_session(
        session,
        header={
            "alg": "HS256",
            "typ": "JWT",
            "crit": ["x-custom-policy"],
            "x-custom-policy": "require-mfa",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_ai_hub_surface_postgres_smoke_uses_signed_scope():
    database_url = getattr(settings, "DATABASE_URL", None)
    if not database_url:
        pytest.skip("PostgreSQL smoke path unavailable: DATABASE_URL is not set")

    user_id = f"ai_hub_user_{uuid.uuid4().hex[:12]}"
    organization_id = f"ai_hub_org_{uuid.uuid4().hex[:12]}"
    workspace_id = f"workspace_{organization_id}"
    event_uid = f"audit_evt_ai_hub_{uuid.uuid4().hex[:18]}"
    engine = create_async_engine(database_url, echo=False)
    session_factory = None
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            prompt = PromptTemplate(
                title="Postgres AI Hub prompt",
                description="source-backed postgres smoke prompt",
                content="Summarize {{email}}",
                is_shared=False,
                created_by=user_id,
            )
            provider = LLMProvider(
                user_id=user_id,
                organization_id=organization_id,
                name="Postgres Provider",
                provider_type="openai",
                api_key=None,
                is_active=True,
            )
            audit_event = SecurityAuditEvent(
                event_uid=event_uid,
                actor_user_id=user_id,
                actor_role="tenant_admin",
                organization_id=organization_id,
                workspace_id=workspace_id,
                event_action="update",
                resource_type="llm_provider",
                resource_uid="llm_provider:postgres",
                evidence_source="api.llm_providers",
                detail_text="Postgres provider evidence",
                observed_at=_now(),
            )
            session.add_all([prompt, provider, audit_event])
            await session.commit()
    except (
        ConnectionRefusedError,
        OSError,
        OperationalError,
        asyncpg.CannotConnectNowError,
        asyncpg.InvalidAuthorizationSpecificationError,
        asyncpg.InvalidCatalogNameError,
        asyncpg.InvalidPasswordError,
    ) as exc:
        await engine.dispose()
        pytest.skip(f"PostgreSQL smoke path unavailable: {exc}")
    except Exception:
        await engine.dispose()
        raise

    assert session_factory is not None

    async def override_real_db():
        async with session_factory() as session:
            yield session

    previous_secret = settings.AUTH_SESSION_HMAC_SECRET
    original_overrides = dict(app.dependency_overrides)
    settings.AUTH_SESSION_HMAC_SECRET = SecretStr(TEST_SESSION_HMAC_SECRET)
    token = _signed_session_token(
        _valid_session_payload(
            sub=user_id,
            org=organization_id,
            workspace=workspace_id,
        )
    )
    app.dependency_overrides[get_db] = override_real_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.get("/api/ai-hub/surface")
    finally:
        settings.AUTH_SESSION_HMAC_SECRET = previous_secret
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM security_audit_events WHERE event_uid = :event_uid"),
                {"event_uid": event_uid},
            )
            await conn.execute(
                text(
                    """
                    DELETE FROM llm_providers
                    WHERE user_id = :user_id AND organization_id = :organization_id
                    """
                ),
                {"user_id": user_id, "organization_id": organization_id},
            )
            await conn.execute(
                text("DELETE FROM prompt_templates WHERE created_by = :user_id"),
                {"user_id": user_id},
            )
        await engine.dispose()

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["prompt_cards"][0]["prompt_title"] == "Postgres AI Hub prompt"
    assert data["agent_cards"][0]["agent_title"] == "Postgres Provider"
    assert data["agent_cards"][0]["configured"] is False
    assert data["run_events"][0]["evidence_source"] == "api.llm_providers"
