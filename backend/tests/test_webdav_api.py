import pytest
from fastapi.testclient import TestClient
from main import app
from db.session import get_db
from services.webdav_service import webdav_service

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")

@pytest.fixture(autouse=True)
def stub_webdav_service(monkeypatch):
    monkeypatch.setattr(
        webdav_service,
        "get_connected_accounts",
        lambda user_id: [{"account_id": 1, "server_url": "https://webdav.naruon.net", "username": "demo_user"}] if user_id == "alice" else [],
    )
    monkeypatch.setattr(
        webdav_service,
        "get_project_folders",
        lambda user_id: [
            {"folder_id": 1, "project_name": "Naruon Roadmap 2026", "webdav_path": "/Projects/Naruon_Roadmap_2026"},
            {"folder_id": 2, "project_name": "Marketing Assets", "webdav_path": "/Projects/Marketing_Assets"}
        ] if user_id == "alice" else [],
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

def test_get_webdav_writeback_intent_no_accounts():
    with TestClient(
        app,
        headers={"X-User-Id": "bob", "X-Organization-Id": "org-acme"},
    ) as client:
        response = client.post("/api/webdav/writeback-intent", json={})
        assert response.status_code == 422
        assert response.json()["detail"] == "No connected WebDAV accounts found."
