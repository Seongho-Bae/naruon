import http.client
import datetime
import hashlib
import json
import logging
import math
import socket
import ssl
import time
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal, cast
from urllib.parse import urlsplit

import jwt
from asyncpg import Connection, connect as asyncpg_connect
from jwt import PyJWKClient
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from core.config import settings, validate_auth_session_hmac_secret_value
from core.url_validation import (
    ValidatedHTTPSURLHost,
    parse_allowed_hosts,
    validate_https_url_host_details,
)

logger = logging.getLogger(__name__)
OIDC_JWKS_TIMEOUT_SECONDS = 5
OIDC_JWKS_MAX_RESPONSE_BYTES = 1024 * 1024


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(
        self,
        address: str,
        *,
        port: int,
        server_hostname: str,
        timeout: float,
        context: ssl.SSLContext,
    ):
        super().__init__(address, port=port, timeout=timeout, context=context)
        self._server_hostname = server_hostname

    def connect(self) -> None:
        self.sock = socket.create_connection(
            (self.host, self.port),
            self.timeout,
            self.source_address,
        )
        self.sock = self._context.wrap_socket(
            self.sock,
            server_hostname=self._server_hostname,
        )


class _PinnedOIDCJWKSClient(PyJWKClient):
    def __init__(self, validated_url: ValidatedHTTPSURLHost):
        super().__init__(
            validated_url.normalized_url,
            cache_keys=True,
            timeout=OIDC_JWKS_TIMEOUT_SECONDS,
        )
        self._validated_url = validated_url
        self._ssl_context = ssl.create_default_context()

    def fetch_data(self) -> Any:
        parsed = urlsplit(self.uri)
        target = parsed.path or "/"
        if parsed.query:
            target = f"{target}?{parsed.query}"
        host_header = self._validated_url.hostname
        if self._validated_url.port != 443:
            host_header = f"{host_header}:{self._validated_url.port}"

        last_error: Exception | None = None
        for address in self._validated_url.addresses:
            try:
                connection = _PinnedHTTPSConnection(
                    address,
                    port=self._validated_url.port,
                    server_hostname=self._validated_url.hostname,
                    timeout=self.timeout,
                    context=self._ssl_context,
                )
                try:
                    connection.request(
                        "GET",
                        target,
                        headers={
                            **self.headers,
                            "Host": host_header,
                        },
                    )
                    response = connection.getresponse()
                    response_body = response.read(OIDC_JWKS_MAX_RESPONSE_BYTES + 1)
                    if len(response_body) > OIDC_JWKS_MAX_RESPONSE_BYTES:
                        raise ValueError("OIDC JWKS response is too large")
                    if response.status >= 400:
                        raise ValueError(
                            f"OIDC JWKS endpoint returned {response.status}"
                        )
                    jwk_set = json.loads(response_body.decode("utf-8"))
                finally:
                    connection.close()
                if self.jwk_set_cache is not None:
                    self.jwk_set_cache.put(jwk_set)
                return jwk_set
            except Exception as exc:
                last_error = exc
        raise jwt.PyJWKClientConnectionError(
            f'Fail to fetch data from the url, err: "{last_error}"'
        ) from last_error


def _build_oidc_jwks_client() -> PyJWKClient | None:
    if not settings.OIDC_JWKS_URL:
        return None
    validated_url = validate_https_url_host_details(
        "OIDC_JWKS_URL",
        settings.OIDC_JWKS_URL,
        parse_allowed_hosts(settings.ALLOWED_OIDC_HOSTS),
        "ALLOWED_OIDC_HOSTS",
    )
    return _PinnedOIDCJWKSClient(validated_url)


jwks_client = _build_oidc_jwks_client()
_cached_oidc_signing_keys: tuple[Any, ...] = ()

RoleName = Literal[
    "system_admin",
    "tenant_admin",
    "platform_admin",
    "organization_admin",
    "group_admin",
    "member",
]
SessionVerifier = Literal["hmac", "oidc", "override"]
ALLOWED_ROLES: set[str] = {
    "system_admin",
    "tenant_admin",
    "platform_admin",
    "organization_admin",
    "group_admin",
    "member",
}
SYSTEM_ADMIN_ROLES = frozenset({"system_admin", "platform_admin"})
TENANT_ADMIN_ROLES = frozenset({"tenant_admin", "organization_admin"})
ADMIN_ROLES = SYSTEM_ADMIN_ROLES | TENANT_ADMIN_ROLES
SESSION_ISSUER = "naruon-control-plane"
SESSION_AUDIENCE = "naruon-api"
SESSION_SIGNING_ALGORITHM = "HS256"
OIDC_SIGNING_ALGORITHM = "RS256"
MIN_SESSION_SECRET_BYTES = 32

router = APIRouter(prefix="/api/auth", tags=["auth"])


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    role: RoleName
    organization_id: str | None
    group_ids: tuple[str, ...]
    workspace_id: str
    session_verifier: SessionVerifier = field(default="override", compare=False)


class LogoutResponse(BaseModel):
    revoked: bool


