from fastapi import Header

async def get_current_user(x_user_id: str | None = Header(None, alias="X-User-Id")) -> str:
    """
    Dummy authentication dependency.
    Extracts the user ID from the X-User-Id header.
    Defaults to "default" if not provided.
    """
    return x_user_id or "default"
