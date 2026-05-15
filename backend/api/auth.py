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
    raw_issuer = getattr(settings, "OIDC_ISSUER", None)
    raw_audience = getattr(settings, "OIDC_AUDIENCE", None)
    issuer = raw_issuer.strip() if raw_issuer else None
    audience = raw_audience.strip() if raw_audience else None
    if not issuer or not audience:
        raise HTTPException(
            status_code=503, detail="OIDC issuer and audience are not configured"
        )
    return issuer, audience


def _get_oidc_shared_secret() -> str | None:
    secret = getattr(settings, "OIDC_SHARED_SECRET", None)
    if isinstance(secret, SecretStr):
        return secret.get_secret_value()
    return secret


def _expected_oidc_algorithm() -> Literal["RS256", "HS256"]:
    if getattr(settings, "OIDC_JWKS_URL", None):
        return "RS256"
    if _get_oidc_shared_secret():
        return "HS256"
    raise HTTPException(status_code=503, detail="OIDC verifier is not configured")


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
        expected_algorithm = _expected_oidc_algorithm()
        if algorithm != expected_algorithm:
            raise HTTPException(status_code=401, detail="Invalid bearer token")
        if expected_algorithm == "RS256":
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
) -> AuthContext:
    authorization_value = _normalize_header_value(authorization)
    if authorization_value and settings.AUTH_MODE in {"oidc", "hybrid"}:
        return _build_context_from_claims(
            await _decode_bearer_token(authorization_value)
        )

    raise HTTPException(status_code=401, detail="Authentication required")


async def get_current_user(
    authorization: str | None = Header(None, alias="Authorization"),
) -> str:
    return (
        await get_auth_context(
            authorization=authorization,
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
