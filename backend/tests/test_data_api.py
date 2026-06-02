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
from db.models import Base, ConnectorSignalEvent, ProjectFolder, WebdavAccount
from db.session import get_db
from main import app

TEST_SESSION_HMAC_SECRET = "data-quality-surface-hmac-material-32-bytes"  # noqa: S105


class MockResult:
    def __init__(self, obj):
        self.obj = obj

    def scalars(self):
        return self

    def all(self):
        return self.obj if isinstance(self.obj, list) else []

    def scalar_one(self):
        return self.obj


class MockAsyncSession:
    def __init__(self, results):
        self.results = results
        self.queries = []
        self.execute_calls = 0

    async def execute(self, query):
        self.queries.append(query)
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
        "groups": ["group-data"],
        "workspace": "workspace-org-acme",
        "exp": int(time.time()) + 300,
    }
    payload.update(overrides)
    return payload


def _now() -> datetime:
    return datetime(2026, 5, 28, 5, 45, tzinfo=timezone.utc)


def _webdav_account(source_uid: str) -> WebdavAccount:
    return WebdavAccount(
        source_uid=source_uid,
        user_id="owner",
        organization_id="org-acme",
        server_url="https://files.acme.example/dav",
        username="files@example.com",
        credentials_encrypted="credential secret",
        writeback_enabled=True,
        created_at=_now(),
    )


def _project_folder(folder_uid: str) -> ProjectFolder:
    return ProjectFolder(
        folder_uid=folder_uid,
        user_id="owner",
        organization_id="org-acme",
        project_name="Naruon Roadmap 2026",
        webdav_path="/Projects/Naruon_Roadmap_2026",
        created_at=_now(),
    )


def _connector_event(event_uid: str) -> ConnectorSignalEvent:
    return ConnectorSignalEvent(
        event_uid=event_uid,
        organization_id="org-acme",
        workspace_id="workspace-org-acme",
        signal_key="connector_heartbeat",
        state_code="heartbeat",
        detail_text="outbound connector heartbeat received",
        observed_at=_now(),
    )


@pytest.fixture
def mock_db():
    return MockAsyncSession(
        [
            [_webdav_account("webdav_src_primary")],
            [_project_folder("webdav_folder_roadmap")],
            4,
            3,
            1,
            2,
            1,
            3,
            1,
            [_connector_event("connector_evt_data_quality")],
        ]
    )


def _with_signed_auth(mock_db, token: str):
    async def override_get_db():
        yield mock_db

    previous_secret = settings.AUTH_SESSION_HMAC_SECRET
    original_overrides = dict(app.dependency_overrides)
    settings.AUTH_SESSION_HMAC_SECRET = SecretStr(TEST_SESSION_HMAC_SECRET)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_auth_context, None)
    app.dependency_overrides.pop(get_current_user, None)
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    return client, previous_secret, original_overrides


def _restore_overrides(previous_secret, original_overrides):
    settings.AUTH_SESSION_HMAC_SECRET = previous_secret
    app.dependency_overrides.clear()
    app.dependency_overrides.update(original_overrides)


def test_data_quality_surface_returns_source_backed_counts_without_secrets(mock_db):
    token = _signed_session_token(_valid_session_payload())
    client, previous_secret, original_overrides = _with_signed_auth(mock_db, token)
    try:
        response = client.get("/api/data/quality-surface")
    finally:
        client.close()
        _restore_overrides(previous_secret, original_overrides)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["audit_event"] == "data.quality_surface.viewed"
    assert data["workspace_id"] == "workspace-org-acme"
    assert data["provider_write_executed"] is False
    assert {source["source_id"] for source in data["repositories"]} == {
        "email_repository",
        "attachment_repository",
        "webdav_src_primary",
        "webdav_folder_roadmap",
    }
    assert data["pipeline_stages"][1]["detail_text"] == (
        "4 emails and 3 attachments are visible in the signed workspace scope."
    )
    assert data["embedding_collections"][0] == {
        "collection_key": "emails_embedding",
        "display_name": "Email vectors",
        "object_count": 4,
        "embedded_count": 3,
        "embedding_model": settings.OPENAI_EMBEDDING_MODEL,
        "vector_dimensions": 1536,
        "status_code": "running",
        "evidence_source": "emails.embedding",
        "provider_write_executed": False,
    }
    quality_by_key = {check["check_key"]: check for check in data["quality_checks"]}
    assert quality_by_key["thread_id_integrity"]["issue_count"] == 1
    assert quality_by_key["dedupe_fingerprint"]["issue_count"] == 2
    assert quality_by_key["attachment_content"]["issue_count"] == 1
    assert data["connector_events"][0]["event_uid"] == "connector_evt_data_quality"

    serialized = response.text
    for forbidden in (
        "account_id",
        "folder_id",
        "credentials_encrypted",
        "credential secret",
        "username",
        "files@example.com",
        "https://files.acme.example",
        "webdav_path",
        "/Projects/Naruon_Roadmap_2026",
    ):
        assert forbidden not in serialized


