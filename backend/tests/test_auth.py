import base64
import hashlib
import hmac
import json
import time
from collections.abc import Mapping
from pathlib import Path

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from api.auth import get_current_user
from core.auth_tokens import verified_signed_subject
from core.config import settings

TEST_SIGNING_SECRET = "test-auth-signing-secret-with-at-least-32-bytes"


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def build_compact_token(
    header: Mapping[str, object],
    payload: Mapping[str, object],
    *,
    secret: str = TEST_SIGNING_SECRET,
) -> str:
    signing_input = ".".join(
        [
            _base64url_encode(json.dumps(header, separators=(",", ":")).encode()),
            _base64url_encode(json.dumps(payload, separators=(",", ":")).encode()),
        ]
    )
    signature = hmac.new(
        secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256
    ).digest()
    return f"{signing_input}.{_base64url_encode(signature)}"


def build_signed_auth_token(
    subject: str = "default",
    *,
    secret: str = TEST_SIGNING_SECRET,
    expires_at: int | None = None,
    not_before: int | None = None,
) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": subject, "iat": now, "exp": expires_at or now + 3600}
    if not_before is not None:
        payload["nbf"] = not_before
    return build_compact_token(header, payload, secret=secret)


@pytest.fixture(autouse=True)
def reset_auth_settings(monkeypatch):
    monkeypatch.setattr(settings, "API_AUTH_USER_ID", None, raising=False)
    monkeypatch.setattr(settings, "API_AUTH_SIGNING_SECRET", None, raising=False)
    monkeypatch.setattr(settings, "API_AUTH_SIGNING_SECRET_FILE", None, raising=False)


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


def configure_signing_secret(secret: str = TEST_SIGNING_SECRET) -> None:
    settings.API_AUTH_SIGNING_SECRET = SecretStr(secret)
    settings.API_AUTH_SIGNING_SECRET_FILE = None


@pytest.mark.asyncio
async def test_get_current_user_requires_configured_authentication():
    response = await get_protected_response(
        headers={"Authorization": f"Bearer {build_signed_auth_token()}"}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is not configured"}


@pytest.mark.asyncio
async def test_get_current_user_requires_bearer_token():
    configure_signing_secret()

    response = await get_protected_response()

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_bearer_token():
    configure_signing_secret()

    response = await get_protected_response(
        headers={"Authorization": "Bearer wrong-token"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_verified_signed_subject_rejects_non_ascii_signature_without_server_error():
    token = build_signed_auth_token()
    header, payload, _signature = token.split(".")

    subject = verified_signed_subject(
        f"{header}.{payload}.é", TEST_SIGNING_SECRET, now=time.time()
    )

    assert subject is None


def test_verified_signed_subject_rejects_malformed_base64_payload():
    token = build_signed_auth_token()
    header, _payload, signature = token.split(".")

    assert (
        verified_signed_subject(f"{header}.not-valid-!.{signature}", TEST_SIGNING_SECRET)
        is None
    )


@pytest.mark.parametrize(
    "header",
    [
        {"alg": "none", "typ": "JWT"},
        {"alg": "HS256", "typ": "not-jwt"},
    ],
)
def test_verified_signed_subject_rejects_wrong_header_contract(
    header: Mapping[str, object]
):
    now = int(time.time())
    token = build_compact_token(
        header,
        {"sub": "default", "iat": now, "exp": now + 3600},
    )

    assert verified_signed_subject(token, TEST_SIGNING_SECRET, now=now) is None


def test_verified_signed_subject_rejects_tampered_signature():
    token = build_signed_auth_token()
    header, payload, _signature = token.split(".")

    assert (
        verified_signed_subject(f"{header}.{payload}.invalid", TEST_SIGNING_SECRET)
        is None
    )


def test_verified_signed_subject_rejects_blank_subject():
    token = build_signed_auth_token("   ")

    assert verified_signed_subject(token, TEST_SIGNING_SECRET) is None


def test_verified_signed_subject_rejects_future_not_before():
    now = int(time.time())
    token = build_signed_auth_token(not_before=now + 60)

    assert verified_signed_subject(token, TEST_SIGNING_SECRET, now=now) is None


def test_verified_signed_subject_rejects_token_expiring_at_current_time():
    now = int(time.time())
    token = build_signed_auth_token(expires_at=now)

    assert verified_signed_subject(token, TEST_SIGNING_SECRET, now=now) is None


@pytest.mark.asyncio
async def test_get_current_user_rejects_legacy_static_bearer_token():
    configure_signing_secret()

    response = await get_protected_response(
        headers={"Authorization": "Bearer test-token"}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


@pytest.mark.asyncio
async def test_get_current_user_returns_signed_token_subject():
    configure_signing_secret()

    response = await get_protected_response(
        headers={"Authorization": f"Bearer {build_signed_auth_token('user-123')}"}
    )

    assert response.status_code == 200
    assert response.json() == {"user_id": "user-123"}


@pytest.mark.asyncio
async def test_get_current_user_ignores_x_user_id_when_bearer_token_is_valid():
    configure_signing_secret()

    response = await get_protected_response(
        headers={
            "Authorization": f"Bearer {build_signed_auth_token('signed-user')}",
            "X-User-Id": "attacker",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"user_id": "signed-user"}


@pytest.mark.asyncio
async def test_get_current_user_rejects_expired_signed_token():
    configure_signing_secret()

    response = await get_protected_response(
        headers={
            "Authorization": f"Bearer {build_signed_auth_token(expires_at=int(time.time()) - 1)}"
        }
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


@pytest.mark.asyncio
async def test_get_current_user_reads_signing_secret_from_configured_file(
    tmp_path: Path,
):
    secret_file = tmp_path / "api-signing-secret"
    secret_file.write_text(f"{TEST_SIGNING_SECRET}\n", encoding="utf-8")
    settings.API_AUTH_SIGNING_SECRET = None
    settings.API_AUTH_SIGNING_SECRET_FILE = str(secret_file)

    response = await get_protected_response(
        headers={"Authorization": f"Bearer {build_signed_auth_token('file-user')}"}
    )

    assert response.status_code == 200
    assert response.json() == {"user_id": "file-user"}


@pytest.mark.asyncio
async def test_get_current_user_rejects_oversized_signing_secret_file(tmp_path: Path):
    secret_file = tmp_path / "api-signing-secret"
    secret_file.write_text("x" * ((10 * 1024) + 1), encoding="utf-8")
    settings.API_AUTH_SIGNING_SECRET = None
    settings.API_AUTH_SIGNING_SECRET_FILE = str(secret_file)

    response = await get_protected_response(
        headers={"Authorization": f"Bearer {build_signed_auth_token()}"}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is not configured"}


@pytest.mark.asyncio
async def test_get_current_user_rejects_non_regular_signing_secret_file(tmp_path: Path):
    secret_dir = tmp_path / "api-signing-secret-dir"
    secret_dir.mkdir()
    settings.API_AUTH_SIGNING_SECRET = None
    settings.API_AUTH_SIGNING_SECRET_FILE = str(secret_dir)

    response = await get_protected_response(
        headers={"Authorization": f"Bearer {build_signed_auth_token()}"}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is not configured"}


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_utf8_signing_secret_file(tmp_path: Path):
    secret_file = tmp_path / "api-signing-secret"
    secret_file.write_bytes(b"\xff\xfe")
    settings.API_AUTH_SIGNING_SECRET = None
    settings.API_AUTH_SIGNING_SECRET_FILE = str(secret_file)

    response = await get_protected_response(
        headers={"Authorization": f"Bearer {build_signed_auth_token()}"},
        raise_server_exceptions=False,
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is not configured"}
