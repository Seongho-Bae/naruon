from pathlib import Path

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from api.auth import get_current_user
from core.config import settings


@pytest.fixture(autouse=True)
def reset_auth_settings(monkeypatch):
    monkeypatch.setattr(settings, "API_AUTH_USER_ID", None, raising=False)
    monkeypatch.setattr(settings, "API_AUTH_BEARER_TOKEN", None, raising=False)
    monkeypatch.setattr(settings, "API_AUTH_BEARER_TOKEN_FILE", None, raising=False)


def build_auth_app() -> FastAPI:
    auth_app = FastAPI()

    @auth_app.get("/protected")
    async def protected(current_user: str = Depends(get_current_user)):
        return {"user_id": current_user}

    return auth_app


async def get_protected_response(
    headers: dict[str, str] | None = None,
    *,
    raise_server_exceptions: bool = True,
):
    async with AsyncClient(
        transport=ASGITransport(
            app=build_auth_app(), raise_app_exceptions=raise_server_exceptions
        ),
        base_url="http://test",
    ) as client:
        return await client.get("/protected", headers=headers)


def configure_token(user_id: str = "default", token: str = "test-token") -> None:
    settings.API_AUTH_USER_ID = user_id
    settings.API_AUTH_BEARER_TOKEN = SecretStr(token)
    settings.API_AUTH_BEARER_TOKEN_FILE = None


@pytest.mark.asyncio
async def test_get_current_user_requires_configured_authentication():
    response = await get_protected_response(
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is not configured"}


@pytest.mark.asyncio
async def test_get_current_user_requires_bearer_token():
    configure_token()

    response = await get_protected_response()

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_bearer_token():
    configure_token()

    response = await get_protected_response(
        headers={"Authorization": "Bearer wrong-token"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


@pytest.mark.asyncio
async def test_get_current_user_returns_configured_user_for_valid_bearer_token():
    configure_token(user_id="user-123", token="test-token")

    response = await get_protected_response(
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 200
    assert response.json() == {"user_id": "user-123"}


@pytest.mark.asyncio
async def test_get_current_user_ignores_x_user_id_when_bearer_token_is_valid():
    configure_token(user_id="default", token="test-token")

    response = await get_protected_response(
        headers={"Authorization": "Bearer test-token", "X-User-Id": "attacker"},
    )

    assert response.status_code == 200
    assert response.json() == {"user_id": "default"}


@pytest.mark.asyncio
async def test_get_current_user_reads_bearer_token_from_configured_file(
    tmp_path: Path,
):
    token_file = tmp_path / "api-token"
    token_file.write_text("file-token\n", encoding="utf-8")
    settings.API_AUTH_USER_ID = "file-user"
    settings.API_AUTH_BEARER_TOKEN = None
    settings.API_AUTH_BEARER_TOKEN_FILE = str(token_file)

    response = await get_protected_response(
        headers={"Authorization": "Bearer file-token"}
    )

    assert response.status_code == 200
    assert response.json() == {"user_id": "file-user"}


@pytest.mark.asyncio
async def test_get_current_user_rejects_oversized_bearer_token_file(tmp_path: Path):
    token_file = tmp_path / "api-token"
    token_file.write_text("x" * ((10 * 1024) + 1), encoding="utf-8")
    settings.API_AUTH_USER_ID = "file-user"
    settings.API_AUTH_BEARER_TOKEN = None
    settings.API_AUTH_BEARER_TOKEN_FILE = str(token_file)

    response = await get_protected_response(
        headers={"Authorization": "Bearer file-token"}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is not configured"}


@pytest.mark.asyncio
async def test_get_current_user_rejects_non_regular_bearer_token_file(tmp_path: Path):
    token_dir = tmp_path / "api-token-dir"
    token_dir.mkdir()
    settings.API_AUTH_USER_ID = "file-user"
    settings.API_AUTH_BEARER_TOKEN = None
    settings.API_AUTH_BEARER_TOKEN_FILE = str(token_dir)

    response = await get_protected_response(
        headers={"Authorization": "Bearer file-token"}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is not configured"}


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_utf8_bearer_token_file(tmp_path: Path):
    token_file = tmp_path / "api-token"
    token_file.write_bytes(b"\xff\xfe")
    settings.API_AUTH_USER_ID = "file-user"
    settings.API_AUTH_BEARER_TOKEN = None
    settings.API_AUTH_BEARER_TOKEN_FILE = str(token_file)

    response = await get_protected_response(
        headers={"Authorization": "Bearer file-token"},
        raise_server_exceptions=False,
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is not configured"}
