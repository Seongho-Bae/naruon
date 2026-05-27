import base64
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

from core.config import settings
from main import app
from api.auth import get_auth_context
from db.models import TicketTask
from db.session import get_db
from services.webdav_service import WebDavService, webdav_service

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")
TEST_SESSION_HMAC_SECRET = "webdav-knowledge-hmac-material-32-bytes"  # noqa: S105


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
        "sub": "alice",
        "role": "tenant_admin",
        "org": "org-acme",
        "groups": ["group-1", "group-2"],
        "workspace": "workspace-org-acme",
        "exp": int(time.time()) + 300,
    }
    payload.update(overrides)
    return payload

@pytest.fixture(autouse=True)
def stub_webdav_service(monkeypatch):
    async def fake_accounts(db, user_id):
        return [
            {
                "account_id": 1,
                "server_url": "https://webdav.naruon.net",
                "username": "demo_user",
            }
        ] if user_id == "alice" else []

    async def fake_folders(db, user_id):
        return [
            {"folder_id": 1, "project_name": "Naruon Roadmap 2026", "webdav_path": "/Projects/Naruon_Roadmap_2026"},
            {"folder_id": 2, "project_name": "Marketing Assets", "webdav_path": "/Projects/Marketing_Assets"}
        ] if user_id == "alice" else []

    async def fake_intent(db, user_id, target_account_id=None):
        return webdav_service.determine_webdav_writeback_intent_from_accounts(
            await fake_accounts(db, user_id),
            target_account_id=target_account_id,
        )

    async def fake_knowledge_intent(
        db,
        user_id,
        organization_id,
        source_task_id,
        target_account_id=None,
    ):
        if source_task_id == "task-email":
            return {
                "status": "error",
                "message": "Task is not self-sent knowledge.",
            }
        if source_task_id != "task-self-knowledge":
            return {
                "status": "error",
                "message": "Self-sent knowledge task was not found.",
            }
        result = await fake_intent(db, user_id, target_account_id=target_account_id)
        if result.get("status") == "error":
            return result
        return {
            **result,
            "intent": "knowledge_materialization",
            "status": "intent_ready",
            "task_id": source_task_id,
            "source_type": "self_sent_knowledge",
            "source_email_id": "<self-note@example.com>",
            "source_thread_id": "thread-self-note",
            "source_id": result["source_id"],
            "server_url": result["server_url"],
            "target_path": f"/Naruon/Notes/{source_task_id}.md",
            "requires_if_match": result["requires_if_match"],
            "provenance": result["provenance"],
            "provider_write_executed": False,
            "audit_event": "webdav.self_sent_knowledge_intent.created",
        }

    monkeypatch.setattr(webdav_service, "get_connected_accounts_from_db", fake_accounts)
    monkeypatch.setattr(webdav_service, "get_project_folders_from_db", fake_folders)
    monkeypatch.setattr(
        webdav_service,
        "determine_webdav_writeback_intent_from_db",
        fake_intent,
    )
    monkeypatch.setattr(
        webdav_service,
        "determine_knowledge_materialization_intent_from_db",
        fake_knowledge_intent,
    )

@pytest.fixture
def auth_client():
    with TestClient(
        app,
        headers={"X-User-Id": "alice", "X-Organization-Id": "org-acme"},
    ) as client:
        yield client

def test_get_webdav_accounts(auth_client):
    response = auth_client.get("/api/webdav/accounts")
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) > 0
    assert body[0]["server_url"] == "https://webdav.naruon.net"
    assert body[0]["username"] == "demo_user"

def test_get_project_folders(auth_client):
    response = auth_client.get("/api/webdav/folders")
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == 2
    assert body[0]["project_name"] == "Naruon Roadmap 2026"
    assert body[1]["project_name"] == "Marketing Assets"

def test_get_webdav_writeback_intent(auth_client):
    response = auth_client.post("/api/webdav/writeback-intent", json={})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["intent"] == "writeback"
    assert body["requires_if_match"] is True
    assert body["source_id"] == 1
    assert body["server_url"] == "https://webdav.naruon.net"
    assert body["provenance"] == "server-authoritative"


