from pathlib import Path

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from api.auth import get_current_user
from core.config import settings


@pytest.fixture(autouse=True)
def reset_auth_settings(monkeypatch):
    monkeypatch.setattr(settings, "API_AUTH_USER_ID", None, raising=False)
    monkeypatch.setattr(settings, "API_AUTH_BEARER_TOKEN", None, raising=False)
    monkeypatch.setattr(settings, "API_AUTH_BEARER_TOKEN_FILE", None, raising=False)


def build_auth_client() -> TestClient:
    auth_app = FastAPI()

    @auth_app.get("/protected")
    async def protected(current_user: str = Depends(get_current_user)):
        return {"user_id": current_user}

    return TestClient(auth_app)


def configure_token(user_id: str = "default", token: str = "test-token") -> None:
    settings.API_AUTH_USER_ID = user_id
    settings.API_AUTH_BEARER_TOKEN = SecretStr(token)
    settings.API_AUTH_BEARER_TOKEN_FILE = None


def test_get_current_user_requires_configured_authentication():
    client = build_auth_client()

    response = client.get("/protected", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is not configured"}


def test_get_current_user_requires_bearer_token():
    configure_token()
    client = build_auth_client()

    response = client.get("/protected")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_get_current_user_rejects_invalid_bearer_token():
    configure_token()
    client = build_auth_client()

    response = client.get("/protected", headers={"Authorization": "Bearer wrong-token"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_get_current_user_returns_configured_user_for_valid_bearer_token():
    configure_token(user_id="user-123", token="test-token")
    client = build_auth_client()

    response = client.get("/protected", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.json() == {"user_id": "user-123"}


def test_get_current_user_ignores_x_user_id_when_bearer_token_is_valid():
    configure_token(user_id="default", token="test-token")
    client = build_auth_client()

    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer test-token", "X-User-Id": "attacker"},
    )

    assert response.status_code == 200
    assert response.json() == {"user_id": "default"}


def test_get_current_user_reads_bearer_token_from_configured_file(tmp_path: Path):
    token_file = tmp_path / "api-token"
    token_file.write_text("file-token\n", encoding="utf-8")
    settings.API_AUTH_USER_ID = "file-user"
    settings.API_AUTH_BEARER_TOKEN = None
    settings.API_AUTH_BEARER_TOKEN_FILE = str(token_file)
    client = build_auth_client()

    response = client.get("/protected", headers={"Authorization": "Bearer file-token"})

    assert response.status_code == 200
    assert response.json() == {"user_id": "file-user"}
