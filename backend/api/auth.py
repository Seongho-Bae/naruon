from fastapi import Depends, Header, HTTPException

async def get_current_user(x_user_id: str | None = Header(None, alias="X-User-Id")) -> str:

    """
    Extracts the user ID from the X-User-Id header.
    In a real implementation, this should validate a JWT or Keycloak token.
    For now, we enforce that it must be present.
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return x_user_id


async def get_current_workspace_id(current_user: str = Depends(get_current_user)) -> str:
    return f"workspace-{current_user}"


async def get_current_user_role(
    current_user: str = Depends(get_current_user),
) -> str:
    return "organization_admin" if current_user == "admin" else "member"
