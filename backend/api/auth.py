from fastapi import Header, HTTPException

async def get_current_user(x_user_id: str | None = Header(None, alias="X-User-Id")) -> str:

    """
    Extracts the user ID from the X-User-Id header.
    In a real implementation, this should validate a JWT or Keycloak token.
    For now, we enforce that it must be present.
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return x_user_id


async def get_current_workspace_id(
    x_workspace_id: str | None = Header("default-workspace", alias="X-Workspace-Id")
) -> str:
    return x_workspace_id or "default-workspace"


async def get_current_user_role(
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    current_user: str = Header(None, alias="X-User-Id"),
) -> str:
    if x_user_role:
        return x_user_role
    return "organization_admin" if current_user == "admin" else "member"
