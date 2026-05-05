LOCAL_DEVELOPMENT_USER_ID = "default"


async def get_current_user() -> str:
    """
    Local-development authentication dependency.

    Until real authentication exists, the backend runs as a fixed single local
    user. Do not trust request-controlled identity headers such as X-User-Id.
    """
    return LOCAL_DEVELOPMENT_USER_ID
