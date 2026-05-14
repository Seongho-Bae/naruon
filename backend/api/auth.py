import asyncio
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, cast, get_args

import jwt
from fastapi import Depends, Header, HTTPException
from pydantic import SecretStr

from core.config import settings

RoleName = Literal["platform_admin", "organization_admin", "group_admin", "member"]
SCOPED_ROLES: set[str] = set(get_args(RoleName))


@dataclass(frozen=True)
class AuthContext:
    user_id: str
    role: RoleName
    organization_id: str | None
    group_ids: tuple[str, ...]
    workspace_id: str


def _normalize_header_value(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _derive_role(user_id: str, requested_role: str | None) -> RoleName:
    """
    Derive user role from request headers in trusted dev/test mode.

    In production, header-provided roles are ignored and every request is treated
    as `member` until SSO/OIDC claims are wired in.
    """
    if not (settings.DEBUG or settings.TRUST_DEV_HEADERS):
        return "member"
    if requested_role in SCOPED_ROLES:
        return cast(RoleName, requested_role)
    return "organization_admin" if user_id == "admin" else "member"


def _parse_group_ids(group_ids_header: str | None) -> tuple[str, ...]:
    if not group_ids_header:
        return ()
    return tuple(
        group_id.strip() for group_id in group_ids_header.split(",") if group_id.strip()
    )


def _extract_role_from_claims(user_id: str, claims: dict) -> RoleName:
    requested_role = claims.get("naruon_role") or claims.get("role")
    if isinstance(requested_role, str) and requested_role in SCOPED_ROLES:
        return cast(RoleName, requested_role)

    roles = claims.get("roles")
    if isinstance(roles, list):
        for candidate in (
            "platform_admin",
            "organization_admin",
            "group_admin",
            "member",
        ):
            if candidate in roles:
                return cast(RoleName, candidate)

    return "member"


def _build_context_from_claims(claims: dict) -> AuthContext:
    user_id = claims.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        raise HTTPException(status_code=401, detail="Authentication required")

    organization_id = claims.get("organization_id") or claims.get("org_id")
    if organization_id is not None and not isinstance(organization_id, str):
        organization_id = None

    raw_groups = claims.get("groups")
    group_ids: tuple[str, ...]
    if isinstance(raw_groups, list):
        group_ids = tuple(
            str(group).strip() for group in raw_groups if str(group).strip()
        )
    else:
        group_ids = ()

    role = _extract_role_from_claims(user_id, claims)
    workspace_id = _derive_workspace_id(user_id, organization_id)
    return AuthContext(
        user_id=user_id,
        role=role,
        organization_id=organization_id,
        group_ids=group_ids,
        workspace_id=workspace_id,
    )


@lru_cache(maxsize=8)
def _get_jwk_client(jwks_url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(jwks_url)


def _require_oidc_claim_expectations() -> tuple[str, str]:
    issuer = settings.OIDC_ISSUER.strip() if settings.OIDC_ISSUER else None
    audience = settings.OIDC_AUDIENCE.strip() if settings.OIDC_AUDIENCE else None
    if not issuer or not audience:
        raise HTTPException(
            status_code=503, detail="OIDC issuer and audience are not configured"
        )
    return issuer, audience


def _get_oidc_shared_secret() -> str | None:
    secret = settings.OIDC_SHARED_SECRET
    if isinstance(secret, SecretStr):
        return secret.get_secret_value()
    return secret


async def _decode_bearer_token(authorization: str) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid bearer token")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Invalid bearer token")

    issuer, audience = _require_oidc_claim_expectations()
    options = {"require": ["sub", "iss", "aud", "exp"]}
    try:
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg")
        if algorithm == "RS256":
            jwks_url = settings.OIDC_JWKS_URL
            if not jwks_url:
                raise HTTPException(
                    status_code=503, detail="OIDC JWKS URL is not configured"
                )
            signing_key = await asyncio.to_thread(
                _get_jwk_client(jwks_url).get_signing_key_from_jwt, token
            )
            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=audience,
                issuer=issuer,
                options=options,
            )

        secret = _get_oidc_shared_secret()
        if not secret:
            raise HTTPException(
                status_code=503, detail="OIDC shared secret is not configured"
            )

        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=audience,
            issuer=issuer,
            options=options,
        )
    except HTTPException:
        raise
    except (jwt.PyJWTError, jwt.PyJWKClientError) as exc:
        raise HTTPException(status_code=401, detail="Invalid bearer token") from exc


