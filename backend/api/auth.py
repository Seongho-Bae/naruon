import base64
import binascii
import hashlib
import hmac
import json
import math
import time
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Annotated, Any, Literal, cast
from urllib.parse import urlparse

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from core.config import (
    DEFAULT_ALLOWED_BROWSER_ORIGINS,
    allowed_browser_origins,
    settings,
    validate_auth_session_hmac_secret_value,
)

RoleName = Literal["platform_admin", "organization_admin", "group_admin", "member"]
ALLOWED_ROLES: set[str] = {
    "platform_admin",
    "organization_admin",
    "group_admin",
    "member",
}
SESSION_ISSUER = "naruon-control-plane"
SESSION_AUDIENCE = "naruon-api"
SESSION_SIGNING_ALGORITHM = "HS256"
MIN_SESSION_SECRET_BYTES = 32
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
COOKIE_CSRF_ERROR = "Cross-site request rejected"
NO_REQUEST = cast(Request, None)
router = APIRouter(prefix="/api/auth")


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    role: RoleName
    organization_id: str | None
    group_ids: tuple[str, ...]
    workspace_id: str


class AuthContextResponse(BaseModel):
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
    request: Request = NO_REQUEST,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    naruon_session_token: Annotated[
        str | None, Cookie(alias="naruon_session_token")
    ] = None,
) -> AuthContext:
    _enforce_cookie_csrf_origin(request, authorization, naruon_session_token)
    return build_auth_context(
        authorization=authorization, session_cookie_token=naruon_session_token
    )


def build_auth_context(
    authorization: str | None = None, session_cookie_token: str | None = None
) -> AuthContext:
    """
    Build runtime identity from verified signed session material.

    Client-supplied identity metadata is not authentication material. Only a
    signed session token signed by the configured control-plane HMAC secret can
    supply identity, role, organization, group, and workspace claims in the
    runtime dependency path. Browser requests should use the HttpOnly
    ``naruon_session_token`` cookie; non-browser clients may still use a bearer
    token. Endpoint tests that need fixture identities must continue to use
    explicit FastAPI dependency overrides.
    """
    payload = _verify_signed_session_payload(
        authorization=authorization, session_cookie_token=session_cookie_token
    )
    return _auth_context_from_session_payload(payload)


def _authentication_error() -> HTTPException:
    return HTTPException(status_code=401, detail="Authentication required")


def _csrf_error() -> HTTPException:
    return HTTPException(status_code=403, detail=COOKIE_CSRF_ERROR)


def _normalized_origin(value: str) -> str | None:
    parsed = urlparse(value.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return None
    if parsed.username or parsed.password:
        return None
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


def _request_origin(request: Request) -> str | None:
    origin = request.headers.get("origin")
    if origin:
        return _normalized_origin(origin)
    referer = request.headers.get("referer")
    if referer:
        return _normalized_origin(referer)
    return None


def _is_local_browser_origin(origin: str) -> bool:
    parsed = urlparse(origin.strip())
    hostname = parsed.hostname
    if hostname is None:
        return False
    normalized_hostname = hostname.lower()
    if normalized_hostname == "localhost" or normalized_hostname.endswith(".localhost"):
        return True
    try:
        return ip_address(normalized_hostname).is_loopback
    except ValueError:
        return False


def _enforce_cookie_csrf_origin(
    request: Request | None,
    authorization: str | None,
    session_cookie_token: str | None,
) -> None:
    if authorization is not None or session_cookie_token is None:
        return
    if request is None or request.method.upper() in SAFE_METHODS:
        return

    configured_origins = allowed_browser_origins(settings.ALLOWED_BROWSER_ORIGINS)
    if settings.RUNTIME_ENVIRONMENT == "production" and (
        configured_origins == DEFAULT_ALLOWED_BROWSER_ORIGINS
        or any(_is_local_browser_origin(origin) for origin in configured_origins)
    ):
        raise _csrf_error()
    allowed_origins = {origin.lower() for origin in configured_origins}
    if _request_origin(request) not in allowed_origins:
        raise _csrf_error()


def _session_secret_bytes() -> bytes:
    configured = settings.AUTH_SESSION_HMAC_SECRET
    if configured is None:
        raise _authentication_error()
    secret = configured.get_secret_value().encode("utf-8")
    if len(secret) < MIN_SESSION_SECRET_BYTES:
        raise _authentication_error()
    try:
        validate_auth_session_hmac_secret_value(configured.get_secret_value())
    except ValueError:
        raise _authentication_error() from None
    return secret


def _extract_bearer_token(authorization: str | None) -> str:
    if authorization is None:
        raise _authentication_error()
    scheme, separator, token = authorization.strip().partition(" ")
    if separator != " " or scheme.lower() != "bearer" or not token.strip():
        raise _authentication_error()
    return token.strip()


def _extract_session_token(
    authorization: str | None, session_cookie_token: str | None
) -> str:
    if authorization is not None:
        return _extract_bearer_token(authorization)
    if session_cookie_token is None or not session_cookie_token.strip():
        raise _authentication_error()
    return session_cookie_token.strip()


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


def _json_object_from_base64url_segment(segment: str) -> dict[str, Any]:
    try:
        decoded = json.loads(_base64url_decode(segment).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise _authentication_error() from None
    if not isinstance(decoded, dict):
        raise _authentication_error()
    return decoded


def _verify_signed_session_payload(
    authorization: str | None, session_cookie_token: str | None
) -> dict[str, Any]:
    token = _extract_session_token(authorization, session_cookie_token)
    token_segments = token.split(".")
    if len(token_segments) != 3:
        raise _authentication_error()
    header_segment, payload_segment, signature_segment = token_segments

    header = _json_object_from_base64url_segment(header_segment)
    if header.get("alg") != SESSION_SIGNING_ALGORITHM:
        raise _authentication_error()

    secret = _session_secret_bytes()
    signing_input = f"{header_segment}.{payload_segment}"
    expected_signature = hmac.new(
        secret, _ascii_token_segment(signing_input), hashlib.sha256
    ).digest()
    provided_signature = _base64url_decode(signature_segment)
    if not hmac.compare_digest(expected_signature, provided_signature):
        raise _authentication_error()

    return _json_object_from_base64url_segment(payload_segment)


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


@router.get("/context", response_model=AuthContextResponse)
async def auth_context_endpoint(
    auth_context: AuthContext = Depends(get_auth_context),
) -> AuthContextResponse:
    return AuthContextResponse(
        user_id=auth_context.user_id,
        role=auth_context.role,
        organization_id=auth_context.organization_id,
        group_ids=auth_context.group_ids,
        workspace_id=auth_context.workspace_id,
    )
