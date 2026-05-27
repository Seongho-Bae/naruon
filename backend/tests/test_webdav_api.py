import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.config import settings
from main import app
from db.session import get_db
from services.webdav_service import WebDavService, webdav_service

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")

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

    monkeypatch.setattr(webdav_service, "get_connected_accounts_from_db", fake_accounts)
    monkeypatch.setattr(webdav_service, "get_project_folders_from_db", fake_folders)
    monkeypatch.setattr(
        webdav_service,
        "determine_webdav_writeback_intent_from_db",
        fake_intent,
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
                    WHERE account_id = :account_id OR user_id = :user_id
                    """
                ),
                {"account_id": 8871, "user_id": "alice"},
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
                    "account_id": 8871,
                    "user_id": "alice",
                    "server_url": "https://real-webdav.naruon.net",
                    "username": "alice",
                    "credentials_encrypted": "test-only-placeholder",
                },
            )
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"PostgreSQL smoke path unavailable: {exc}")

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
            headers={"X-User-Id": "alice", "X-Organization-Id": "org-acme"},
        ) as client:
            response = await client.post(
                "/api/webdav/writeback-intent",
                json={"target_account_id": 8871},
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM webdav_accounts WHERE account_id = :account_id"),
                {"account_id": 8871},
            )
        await engine.dispose()

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source_id"] == 8871
    assert body["server_url"] == "https://real-webdav.naruon.net"
    assert body["provenance"] == "server-authoritative"