def test_get_webdav_writeback_intent_with_target_account(auth_client):
    response = auth_client.post(
        "/api/webdav/writeback-intent",
        json={"target_account_id": 1},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["intent"] == "writeback"
    assert body["source_id"] == 1
    assert body["server_url"] == "https://webdav.naruon.net"
    assert body["requires_if_match"] is True
    assert body["provenance"] == "server-authoritative"


def test_get_webdav_writeback_intent_with_invalid_target_account(auth_client):
    response = auth_client.post(
        "/api/webdav/writeback-intent",
        json={"target_account_id": 999},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Requested WebDAV account was not found."


def test_get_self_sent_knowledge_webdav_intent(auth_client):
    response = auth_client.post(
        "/api/webdav/knowledge-materialization-intent",
        json={
            "target_account_id": 1,
            "source_task_id": "task-self-knowledge",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["intent"] == "knowledge_materialization"
    assert body["status"] == "intent_ready"
    assert body["task_id"] == "task-self-knowledge"
    assert body["source_type"] == "self_sent_knowledge"
    assert body["source_email_id"] == "<self-note@example.com>"
    assert body["source_thread_id"] == "thread-self-note"
    assert body["target_path"] == "/Naruon/Notes/task-self-knowledge.md"
    assert body["provider_write_executed"] is False
    assert body["audit_event"] == "webdav.self_sent_knowledge_intent.created"
    assert "related_email_id" not in body
    assert "user_id" not in body
    assert "organization_id" not in body


def test_self_sent_knowledge_webdav_intent_requires_source_task(auth_client):
    response = auth_client.post(
        "/api/webdav/knowledge-materialization-intent",
        json={},
    )
    assert response.status_code == 422


def test_self_sent_knowledge_webdav_intent_returns_not_found_for_other_owner_task(
    auth_client,
):
    response = auth_client.post(
        "/api/webdav/knowledge-materialization-intent",
        json={"source_task_id": "task-other-owner"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Self-sent knowledge task was not found."


def test_self_sent_knowledge_webdav_intent_rejects_non_self_sent_task(auth_client):
    response = auth_client.post(
        "/api/webdav/knowledge-materialization-intent",
        json={"source_task_id": "task-email"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Task is not self-sent knowledge."


def test_self_sent_knowledge_webdav_intent_requires_connected_webdav_account():
    with TestClient(
        app,
        headers={"X-User-Id": "bob", "X-Organization-Id": "org-acme"},
    ) as client:
        response = client.post(
            "/api/webdav/knowledge-materialization-intent",
            json={"source_task_id": "task-self-knowledge"},
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "No connected WebDAV accounts found."


def test_get_self_sent_knowledge_webdav_intent_accepts_signed_bearer_session():
    previous_secret = settings.AUTH_SESSION_HMAC_SECRET
    previous_override = app.dependency_overrides.pop(get_auth_context, None)
    settings.AUTH_SESSION_HMAC_SECRET = SecretStr(TEST_SESSION_HMAC_SECRET)
    token = _signed_session_token(_valid_session_payload())
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/webdav/knowledge-materialization-intent",
                json={
                    "target_account_id": 1,
                    "source_task_id": "task-self-knowledge",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
    finally:
        settings.AUTH_SESSION_HMAC_SECRET = previous_secret
        if previous_override is not None:
            app.dependency_overrides[get_auth_context] = previous_override

    assert response.status_code == 200, response.text
    assert response.json()["task_id"] == "task-self-knowledge"


@pytest.mark.asyncio
async def test_knowledge_materialization_rejects_non_self_sent_task(monkeypatch):
    task = TicketTask(
        user_id="alice",
        organization_id="org-acme",
        title="Ordinary task",
        source_type="email",
    )
    task.task_uid = "task-email"
    task.related_thread_id = "thread-email"

    class Result:
        def one_or_none(self):
            return (task, "<email@example.com>")

    class Session:
        async def execute(self, stmt):
            return Result()

    monkeypatch.setattr(
        webdav_service,
        "get_connected_accounts_from_db",
        lambda session, user_id: [],
    )

    result = await webdav_service.determine_knowledge_materialization_intent_from_db(
        Session(),
        "alice",
        "org-acme",
        "task-email",
    )

    assert result == {
        "status": "error",
        "message": "Task is not self-sent knowledge.",
    }


def test_get_webdav_writeback_intent_no_accounts():
    with TestClient(
        app,
        headers={"X-User-Id": "bob", "X-Organization-Id": "org-acme"},
    ) as client:
        response = client.post("/api/webdav/writeback-intent", json={})
        assert response.status_code == 422
        assert response.json()["detail"] == "No connected WebDAV accounts found."


@pytest.mark.asyncio
async def test_webdav_writeback_intent_real_postgres_smoke(monkeypatch):
    account_id = 10_000 + (uuid.uuid4().int % 1_000_000)
    user_id = f"webdav-smoke-{account_id}"
    monkeypatch.setattr(
        webdav_service,
        "get_connected_accounts_from_db",
        WebDavService.get_connected_accounts_from_db.__get__(
            webdav_service,
            WebDavService,
        ),
    )
    monkeypatch.setattr(
        webdav_service,
        "determine_webdav_writeback_intent_from_db",
        WebDavService.determine_webdav_writeback_intent_from_db.__get__(
            webdav_service,
            WebDavService,
        ),
    )

    engine = create_async_engine(settings.DATABASE_URL)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS webdav_accounts (
                        account_id INTEGER PRIMARY KEY,
                        user_id VARCHAR NOT NULL,
                        server_url VARCHAR NOT NULL,
                        username VARCHAR NOT NULL,
                        credentials_encrypted VARCHAR NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
            await conn.execute(
                text(
                    """
                    DELETE FROM webdav_accounts
                    WHERE account_id = :account_id
                    """
                ),
                {"account_id": account_id},
            )
            await conn.execute(
                text(
                    """
                    INSERT INTO webdav_accounts (
                        account_id,
                        user_id,
                        server_url,
                        username,
                        credentials_encrypted
                    )
                    VALUES (
                        :account_id,
                        :user_id,
                        :server_url,
                        :username,
                        :credentials_encrypted
                    )
                    """
                ),
                {
                    "account_id": account_id,
                    "user_id": user_id,
                    "server_url": "https://real-webdav.naruon.net",
                    "username": user_id,
                    "credentials_encrypted": "test-only-placeholder",
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

    app.dependency_overrides[get_db] = override_real_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
            headers={"X-User-Id": user_id, "X-Organization-Id": "org-acme"},
        ) as client:
            response = await client.post(
                "/api/webdav/writeback-intent",
                json={"target_account_id": account_id},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM webdav_accounts WHERE account_id = :account_id"),
                {"account_id": account_id},
            )
        await engine.dispose()

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source_id"] == account_id
    assert body["server_url"] == "https://real-webdav.naruon.net"
    assert body["provenance"] == "server-authoritative"
