from dataclasses import dataclass
from typing import Literal, cast

from fastapi import Depends, Header, HTTPException

from core.config import settings


RoleName = Literal["platform_admin", "organization_admin", "group_admin", "member"]
SCOPED_ROLES: set[str] = {"platform_admin", "organization_admin", "group_admin", "member"}


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
    if not (settings.DEBUG or settings.TRUST_DEV_HEADERS):
        return "member"
    if requested_role in SCOPED_ROLES:
        return cast(RoleName, requested_role)
    return "organization_admin" if user_id == "admin" else "member"


def _parse_group_ids(group_ids_header: str | None) -> tuple[str, ...]:
    if not group_ids_header:
        return ()
    return tuple(group_id.strip() for group_id in group_ids_header.split(",") if group_id.strip())


def _derive_workspace_id(
    user_id: str,
    organization_id: str | None,
) -> str:
    if organization_id:
        return f"workspace-{organization_id}"
    return f"workspace-{user_id}"


def ensure_organization_access(auth_context: AuthContext, organization_id: str) -> None:
    if auth_context.role == "platform_admin":
        return
    if auth_context.organization_id != organization_id:
        raise HTTPException(status_code=403, detail="Resource belongs to a different organization")


async def get_auth_context(
    x_user_id: str | None = Header(None, alias="X-User-Id"),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_organization_id: str | None = Header(None, alias="X-Organization-Id"),
    x_group_ids: str | None = Header(None, alias="X-Group-Ids"),
) -> AuthContext:
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
    token-derived scope claims from Keycloak or Casdoor.
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
    x_user_id: str | None = Header(None, alias="X-User-Id"),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_organization_id: str | None = Header(None, alias="X-Organization-Id"),
    x_group_ids: str | None = Header(None, alias="X-Group-Ids"),
) -> str:
    return build_auth_context(
        x_user_id=x_user_id,
        x_user_role=x_user_role,
        x_organization_id=x_organization_id,
        x_group_ids=x_group_ids,
    ).user_id


async def get_current_workspace_id(auth_context: AuthContext = Depends(get_auth_context)) -> str:
    return auth_context.workspace_id


async def get_current_user_role(
    auth_context: AuthContext = Depends(get_auth_context),
) -> str:
    return auth_context.role
