import base64
import datetime
import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient
from pydantic import SecretStr

from api.auth import SESSION_AUDIENCE, SESSION_ISSUER
from core.config import settings
from db.models import LLMProvider, PromptTemplate, SecurityAuditEvent
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
                [
                    prompt
                    for prompt in self.prompts
                    if prompt.created_by == owner_id or prompt.is_shared
                ]
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


def _signed_session_token(payload: dict[str, object]) -> str:
    header_segment = _base64url_encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode()
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


def _request_with_signed_session(db_session: MockSession):
    previous_secret = settings.AUTH_SESSION_HMAC_SECRET

    async def scoped_db():
        yield db_session

    settings.AUTH_SESSION_HMAC_SECRET = SecretStr(TEST_SESSION_HMAC_SECRET)
    app.dependency_overrides[get_db] = scoped_db
    try:
        token = _signed_session_token(_valid_session_payload())
        with TestClient(app) as client:
            return client.get(
                "/api/ai-hub/surface",
                headers={"Authorization": f"Bearer {token}"},
            )
    finally:
        settings.AUTH_SESSION_HMAC_SECRET = previous_secret
        app.dependency_overrides.clear()


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
    assert data["summary_cards"][0]["value_text"] == "2"
    assert data["prompt_cards"][0]["prompt_title"] == "의사결정 로그 요약"
    assert data["prompt_cards"][0]["prompt_key"].startswith("prompt_")
    assert "id" not in data["prompt_cards"][0]
    assert data["workflow_cards"][0]["state_code"] == "ready"
    assert data["agent_cards"][0]["configured"] is True
    assert data["agent_cards"][0]["state_code"] == "active"
    assert data["evaluation_metrics"][1]["score_value"] == 100
    assert data["run_events"][0]["evidence_source"] == "api.llm_providers"
    assert "credential material" not in response.text


def test_ai_hub_surface_rejects_public_identity_headers_without_signed_session():
    session = MockSession()

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

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