class SessionResponse(BaseModel):
    user_id: str
    organization_id: str | None
    workspace_id: str


def ensure_organization_access(auth_context: AuthContext, organization_id: str) -> None:
    if is_system_admin_role(auth_context.role):
        return
    if auth_context.organization_id != organization_id:
        raise HTTPException(
            status_code=403, detail="Resource belongs to a different organization"
        )


def is_system_admin_role(role: str) -> bool:
    return role in SYSTEM_ADMIN_ROLES


def is_tenant_admin_role(role: str) -> bool:
    return role in TENANT_ADMIN_ROLES


def is_admin_role(role: str) -> bool:
    return role in ADMIN_ROLES


async def get_auth_context(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> AuthContext:
    return await build_persistent_auth_context(authorization)


def build_auth_context(authorization: str | None = None) -> AuthContext:
    """
    Build runtime identity from verified signed session material.

    Client-supplied identity metadata is not authentication material. Only a
    bearer token signed by the configured control-plane HMAC secret can supply
    identity, role, organization, group, and workspace claims in the runtime
    dependency path. Endpoint tests that need fixture identities must continue to
    use explicit FastAPI dependency overrides.
    """
    payload, session_verifier = _verify_signed_session_payload(authorization)
    return _auth_context_from_session_payload(payload, session_verifier)


async def build_persistent_auth_context(
    authorization: str | None,
) -> AuthContext:
    token = _extract_bearer_token(authorization)
    payload, session_verifier = _verify_signed_session_token(token)
    await _reject_persistently_revoked_session_token(token)
    return _auth_context_from_session_payload(payload, session_verifier)


def _authentication_error() -> HTTPException:
    return HTTPException(status_code=401, detail="Authentication required")


def preload_oidc_jwks() -> None:
    """Populate OIDC signing keys outside the request authentication path."""
    global _cached_oidc_signing_keys
    if jwks_client is None:
        _cached_oidc_signing_keys = ()
        return
    try:
        jwk_set = jwks_client.get_jwk_set(refresh=True)
        _cached_oidc_signing_keys = tuple(jwk_set.keys)
    except Exception:
        _cached_oidc_signing_keys = ()
        logger.exception("OIDC JWKS preload failed; requests will fail closed.")


def _cached_oidc_signing_key_from_jwt(token: str) -> Any:
    if not _cached_oidc_signing_keys:
        raise _authentication_error()
    try:
        header = jwt.get_unverified_header(token)
    except Exception:
        raise _authentication_error() from None
    _reject_unsupported_critical_headers(header)
    if header.get("alg") != OIDC_SIGNING_ALGORITHM:
        raise _authentication_error()
    key_id = header.get("kid")
    if not isinstance(key_id, str) or not key_id.strip():
        raise _authentication_error()
    for signing_key in _cached_oidc_signing_keys:
        if getattr(signing_key, "key_id", None) == key_id:
            return signing_key
    raise _authentication_error()


def _reject_unsupported_critical_headers(header: dict[str, Any]) -> None:
    if "crit" in header:
        raise _authentication_error()


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


def _session_token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _as_aware_utc(value: datetime.datetime) -> datetime.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=datetime.timezone.utc)
    return value.astimezone(datetime.timezone.utc)


def _session_expiration_datetime(payload: dict[str, Any]) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(
        _session_expires_at(payload), datetime.timezone.utc
    )


def _revocation_database_url() -> str:
    database_url = str(settings.DATABASE_URL)
    if database_url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + database_url[len("postgresql+asyncpg://") :]
    if database_url.startswith("postgres+asyncpg://"):
        return "postgres://" + database_url[len("postgres+asyncpg://") :]
    return database_url


async def revoke_session_token(
    token: str,
    expires_at: datetime.datetime,
    *,
    user_id: str,
    organization_id: str | None,
    workspace_id: str,
) -> None:
    now = _utc_now()
    normalized_expires_at = _as_aware_utc(expires_at)
    if normalized_expires_at <= now:
        return
    fingerprint = _session_token_fingerprint(token)

    connection: Connection | None = None
    try:
        connection = await asyncpg_connect(_revocation_database_url(), timeout=5)
        await connection.execute(
            "DELETE FROM revoked_session_tokens WHERE expires_at <= $1",
            now,
        )
        await connection.execute(
            """
            INSERT INTO revoked_session_tokens (
                token_fingerprint,
                user_id,
                organization_id,
                workspace_id,
                expires_at,
                revoked_at
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (token_fingerprint) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                organization_id = EXCLUDED.organization_id,
                workspace_id = EXCLUDED.workspace_id,
                expires_at = EXCLUDED.expires_at,
                revoked_at = EXCLUDED.revoked_at
            """,
            fingerprint,
            user_id,
            organization_id,
            workspace_id,
            normalized_expires_at,
            now,
        )
    except HTTPException:
        raise
    except Exception:
        raise _authentication_error() from None
    finally:
        if connection is not None:
            await connection.close()


