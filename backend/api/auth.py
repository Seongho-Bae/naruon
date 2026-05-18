from dataclasses import dataclass
import hmac
from typing import Literal, cast, get_args

from fastapi import Depends, Header, HTTPException

from core.config import settings

RoleName = Literal["platform_admin", "organization_admin", "group_admin", "member"]
SCOPED_ROLES: set[str] = set(get_args(RoleName))
DEV_HEADER_AUTH_ENVIRONMENTS = {"development", "local", "test"}
MIN_DEV_AUTH_TOKEN_LENGTH = 32


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


def _dev_auth_token_matches(provided_token: str | None) -> bool:
    runtime_environment = settings.RUNTIME_ENVIRONMENT.strip().lower()
    if (
        not settings.TRUST_DEV_HEADERS
        or runtime_environment not in DEV_HEADER_AUTH_ENVIRONMENTS
        or settings.DEV_AUTH_TOKEN is None
    ):
        return False
    if provided_token is None:
        return False
    configured_token = settings.DEV_AUTH_TOKEN.get_secret_value()
    if len(configured_token) < MIN_DEV_AUTH_TOKEN_LENGTH:
        return False
    return hmac.compare_digest(provided_token, configured_token)


def _derive_role(user_id: str, requested_role: str | None) -> RoleName:
    """
    Derive user role from request headers in trusted dev/test mode.

    Header-provided roles are only available after the caller proves access to
    the server-side development auth token. DEBUG alone never enables identity
    or role trust because DEBUG can leak into deployed environments. User IDs do
    not imply administrative roles; privileged roles must be explicit trusted
    role claims.
    """
    if requested_role in SCOPED_ROLES:
        return cast(RoleName, requested_role)
    return "member"


def _parse_group_ids(group_ids_header: str | None) -> tuple[str, ...]:
    if not group_ids_header:
        return ()
    return tuple(
        group_id.strip() for group_id in group_ids_header.split(",") if group_id.strip()
    )


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
    x_user_id: str | None = Header(None, alias="X-User-Id"),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_organization_id: str | None = Header(None, alias="X-Organization-Id"),
    x_group_ids: str | None = Header(None, alias="X-Group-Ids"),
    x_dev_auth_token: str | None = Header(None, alias="X-Dev-Auth-Token"),
) -> AuthContext:
    return build_auth_context(
        x_user_id=x_user_id,
        x_user_role=x_user_role,
        x_organization_id=x_organization_id,
        x_group_ids=x_group_ids,
        x_dev_auth_token=x_dev_auth_token,
    )


def build_auth_context(
    x_user_id: object,
    x_user_role: object = None,
    x_organization_id: object = None,
    x_group_ids: object = None,
    x_dev_auth_token: object = None,
) -> AuthContext:
    """
    Builds an auth context from trusted identity material.

    Local/test header auth is accepted only when the server operator explicitly
    runs a local/test runtime environment, enables `TRUST_DEV_HEADERS`, configures
    a strong development token, and the request includes the matching
    `X-Dev-Auth-Token`. Public `X-User-*` headers alone are never an
    authentication mechanism; production OIDC/Keycloak/Casdoor token validation
    will replace this development-only path.
    """
    if not _dev_auth_token_matches(_normalize_header_value(x_dev_auth_token)):
        raise HTTPException(status_code=401, detail="Authentication required")

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
    x_user_id: str | None = Header(None, alias="X-User-Id"),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_organization_id: str | None = Header(None, alias="X-Organization-Id"),
    x_group_ids: str | None = Header(None, alias="X-Group-Ids"),
    x_dev_auth_token: str | None = Header(None, alias="X-Dev-Auth-Token"),
) -> str:
    return build_auth_context(
        x_user_id=x_user_id,
        x_user_role=x_user_role,
        x_organization_id=x_organization_id,
        x_group_ids=x_group_ids,
        x_dev_auth_token=x_dev_auth_token,
    ).user_id


async def get_current_workspace_id(
    auth_context: AuthContext = Depends(get_auth_context),
) -> str:
    return auth_context.workspace_id


async def get_current_user_role(
    auth_context: AuthContext = Depends(get_auth_context),
) -> str:
    return auth_context.role
