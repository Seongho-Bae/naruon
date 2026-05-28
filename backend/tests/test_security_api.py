import base64
from datetime import datetime, timezone
import hashlib
import hmac
import json
import time
import uuid

import asyncpg
from fastapi.testclient import TestClient
import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from api.auth import get_auth_context, get_current_user
from core.config import settings
from db.models import (
    CalendarWritebackSource,
    ConnectorSignalEvent,
    SecurityAuditEvent,
    WebdavAccount,
)
from db.session import get_db
from main import app

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")
TEST_SESSION_HMAC_SECRET = "security-governance-hmac-material-32-bytes"  # noqa: S105


class MockResult:
    def __init__(self, obj):
        self.obj = obj

    def scalars(self):
        return self

    def all(self):
        return self.obj if isinstance(self.obj, list) else []


class MockAsyncSession:
    def __init__(
        self,
        webdav_accounts: list[WebdavAccount] | None = None,
        calendar_sources: list[CalendarWritebackSource] | None = None,
        audit_events: list[SecurityAuditEvent] | None = None,
        connector_events: list[ConnectorSignalEvent] | None = None,
    ):
        self.results = [
            webdav_accounts or [],
            calendar_sources or [],
            audit_events or [],
            connector_events or [],
        ]
        self.execute_calls = 0

    async def execute(self, query):
        del query
        result = self.results[self.execute_calls]
        self.execute_calls += 1
        return MockResult(result)


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


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
        "iss": "naruon-control-plane",
        "aud": "naruon-api",
        "sub": "admin",
        "role": "tenant_admin",
        "org": "org-acme",
        "groups": ["group-security"],
        "workspace": "workspace-org-acme",
        "exp": int(time.time()) + 300,
    }
    payload.update(overrides)
    return payload


def _now() -> datetime:
    return datetime(2026, 5, 28, 4, 0, tzinfo=timezone.utc)


def _webdav_account(
    source_uid: str,
    user_id: str,
    organization_id: str | None = "org-acme",
) -> WebdavAccount:
    return WebdavAccount(
        source_uid=source_uid,
        user_id=user_id,
        organization_id=organization_id,
        server_url="https://files.acme.example/dav",
        username="files@example.com",
        credentials_encrypted="credential secret",
        writeback_enabled=True,
        created_at=_now(),
    )


def _calendar_source(
    source_uid: str,
    user_id: str,
    organization_id: str | None = "org-acme",
) -> CalendarWritebackSource:
    return CalendarWritebackSource(
        source_uid=source_uid,
        user_id=user_id,
        organization_id=organization_id,
        workspace_id="workspace-org-acme",
        account_ref="caldav-account-ref",
        provider_name="Customer CalDAV",
        source_protocol="caldav",
        source_host="calendar.acme.example",
        writeback_enabled=True,
        etag_value="etag-caldav-primary",
        created_at=_now(),
    )


def _connector_event(
    event_uid: str,
    organization_id: str = "org-acme",
    workspace_id: str = "workspace-org-acme",
) -> ConnectorSignalEvent:
    return ConnectorSignalEvent(
        event_uid=event_uid,
        organization_id=organization_id,
        workspace_id=workspace_id,
        signal_key="connector_heartbeat",
        state_code="heartbeat",
        detail_text="outbound connector heartbeat",
        observed_at=_now(),
    )


def _audit_event(
    event_uid: str,
    actor_user_id: str = "admin",
    organization_id: str | None = "org-acme",
    workspace_id: str = "workspace-org-acme",
) -> SecurityAuditEvent:
    return SecurityAuditEvent(
        event_uid=event_uid,
        actor_user_id=actor_user_id,
        actor_role="tenant_admin",
        organization_id=organization_id,
        workspace_id=workspace_id,
        event_action="update",
        resource_type="llm_provider",
        resource_uid="llm_provider:provider_primary",
        evidence_source="api.llm_providers",
        detail_text="Updated provider configuration",
        observed_at=_now(),
    )


@pytest.fixture
def mock_db():
    return MockAsyncSession(
        webdav_accounts=[
            _webdav_account("webdav_src_org_primary", "owner"),
            _webdav_account("webdav_src_other_org", "owner", "org-rival"),
        ],
        calendar_sources=[
            _calendar_source("caldav_src_primary", "owner"),
            _calendar_source("caldav_src_other_org", "owner", "org-rival"),
        ],
        audit_events=[
            _audit_event("audit_evt_provider_update"),
            _audit_event("audit_evt_other_org", organization_id="org-rival"),
        ],
        connector_events=[
            _connector_event("connector_evt_heartbeat"),
            _connector_event("connector_evt_other_org", "org-rival"),
        ],
    )


