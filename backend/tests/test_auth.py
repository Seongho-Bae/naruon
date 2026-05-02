import pytest
from fastapi import HTTPException

from api.auth import create_user_token, get_current_user


@pytest.mark.asyncio
async def test_get_current_user_accepts_signed_bearer_token(monkeypatch):
    monkeypatch.setenv("AUTH_TOKEN_SECRET", "test-auth-secret")

    token = create_user_token("alice")

    assert await get_current_user(f"Bearer {token}") == "alice"


@pytest.mark.asyncio
async def test_get_current_user_rejects_expired_signed_bearer_token(monkeypatch):
    monkeypatch.setenv("AUTH_TOKEN_SECRET", "test-auth-secret")

    token = create_user_token("alice", ttl_seconds=-1)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(f"Bearer {token}")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_rejects_tampered_signed_bearer_token(monkeypatch):
    monkeypatch.setenv("AUTH_TOKEN_SECRET", "test-auth-secret")

    token = create_user_token("alice")
    tampered_token = f"{token[:-1]}x"

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(f"Bearer {tampered_token}")

    assert exc_info.value.status_code == 401