async def _reject_persistently_revoked_session_token(token: str) -> None:
    connection: Connection | None = None
    try:
        connection = await asyncpg_connect(_revocation_database_url(), timeout=5)
        is_revoked = await connection.fetchval(
            """
            SELECT TRUE
            FROM revoked_session_tokens
            WHERE token_fingerprint = $1 AND expires_at > $2
            LIMIT 1
            """,
            _session_token_fingerprint(token),
            _utc_now(),
        )
    except HTTPException:
        raise
    except Exception:
        raise _authentication_error() from None
    finally:
        if connection is not None:
            await connection.close()
    if is_revoked:
        raise _authentication_error()


def _verify_signed_session_payload(
    authorization: str | None,
) -> tuple[dict[str, Any], SessionVerifier]:
    token = _extract_bearer_token(authorization)
    return _verify_signed_session_token(token)


def _verify_signed_session_token(token: str) -> tuple[dict[str, Any], SessionVerifier]:
    if settings.OIDC_ISSUER_URL:
        return _verify_oidc_session_token(token)
    return _verify_hmac_session_token(token)


def _verify_oidc_session_token(token: str) -> tuple[dict[str, Any], SessionVerifier]:
    if jwks_client is None:
        raise _authentication_error()
    try:
        signing_key = _cached_oidc_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=[OIDC_SIGNING_ALGORITHM],
            audience=settings.OIDC_CLIENT_ID,
            issuer=settings.OIDC_ISSUER_URL,
        )
        _reject_signed_session_system_admin_payload(payload)
        return payload, "oidc"
    except Exception:
        raise _authentication_error() from None


def _verify_hmac_session_token(token: str) -> tuple[dict[str, Any], SessionVerifier]:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        raise _authentication_error() from None
    if header.get("alg") != SESSION_SIGNING_ALGORITHM:
        raise _authentication_error()
    _reject_unsupported_critical_headers(header)

    try:
        payload = jwt.decode(
            token,
            _session_secret_bytes(),
            algorithms=[SESSION_SIGNING_ALGORITHM],
            audience=SESSION_AUDIENCE,
            issuer=SESSION_ISSUER,
        )
    except jwt.PyJWTError:
        raise _authentication_error()
    if not isinstance(payload, dict):
        raise _authentication_error()
    _reject_signed_session_system_admin_payload(payload)
    return payload, "hmac"


def _reject_signed_session_system_admin_payload(payload: dict[str, Any]) -> None:
    role_claim = payload.get("role")
    if not isinstance(role_claim, str):
        raise _authentication_error()
    # SaaS control-plane roles require explicit server-side assignment, not
    # externally supplied HMAC or enterprise OIDC session claims.
    if role_claim in SYSTEM_ADMIN_ROLES:
        raise _authentication_error()


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


def _session_expires_at(payload: dict[str, Any]) -> float:
    expires_at = payload.get("exp")
    if isinstance(expires_at, bool) or not isinstance(expires_at, (int, float)):
        raise _authentication_error()
    if not math.isfinite(expires_at):
        raise _authentication_error()
    return float(expires_at)


def _validate_session_metadata(
    payload: dict[str, Any], session_verifier: SessionVerifier
) -> None:
    if session_verifier == "hmac":
        if payload.get("ver") != 1:
            raise _authentication_error()
        if payload.get("iss") != SESSION_ISSUER:
            raise _authentication_error()
        if payload.get("aud") != SESSION_AUDIENCE:
            raise _authentication_error()
    elif session_verifier != "oidc":
        raise _authentication_error()
    if _session_expires_at(payload) <= time.time():
        raise _authentication_error()


def _auth_context_from_session_payload(
    payload: dict[str, Any], session_verifier: SessionVerifier
) -> AuthContext:
    _validate_session_metadata(payload, session_verifier)
    role_value = _required_string_claim(payload, "role")
    if role_value not in ALLOWED_ROLES:
        raise _authentication_error()
    role = cast(RoleName, role_value)
    organization_id = _optional_string_claim(payload, "org")
    if not is_system_admin_role(role) and organization_id is None:
        raise _authentication_error()
    return AuthContext(
        user_id=_required_string_claim(payload, "sub"),
        role=role,
        organization_id=organization_id,
        group_ids=_tuple_string_claim(payload, "groups"),
        workspace_id=_required_string_claim(payload, "workspace"),
        session_verifier=cast(SessionVerifier, session_verifier),
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


@router.get("/session", response_model=SessionResponse)
async def current_session(
    auth_context: AuthContext = Depends(get_auth_context),
) -> SessionResponse:
    return SessionResponse(
        user_id=auth_context.user_id,
        organization_id=auth_context.organization_id,
        workspace_id=auth_context.workspace_id,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout_current_session(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> LogoutResponse:
    token = _extract_bearer_token(authorization)
    payload, session_verifier = _verify_signed_session_token(token)
    auth_context = _auth_context_from_session_payload(payload, session_verifier)
    await revoke_session_token(
        token,
        _session_expiration_datetime(payload),
        user_id=auth_context.user_id,
        organization_id=auth_context.organization_id,
        workspace_id=auth_context.workspace_id,
    )
    return LogoutResponse(revoked=True)