@pytest.fixture
def admin_client(mock_db):
    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            headers={
                "X-User-Id": "admin",
                "X-User-Role": "tenant_admin",
                "X-Organization-Id": "org-acme",
            },
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_access_surface_returns_org_scoped_sources_and_policy_decisions(admin_client):
    response = admin_client.get("/api/security/access-surface")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["audit_event"] == "security.access_surface.viewed"
    assert data["viewer"]["role"] == "tenant_admin"
    source_ids = {source["source_id"] for source in data["sources"]}
    assert source_ids == {"webdav_src_org_primary", "caldav_src_primary"}
    assert "webdav_src_other_org" not in response.text
    assert "caldav_src_other_org" not in response.text
    assert data["connector_events"][0]["event_uid"] == "connector_evt_heartbeat"
    assert "connector_evt_other_org" not in response.text
    audit_event_ids = {event["event_uid"] for event in data["durable_audit_events"]}
    assert audit_event_ids == {"audit_evt_provider_update"}
    assert "audit_evt_other_org" not in response.text
    assert data["durable_audit_events"][0]["workspace_id"] == "workspace-org-acme"
    reasons = {decision["reason"] for decision in data["policy_decisions"]}
    assert "organization_denied" in reasons
    assert "data_region_denied" in reasons
    assert "allowed" in reasons


def test_access_surface_redacts_sequential_ids_and_credentials(admin_client):
    response = admin_client.get("/api/security/access-surface")

    assert response.status_code == 200, response.text
    serialized = response.text
    for forbidden in (
        "account_id",
        "credentials_encrypted",
        "credential secret",
        "username",
        "files@example.com",
        "api_key",
        "sk-",
        "audit_id",
    ):
        assert forbidden not in serialized


def test_member_surface_only_returns_owned_sources(mock_db):
    async def override_get_db():
        yield MockAsyncSession(
            webdav_accounts=[
                _webdav_account("webdav_src_owned", "member"),
                _webdav_account("webdav_src_admin", "admin"),
            ],
            calendar_sources=[
                _calendar_source("caldav_src_owned", "member"),
                _calendar_source("caldav_src_admin", "admin"),
            ],
            audit_events=[
                _audit_event("audit_evt_member", actor_user_id="member"),
                _audit_event("audit_evt_admin", actor_user_id="admin"),
            ],
            connector_events=[],
        )

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            headers={
                "X-User-Id": "member",
                "X-User-Role": "member",
                "X-Organization-Id": "org-acme",
            },
        ) as client:
            response = client.get("/api/security/access-surface")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200, response.text
    source_ids = {source["source_id"] for source in response.json()["sources"]}
    assert source_ids == {"webdav_src_owned", "caldav_src_owned"}
    audit_event_ids = {
        event["event_uid"] for event in response.json()["durable_audit_events"]
    }
    assert audit_event_ids == {"audit_evt_member"}


def test_access_surface_rejects_public_identity_headers_without_signed_session(mock_db):
    async def override_get_db():
        yield mock_db

    original_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_auth_context, None)
    app.dependency_overrides.pop(get_current_user, None)
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/security/access-surface",
                headers={
                    "X-User-Id": "admin",
                    "X-User-Role": "tenant_admin",
                    "X-Organization-Id": "org-acme",
                },
            )
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_access_surface_accepts_signed_bearer_session(mock_db):
    async def override_get_db():
        yield mock_db

    previous_secret = settings.AUTH_SESSION_HMAC_SECRET
    original_overrides = dict(app.dependency_overrides)
    settings.AUTH_SESSION_HMAC_SECRET = SecretStr(TEST_SESSION_HMAC_SECRET)
    token = _signed_session_token(_valid_session_payload())
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_auth_context, None)
    app.dependency_overrides.pop(get_current_user, None)
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/security/access-surface",
                headers={"Authorization": f"Bearer {token}"},
            )
    finally:
        settings.AUTH_SESSION_HMAC_SECRET = previous_secret
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

    assert response.status_code == 200, response.text
    assert response.json()["viewer"]["user_id"] == "admin"