def _derive_workspace_id(
    user_id: str,
    organization_id: str | None,
) -> str:
    """
    Derive workspace identity from organization or user context only.

    Client-provided workspace overrides are intentionally ignored to prevent
    cross-tenant scope spoofing.
    """
    if organization_id:
        return f"workspace-{organization_id}"
    return f"workspace-{user_id}"


def ensure_organization_access(auth_context: AuthContext, organization_id: str) -> None:
    if auth_context.role == "platform_admin":
        return
    if auth_context.organization_id != organization_id:
        raise HTTPException(
            status_code=403, detail="Resource belongs to a different organization"
        )


async def get_auth_context(
    authorization: str | None = Header(None, alias="Authorization"),
    x_user_id: str | None = Header(None, alias="X-User-Id"),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_organization_id: str | None = Header(None, alias="X-Organization-Id"),
    x_group_ids: str | None = Header(None, alias="X-Group-Ids"),
) -> AuthContext:
    authorization_value = _normalize_header_value(authorization)
    if authorization_value and settings.AUTH_MODE in {"oidc", "hybrid"}:
        return _build_context_from_claims(
            await _decode_bearer_token(authorization_value)
        )

    if settings.AUTH_MODE == "oidc":
        raise HTTPException(status_code=401, detail="Authentication required")

    if settings.AUTH_MODE == "hybrid" and not (
        settings.DEBUG or settings.TRUST_DEV_HEADERS
    ):
        raise HTTPException(status_code=401, detail="Authentication required")

    if settings.AUTH_MODE == "header" and not (
        settings.DEBUG or settings.TRUST_DEV_HEADERS
    ):
        raise HTTPException(status_code=401, detail="Authentication required")

    return build_auth_context(
        x_user_id=x_user_id,
        x_user_role=x_user_role,
        x_organization_id=x_organization_id,
        x_group_ids=x_group_ids,
    )


def build_auth_context(
    x_user_id: object,
    x_user_role: object = None,
    x_organization_id: object = None,
    x_group_ids: object = None,
) -> AuthContext:
    """
    Builds an auth context from the current request headers.
    Today this still trusts local/dev headers, but the shape matches future
    token-derived scope claims from Keycloak or Casdoor. In production,
    role headers are ignored and requests remain `member` until OIDC is wired.
    """
    user_id = _normalize_header_value(x_user_id)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    organization_id = _normalize_header_value(x_organization_id)
    role = _derive_role(user_id, _normalize_header_value(x_user_role))
    group_ids = _parse_group_ids(_normalize_header_value(x_group_ids))
    workspace_id = _derive_workspace_id(user_id, organization_id)

    return AuthContext(
        user_id=user_id,
        role=role,
        organization_id=organization_id,
        group_ids=group_ids,
        workspace_id=workspace_id,
    )


async def get_current_user(
    authorization: str | None = Header(None, alias="Authorization"),
    x_user_id: str | None = Header(None, alias="X-User-Id"),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_organization_id: str | None = Header(None, alias="X-Organization-Id"),
    x_group_ids: str | None = Header(None, alias="X-Group-Ids"),
) -> str:
    return (
        await get_auth_context(
            authorization=authorization,
            x_user_id=x_user_id,
            x_user_role=x_user_role,
            x_organization_id=x_organization_id,
            x_group_ids=x_group_ids,
        )
    ).user_id


async def get_current_workspace_id(
    auth_context: AuthContext = Depends(get_auth_context),
) -> str:
    return auth_context.workspace_id


async def get_current_user_role(
    auth_context: AuthContext = Depends(get_auth_context),
) -> str:
    return auth_context.role
