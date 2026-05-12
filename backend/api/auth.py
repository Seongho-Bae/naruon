from fastapi import Header, HTTPException

async def get_current_user(x_user_id: str | None = Header(None, alias="X-User-Id")) -> dict:

    """
    Extracts the user ID from the X-User-Id header.
    In a real implementation, this should validate a JWT or Keycloak token.
    For now, we enforce that it must be present.
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return {"id": x_user_id, "roles": ["admin"] if x_user_id == "admin" else []}