@pytest.mark.asyncio
async def test_access_surface_real_postgres_smoke_uses_scoped_sources():
    user_id = f"security_smoke_user_{uuid.uuid4().hex[:12]}"
    source_uid = f"webdav_src_security_{uuid.uuid4().hex[:18]}"
    caldav_uid = f"caldav_src_security_{uuid.uuid4().hex[:18]}"
    event_uid = f"connector_evt_security_{uuid.uuid4().hex[:18]}"
    audit_uid = f"audit_evt_security_{uuid.uuid4().hex[:18]}"
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    INSERT INTO webdav_accounts (
                        source_uid,
                        user_id,
                        organization_id,
                        server_url,
                        username,
                        credentials_encrypted,
                        writeback_enabled
                    )
                    VALUES (
                        :source_uid,
                        :user_id,
                        :organization_id,
                        :server_url,
                        :username,
                        :credentials_encrypted,
                        :writeback_enabled
                    )
                    """
                ),
                {
                    "source_uid": source_uid,
                    "user_id": user_id,
                    "organization_id": "org-acme",
                    "server_url": "https://security-files.example/dav",
                    "username": "security-smoke@example.com",
                    "credentials_encrypted": "test-only-placeholder",
                    "writeback_enabled": True,
                },
            )
            await conn.execute(
                text(
                    """
                    INSERT INTO calendar_writeback_sources (
                        source_uid,
                        user_id,
                        organization_id,
                        workspace_id,
                        account_ref,
                        provider_name,
                        source_protocol,
                        source_host,
                        writeback_enabled,
                        etag_value
                    )
                    VALUES (
                        :source_uid,
                        :user_id,
                        :organization_id,
                        :workspace_id,
                        :account_ref,
                        :provider_name,
                        :source_protocol,
                        :source_host,
                        :writeback_enabled,
                        :etag_value
                    )
                    """
                ),
                {
                    "source_uid": caldav_uid,
                    "user_id": user_id,
                    "organization_id": "org-acme",
                    "workspace_id": "workspace-org-acme",
                    "account_ref": "security-smoke-account",
                    "provider_name": "Security Smoke CalDAV",
                    "source_protocol": "caldav",
                    "source_host": "security-caldav.example",
                    "writeback_enabled": True,
                    "etag_value": "etag-security-smoke",
                },
            )
            await conn.execute(
                text(
                    """
                    INSERT INTO connector_signal_events (
                        event_uid,
                        organization_id,
                        workspace_id,
                        signal_key,
                        state_code,
                        detail_text
                    )
                    VALUES (
                        :event_uid,
                        :organization_id,
                        :workspace_id,
                        :signal_key,
                        :state_code,
                        :detail_text
                    )
                    """
                ),
                {
                    "event_uid": event_uid,
                    "organization_id": "org-acme",
                    "workspace_id": "workspace-org-acme",
                    "signal_key": "connector_heartbeat",
                    "state_code": "heartbeat",
                    "detail_text": "security smoke connector heartbeat",
                },
            )
            await conn.execute(
                text(
                    """
                    INSERT INTO security_audit_events (
                        event_uid,
                        actor_user_id,
                        actor_role,
                        organization_id,
                        workspace_id,
                        event_action,
                        resource_type,
                        resource_uid,
                        evidence_source,
                        detail_text
                    )
                    VALUES (
                        :event_uid,
                        :actor_user_id,
                        :actor_role,
                        :organization_id,
                        :workspace_id,
                        :event_action,
                        :resource_type,
                        :resource_uid,
                        :evidence_source,
                        :detail_text
                    )
                    """
                ),
                {
                    "event_uid": audit_uid,
                    "actor_user_id": user_id,
                    "actor_role": "tenant_admin",
                    "organization_id": "org-acme",
                    "workspace_id": "workspace-org-acme",
                    "event_action": "update",
                    "resource_type": "llm_provider",
                    "resource_uid": "llm_provider:security_smoke",
                    "evidence_source": "api.llm_providers",
                    "detail_text": "Updated provider configuration",
                },
            )
    except (
        ConnectionRefusedError,
        OSError,
        OperationalError,
        asyncpg.CannotConnectNowError,
        asyncpg.InvalidAuthorizationSpecificationError,
        asyncpg.InvalidCatalogNameError,
        asyncpg.InvalidPasswordError,
    ):
        await engine.dispose()
        pytest.skip("PostgreSQL smoke path unavailable")
    except Exception:
        await engine.dispose()
        raise

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_real_db():
        async with session_factory() as session:
            yield session

    previous_secret = settings.AUTH_SESSION_HMAC_SECRET
    original_overrides = dict(app.dependency_overrides)
    settings.AUTH_SESSION_HMAC_SECRET = SecretStr(TEST_SESSION_HMAC_SECRET)
    token = _signed_session_token(
        _valid_session_payload(sub=user_id, workspace="workspace-org-acme")
    )
    app.dependency_overrides[get_db] = override_real_db
    app.dependency_overrides.pop(get_auth_context, None)
    app.dependency_overrides.pop(get_current_user, None)
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.get("/api/security/access-surface")
    finally:
        settings.AUTH_SESSION_HMAC_SECRET = previous_secret
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM webdav_accounts WHERE source_uid = :source_uid"),
                {"source_uid": source_uid},
            )
            await conn.execute(
                text(
                    "DELETE FROM calendar_writeback_sources "
                    "WHERE source_uid = :source_uid"
                ),
                {"source_uid": caldav_uid},
            )
            await conn.execute(
                text(
                    "DELETE FROM connector_signal_events "
                    "WHERE event_uid = :event_uid"
                ),
                {"event_uid": event_uid},
            )
            await conn.execute(
                text(
                    "DELETE FROM security_audit_events "
                    "WHERE event_uid = :event_uid"
                ),
                {"event_uid": audit_uid},
            )
        await engine.dispose()

    assert response.status_code == 200, response.text
    body = response.json()
    source_ids = {source["source_id"] for source in body["sources"]}
    assert source_uid in source_ids
    assert caldav_uid in source_ids
    assert event_uid in {event["event_uid"] for event in body["connector_events"]}
    assert audit_uid in {
        event["event_uid"] for event in body["durable_audit_events"]
    }
    assert "account_id" not in response.text
    assert "security-smoke@example.com" not in response.text
