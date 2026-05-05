from pathlib import Path
from secrets import compare_digest

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import settings


bearer_scheme = HTTPBearer(auto_error=False)


def _configured_bearer_token() -> str | None:
    """Return the configured API bearer token without exposing it in logs."""
    if settings.API_AUTH_BEARER_TOKEN is not None:
        token = settings.API_AUTH_BEARER_TOKEN.get_secret_value().strip()
        return token or None

    if settings.API_AUTH_BEARER_TOKEN_FILE:
        try:
            token = Path(settings.API_AUTH_BEARER_TOKEN_FILE).read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication is not configured",
            ) from exc
        return token or None

    return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """
    Authenticate API callers with a configured bearer token.

    The backend no longer trusts request-controlled identity headers or a
    hardcoded local user. A deployment must configure both the authenticated
    user id and a bearer token (or token file) before protected endpoints grant
    access.
    """
    configured_user_id = (settings.API_AUTH_USER_ID or "").strip()
    expected_token = _configured_bearer_token()

    if not configured_user_id or not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not compare_digest(credentials.credentials, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return configured_user_id
