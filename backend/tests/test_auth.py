import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
import jwt
from sqlalchemy.exc import IntegrityError

from api.auth import create_user_token, get_current_user
from db.session import get_db
from main import app

TEST_AUTH_SECRET = "test-auth-secret-with-at-least-32-bytes"


@pytest.mark.asyncio
async def test_get_current_user_accepts_signed_bearer_token(monkeypatch):
    monkeypatch.setenv("AUTH_TOKEN_SECRET", TEST_AUTH_SECRET)

    token = create_user_token("alice")

    assert await get_current_user(f"Bearer {token}") == "alice"


@pytest.mark.asyncio
async def test_get_current_user_rejects_expired_signed_bearer_token(monkeypatch):
    monkeypatch.setenv("AUTH_TOKEN_SECRET", TEST_AUTH_SECRET)

    token = create_user_token("alice", ttl_seconds=-1)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(f"Bearer {token}")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_rejects_tampered_signed_bearer_token(monkeypatch):
    monkeypatch.setenv("AUTH_TOKEN_SECRET", TEST_AUTH_SECRET)

    token = create_user_token("alice")
    header, payload, signature = token.split(".")
    replacement = "A" if signature[0] != "A" else "B"
    tampered_token = f"{header}.{payload}.{replacement}{signature[1:]}"

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(f"Bearer {tampered_token}")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_revoke_current_token_persists_jti_and_blocks_reuse(monkeypatch):
    monkeypatch.setenv("AUTH_TOKEN_SECRET", TEST_AUTH_SECRET)

    class RevocationSession:
        def __init__(self):
            self.revoked_jti = None
            self.added_token = None
            self.committed = False

        async def scalar(self, query):
            return self.revoked_jti

        def add(self, obj):
            self.added_token = obj
            self.revoked_jti = obj.jti

        async def commit(self):
            self.committed = True

    session = RevocationSession()
    token = create_user_token("alice")
    payload = jwt.decode(token, TEST_AUTH_SECRET, algorithms=["HS256"])

    assert await get_current_user(f"Bearer {token}", db=session) == "alice"

    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).post(
            "/api/auth/revoke",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "revoked"}
    assert session.committed is True
    assert session.added_token.jti == payload["jti"]
    assert session.added_token.user_id == "alice"

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(f"Bearer {token}", db=session)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_revoke_current_token_is_idempotent_for_duplicate_jti(monkeypatch):
    monkeypatch.setenv("AUTH_TOKEN_SECRET", TEST_AUTH_SECRET)

    class DuplicateRevocationSession:
        def __init__(self):
            self.rolled_back = False

        async def scalar(self, query):
            return None

        def add(self, obj):
            self.added_token = obj

        async def commit(self):
            raise IntegrityError("duplicate jti", params=None, orig=Exception())

        async def rollback(self):
            self.rolled_back = True

    session = DuplicateRevocationSession()
    token = create_user_token("alice")

    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).post(
            "/api/auth/revoke",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "revoked"}
    assert session.rolled_back is True


@pytest.mark.asyncio
async def test_revoke_current_token_is_idempotent_when_jti_already_revoked(
    monkeypatch,
):
    monkeypatch.setenv("AUTH_TOKEN_SECRET", TEST_AUTH_SECRET)

    class AlreadyRevokedSession:
        def __init__(self):
            self.add_called = False

        async def scalar(self, query):
            return "existing-jti"

        def add(self, obj):
            self.add_called = True

        async def commit(self):
            raise AssertionError("already-revoked tokens should not be inserted again")

    session = AlreadyRevokedSession()
    token = create_user_token("alice")

    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).post(
            "/api/auth/revoke",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "revoked"}
    assert session.add_called is False


def test_create_user_token_uses_standard_jwt_with_revocable_id(monkeypatch):
    monkeypatch.setenv("AUTH_TOKEN_SECRET", TEST_AUTH_SECRET)

    token = create_user_token("alice")
    payload = jwt.decode(
        token,
        TEST_AUTH_SECRET,
        algorithms=["HS256"],
        options={"require": ["sub", "exp", "jti"]},
    )

    assert token.count(".") == 2
    assert payload["sub"] == "alice"
    assert isinstance(payload["jti"], str)
    assert payload["jti"]


@pytest.mark.asyncio
async def test_get_current_user_rejects_revoked_jwt_id(monkeypatch):
    monkeypatch.setenv("AUTH_TOKEN_SECRET", TEST_AUTH_SECRET)

    class RevokedTokenSession:
        async def scalar(self, query):
            return True

    token = create_user_token("alice")

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(f"Bearer {token}", db=RevokedTokenSession())

    assert exc_info.value.status_code == 401
