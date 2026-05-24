import pytest
from fastapi.testclient import TestClient
from main import app
from db.session import get_db

pytestmark = pytest.mark.usefixtures("dev_auth_dependency_overrides")

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
