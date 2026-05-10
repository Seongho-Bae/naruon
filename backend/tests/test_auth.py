import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import SecretStr

from api.auth import get_current_user
from core.config import settings


@pytest.mark.asyncio
async def test_get_current_user_requires_configured_bearer_secret(monkeypatch):
    monkeypatch.setattr(settings, "API_AUTH_TOKEN", None, raising=False)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(None)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Authentication is not configured"


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_bearer_credentials(monkeypatch):
    monkeypatch.setattr(
        settings, "API_AUTH_TOKEN", SecretStr("expected-token"), raising=False
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Authentication required"


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_bearer_token(monkeypatch):
    monkeypatch.setattr(
        settings, "API_AUTH_TOKEN", SecretStr("expected-token"), raising=False
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="attacker-chosen-token",
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authentication token"


@pytest.mark.asyncio
async def test_get_current_user_maps_valid_token_to_configured_single_mailbox(
    monkeypatch,
):
    monkeypatch.setattr(
        settings, "API_AUTH_TOKEN", SecretStr("expected-token"), raising=False
    )
    monkeypatch.setattr(settings, "AUTH_SINGLE_USER_ID", "mailbox-owner", raising=False)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="expected-token",
    )

    assert await get_current_user(credentials) == "mailbox-owner"
