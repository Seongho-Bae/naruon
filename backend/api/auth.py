from dataclasses import dataclass
from typing import Literal

from fastapi import Depends, HTTPException

RoleName = Literal["platform_admin", "organization_admin", "group_admin", "member"]


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


async def get_auth_context() -> AuthContext:
    return build_auth_context()


def build_auth_context() -> AuthContext:
    """
    Fail closed until the runtime has verified identity material.

    Client-supplied identity metadata is not authentication material in the
    runtime dependency path. Endpoint tests that need fixture identities must use
    explicit FastAPI dependency overrides, and production must replace this
    fail-closed placeholder with verified OIDC/JWT/session claims.
    """
    raise HTTPException(status_code=401, detail="Authentication required")


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