def test_data_quality_surface_rejects_public_identity_headers_without_signed_session(
    mock_db,
):
    async def override_get_db():
        yield mock_db

    original_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_auth_context, None)
    app.dependency_overrides.pop(get_current_user, None)
    try:
        with TestClient(app) as client:
            response = client.get(
                "/api/data/quality-surface",
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


def test_member_data_quality_queries_are_owner_scoped(mock_db):
    token = _signed_session_token(
        _valid_session_payload(sub="member", role="member", workspace="workspace-member")
    )
    client, previous_secret, original_overrides = _with_signed_auth(mock_db, token)
    try:
        response = client.get("/api/data/quality-surface")
    finally:
        client.close()
        _restore_overrides(previous_secret, original_overrides)

    assert response.status_code == 200, response.text
    rendered_queries = "\n".join(str(query) for query in mock_db.queries)
    assert "webdav_accounts.user_id = :user_id_1" in rendered_queries
    assert "project_folders.user_id = :user_id_1" in rendered_queries
    assert "emails.user_id = :user_id_1" in rendered_queries


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_data_quality_surface_real_postgres_smoke_uses_signed_scope():
    user_id = f"data_smoke_user_{uuid.uuid4().hex[:12]}"
    organization_id = f"data_smoke_org_{uuid.uuid4().hex[:12]}"
    workspace_id = f"workspace_{organization_id}"
    rival_user_id = f"data_rival_user_{uuid.uuid4().hex[:12]}"
    rival_organization_id = f"data_rival_org_{uuid.uuid4().hex[:12]}"
    webdav_uid = f"webdav_src_data_{uuid.uuid4().hex[:18]}"
    rival_webdav_uid = f"webdav_src_data_rival_{uuid.uuid4().hex[:12]}"
    folder_uid = f"webdav_folder_data_{uuid.uuid4().hex[:18]}"
    event_uid = f"connector_evt_data_{uuid.uuid4().hex[:18]}"
    other_workspace_event_uid = f"connector_evt_other_{uuid.uuid4().hex[:18]}"
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)
            first_email = await conn.execute(
                text(
                    """
                    INSERT INTO emails (
                        user_id, organization_id, message_id, thread_id,
                        fingerprint, sender, recipients, subject, "date", body
                    )
                    VALUES (
                        :user_id, :organization_id, :message_id, :thread_id,
                        :fingerprint, :sender, :recipients, :subject, now(), :body
                    )
                    RETURNING id
                    """
                ),
                {
                    "user_id": user_id,
                    "organization_id": organization_id,
                    "message_id": f"<data-smoke-{uuid.uuid4().hex}@example.com>",
                    "thread_id": "thread-data-smoke",
                    "fingerprint": "sha256:data-smoke",
                    "sender": "partner@example.com",
                    "recipients": "owner@example.com",
                    "subject": "Data smoke ready",
                    "body": "ready body",
                },
            )
            second_email = await conn.execute(
                text(
                    """
                    INSERT INTO emails (
                        user_id, organization_id, message_id, sender, recipients,
                        subject, "date", body
                    )
                    VALUES (
                        :user_id, :organization_id, :message_id, :sender,
                        :recipients, :subject, now(), :body
                    )
                    RETURNING id
                    """
                ),
                {
                    "user_id": user_id,
                    "organization_id": organization_id,
                    "message_id": f"<data-smoke-missing-{uuid.uuid4().hex}@example.com>",
                    "sender": "partner@example.com",
                    "recipients": "owner@example.com",
                    "subject": "Data smoke missing",
                    "body": "missing body",
                },
            )
            rival_email = await conn.execute(
                text(
                    """
                    INSERT INTO emails (
                        user_id, organization_id, message_id, thread_id,
                        fingerprint, sender, recipients, subject, "date", body
                    )
                    VALUES (
                        :user_id, :organization_id, :message_id, :thread_id,
                        :fingerprint, :sender, :recipients, :subject, now(), :body
                    )
                    RETURNING id
                    """
                ),
                {
                    "user_id": rival_user_id,
                    "organization_id": rival_organization_id,
                    "message_id": f"<data-rival-{uuid.uuid4().hex}@example.com>",
                    "thread_id": "thread-rival",
                    "fingerprint": "sha256:rival",
                    "sender": "rival@example.com",
                    "recipients": "rival@example.com",
                    "subject": "Rival",
                    "body": "rival body",
                },
            )
            first_email_id = first_email.scalar_one()
            second_email_id = second_email.scalar_one()
            rival_email_id = rival_email.scalar_one()
            await conn.execute(
                text(
                    """
                    INSERT INTO attachments (email_id, filename, content)
                    VALUES
                    (:first_email_id, 'ready.txt', 'ready attachment'),
                    (:second_email_id, 'blank.txt', ''),
                    (:rival_email_id, 'rival.txt', 'rival attachment')
                    """
                ),
                {
                    "first_email_id": first_email_id,
                    "second_email_id": second_email_id,
                    "rival_email_id": rival_email_id,
                },
            )
            await conn.execute(
                text(
                    """
                    INSERT INTO webdav_accounts (
                        source_uid, user_id, organization_id, server_url, username,
                        credentials_encrypted, writeback_enabled
                    )
                    VALUES
                    (
                        :webdav_uid, :user_id, :organization_id,
                        'https://data-files.example/dav', 'data@example.com',
                        'encrypted-data-secret', true
                    ),
                    (
                        :rival_webdav_uid, :rival_user_id, :rival_organization_id,
                        'https://rival-files.example/dav', 'rival@example.com',
                        'encrypted-rival-secret', true
                    )
                    """
                ),
                {
                    "webdav_uid": webdav_uid,
                    "user_id": user_id,
                    "organization_id": organization_id,
                    "rival_webdav_uid": rival_webdav_uid,
                    "rival_user_id": rival_user_id,
                    "rival_organization_id": rival_organization_id,
                },
            )
            await conn.execute(
                text(
                    """
                    INSERT INTO project_folders (
                        folder_uid, user_id, organization_id, project_name,
                        webdav_path
                    )
                    VALUES (
                        :folder_uid, :user_id, :organization_id,
                        'Data Smoke Folder', '/Projects/Data_Smoke'
                    )
                    """
                ),
                {
                    "folder_uid": folder_uid,
                    "user_id": user_id,
                    "organization_id": organization_id,
                },
            )
            await conn.execute(
                text(
                    """
                    INSERT INTO connector_signal_events (
                        event_uid, organization_id, workspace_id, signal_key,
                        state_code, detail_text
                    )
                    VALUES
                    (
                        :event_uid, :organization_id, :workspace_id,
                        'connector_heartbeat', 'heartbeat',
                        'data smoke heartbeat'
                    ),
                    (
                        :other_workspace_event_uid, :organization_id,
                        'other_workspace', 'connector_heartbeat', 'heartbeat',
                        'other workspace heartbeat'
                    )
                    """
                ),
                {
                    "event_uid": event_uid,
                    "other_workspace_event_uid": other_workspace_event_uid,
                    "organization_id": organization_id,
                    "workspace_id": workspace_id,
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
        _valid_session_payload(
            sub=user_id,
            org=organization_id,
            workspace=workspace_id,
        )
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
            response = await client.get("/api/data/quality-surface")
    finally:
        settings.AUTH_SESSION_HMAC_SECRET = previous_secret
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    DELETE FROM attachments
                    WHERE email_id IN (
                        SELECT id FROM emails
                        WHERE user_id IN (:user_id, :rival_user_id)
                    )
                    """
                ),
                {"user_id": user_id, "rival_user_id": rival_user_id},
            )
            await conn.execute(
                text(
                    "DELETE FROM emails WHERE user_id IN (:user_id, :rival_user_id)"
                ),
                {"user_id": user_id, "rival_user_id": rival_user_id},
            )
            await conn.execute(
                text(
                    "DELETE FROM webdav_accounts "
                    "WHERE source_uid IN (:webdav_uid, :rival_webdav_uid)"
                ),
                {
                    "webdav_uid": webdav_uid,
                    "rival_webdav_uid": rival_webdav_uid,
                },
            )
            await conn.execute(
                text("DELETE FROM project_folders WHERE folder_uid = :folder_uid"),
                {"folder_uid": folder_uid},
            )
            await conn.execute(
                text(
                    "DELETE FROM connector_signal_events "
                    "WHERE event_uid IN (:event_uid, :other_workspace_event_uid)"
                ),
                {
                    "event_uid": event_uid,
                    "other_workspace_event_uid": other_workspace_event_uid,
                },
            )
        await engine.dispose()

    assert response.status_code == 200, response.text
    data = response.json()
    source_ids = {source["source_id"] for source in data["repositories"]}
    assert webdav_uid in source_ids
    assert folder_uid in source_ids
    assert rival_webdav_uid not in response.text
    quality_by_key = {check["check_key"]: check for check in data["quality_checks"]}
    assert quality_by_key["thread_id_integrity"]["issue_count"] == 1
    assert quality_by_key["dedupe_fingerprint"]["issue_count"] == 1
    assert quality_by_key["attachment_content"]["issue_count"] == 1
    assert event_uid in {event["event_uid"] for event in data["connector_events"]}
    assert other_workspace_event_uid not in response.text
    assert "account_id" not in response.text
    assert "encrypted-data-secret" not in response.text
    assert "data@example.com" not in response.text
