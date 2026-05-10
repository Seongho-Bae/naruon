import hmac
from typing import NoReturn

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def _raise_authentication_required() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """Return the configured single-mailbox user after bearer-token validation."""
    configured_token = settings.API_AUTH_TOKEN
    if configured_token is None or not configured_token.get_secret_value():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        )

    if credentials is None:
        _raise_authentication_required()
    validated_credentials = credentials

    if validated_credentials.scheme.lower() != "bearer":
        _raise_authentication_required()

    if not hmac.compare_digest(
        validated_credentials.credentials,
        configured_token.get_secret_value(),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return settings.AUTH_SINGLE_USER_ID
