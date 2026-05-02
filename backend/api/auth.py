import base64
import binascii
import hashlib
import hmac
import json
import os
import time
from typing import Any

from fastapi import Header, HTTPException, status

AUTH_TOKEN_SECRET_ENV = "AUTH_TOKEN_SECRET"
TOKEN_SCHEME = "Bearer"


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid bearer authentication is required",
        headers={"WWW-Authenticate": TOKEN_SCHEME},
    )


def _base64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    try:
        return base64.urlsafe_b64decode(f"{segment}{padding}")
    except (ValueError, binascii.Error) as exc:
        raise _unauthorized() from exc


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _sign_payload(encoded_payload: str, secret: str) -> str:
    signature = hmac.new(
        secret.encode(), encoded_payload.encode(), hashlib.sha256
    ).digest()
    return _base64url_encode(signature)


def _load_auth_secret() -> str:
    secret = os.environ.get(AUTH_TOKEN_SECRET_ENV, "").strip()
    if not secret:
        raise _unauthorized()
    return secret


def _decode_verified_payload(token: str, secret: str) -> dict[str, Any]:
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
    except ValueError as exc:
        raise _unauthorized() from exc

    expected_signature = _sign_payload(encoded_payload, secret)
    if not hmac.compare_digest(encoded_signature, expected_signature):
        raise _unauthorized()

    try:
        payload = json.loads(_base64url_decode(encoded_payload))
    except json.JSONDecodeError as exc:
        raise _unauthorized() from exc

    if not isinstance(payload, dict):
        raise _unauthorized()
    return payload


def _subject_from_payload(payload: dict[str, Any]) -> str:
    subject = payload.get("sub")
    expires_at = payload.get("exp")
    if not isinstance(subject, str) or not subject.strip():
        raise _unauthorized()
    if not isinstance(expires_at, int) or expires_at <= int(time.time()):
        raise _unauthorized()
    return subject


def create_user_token(user_id: str, ttl_seconds: int = 3600) -> str:
    """Create a signed bearer-token value for local tooling and tests."""
    if not user_id.strip():
        raise ValueError("user_id is required")
    payload = json.dumps(
        {"sub": user_id, "exp": int(time.time()) + ttl_seconds},
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    encoded_payload = _base64url_encode(payload)
    encoded_signature = _sign_payload(encoded_payload, _load_auth_secret())
    return f"{encoded_payload}.{encoded_signature}"


async def get_current_user(
    authorization: str | None = Header(None, alias="Authorization"),
) -> str:
    """Return the authenticated user from a signed bearer token."""
    if not authorization:
        raise _unauthorized()

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != TOKEN_SCHEME.lower() or not token:
        raise _unauthorized()

    payload = _decode_verified_payload(token, _load_auth_secret())
    return _subject_from_payload(payload)
