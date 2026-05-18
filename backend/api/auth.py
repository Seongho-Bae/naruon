import base64
import binascii
import hashlib
import hmac
import json
import math
import time
from dataclasses import dataclass
from typing import Annotated, Any, Literal, cast

from fastapi import Depends, Header, HTTPException

from core.config import settings

RoleName = Literal["platform_admin", "organization_admin", "group_admin", "member"]
ALLOWED_ROLES: set[str] = {
    "platform_admin",
    "organization_admin",
    "group_admin",
    "member",
}
SESSION_ISSUER = "naruon-control-plane"
SESSION_AUDIENCE = "naruon-api"
MIN_SESSION_SECRET_BYTES = 32


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    role: RoleName
    organization_id: str | None
    group_ids: tuple[str, ...]
    workspace_id: str


def ensure_organization_access(auth_context: AuthContext, organization_id: str) -> None:
    if auth_context.role == "platform_admin":
        return
    if auth_context.organization_id != organization_id:
        raise HTTPException(
            status_code=403, detail="Resource belongs to a different organization"
        )


async def get_auth_context(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> AuthContext:
    return build_auth_context(authorization=authorization)


def build_auth_context(authorization: str | None = None) -> AuthContext:
    """
    Build runtime identity from verified signed session material.

    Client-supplied identity metadata is not authentication material. Only a
    bearer token signed by the configured control-plane HMAC secret can supply
    identity, role, organization, group, and workspace claims in the runtime
    dependency path. Endpoint tests that need fixture identities must continue to
    use explicit FastAPI dependency overrides.
    """
    payload = _verify_signed_session_payload(authorization)
    return _auth_context_from_session_payload(payload)


def _authentication_error() -> HTTPException:
    return HTTPException(status_code=401, detail="Authentication required")


def _session_secret_bytes() -> bytes:
    configured = settings.AUTH_SESSION_HMAC_SECRET
    if configured is None:
        raise _authentication_error()
    secret = configured.get_secret_value().encode("utf-8")
    if len(secret) < MIN_SESSION_SECRET_BYTES:
        raise _authentication_error()
    return secret


def _extract_bearer_token(authorization: str | None) -> str:
    if authorization is None:
        raise _authentication_error()
    scheme, separator, token = authorization.strip().partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not token.strip():
        raise _authentication_error()
    return token.strip()


def _base64url_decode(segment: str) -> bytes:
    if not segment:
        raise _authentication_error()
    segment_bytes = _ascii_token_segment(segment)
    padding = b"=" * (-len(segment_bytes) % 4)
    try:
        return base64.b64decode(segment_bytes + padding, altchars=b"-_", validate=True)
    except (binascii.Error, ValueError):
        raise _authentication_error() from None


def _ascii_token_segment(segment: str) -> bytes:
    try:
        return segment.encode("ascii")
    except UnicodeEncodeError:
        raise _authentication_error() from None


def _verify_signed_session_payload(authorization: str | None) -> dict[str, Any]:
    token = _extract_bearer_token(authorization)
    payload_segment, separator, signature_segment = token.partition(".")
    if separator != "." or "." in signature_segment:
        raise _authentication_error()

    secret = _session_secret_bytes()
    expected_signature = hmac.new(
        secret, _ascii_token_segment(payload_segment), hashlib.sha256
    ).digest()
    provided_signature = _base64url_decode(signature_segment)
    if not hmac.compare_digest(expected_signature, provided_signature):
        raise _authentication_error()

    try:
        payload = json.loads(_base64url_decode(payload_segment).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise _authentication_error() from None
    if not isinstance(payload, dict):
        raise _authentication_error()
    return payload


def _required_string_claim(payload: dict[str, Any], name: str) -> str:
    value = payload.get(name)
    if not isinstance(value, str) or not value.strip() or not value.isascii():
        raise _authentication_error()
    return value.strip()


def _optional_string_claim(payload: dict[str, Any], name: str) -> str | None:
    value = payload.get(name)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or not value.isascii():
        raise _authentication_error()
    return value.strip()


def _tuple_string_claim(payload: dict[str, Any], name: str) -> tuple[str, ...]:
    value = payload.get(name)
    if value is None:
        return ()
    if not isinstance(value, list):
        raise _authentication_error()
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip() or not item.isascii():
            raise _authentication_error()
        normalized.append(item.strip())
    return tuple(normalized)


def _validate_session_metadata(payload: dict[str, Any]) -> None:
    if payload.get("ver") != 1:
        raise _authentication_error()
    if payload.get("iss") != SESSION_ISSUER:
        raise _authentication_error()
    if payload.get("aud") != SESSION_AUDIENCE:
        raise _authentication_error()
    expires_at = payload.get("exp")
    if isinstance(expires_at, bool) or not isinstance(expires_at, (int, float)):
        raise _authentication_error()
    if not math.isfinite(expires_at):
        raise _authentication_error()
    if expires_at <= time.time():
        raise _authentication_error()


def _auth_context_from_session_payload(payload: dict[str, Any]) -> AuthContext:
    _validate_session_metadata(payload)
    role_value = _required_string_claim(payload, "role")
    if role_value not in ALLOWED_ROLES:
        raise _authentication_error()
    role = cast(RoleName, role_value)
    organization_id = _optional_string_claim(payload, "org")
    if role != "platform_admin" and organization_id is None:
        raise _authentication_error()
    return AuthContext(
        user_id=_required_string_claim(payload, "sub"),
        role=role,
        organization_id=organization_id,
        group_ids=_tuple_string_claim(payload, "groups"),
        workspace_id=_required_string_claim(payload, "workspace"),
    )


async def get_current_user(
    auth_context: AuthContext = Depends(get_auth_context),
) -> str:
    return auth_context.user_id


async def get_current_workspace_id(
    auth_context: AuthContext = Depends(get_auth_context),
) -> str:
    return auth_context.workspace_id


async def get_current_user_role(
    auth_context: AuthContext = Depends(get_auth_context),
) -> str:
    return auth_context.role
