from pathlib import Path
from secrets import compare_digest
from stat import S_ISREG

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)
MAX_BEARER_TOKEN_FILE_BYTES = 10 * 1024


def _auth_config_error() -> HTTPException:
    """Return a generic authentication configuration error."""
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Authentication is not configured",
    )


def _read_bearer_token_file(token_file: str) -> str | None:
    """Read a small regular-file bearer token without unbounded memory use."""
    token_path = Path(token_file)
    try:
        token_stat = token_path.stat()
        if not S_ISREG(token_stat.st_mode):
            raise _auth_config_error()
        if token_stat.st_size > MAX_BEARER_TOKEN_FILE_BYTES:
            raise _auth_config_error()
        with token_path.open("rb") as token_handle:
            token = token_handle.read(MAX_BEARER_TOKEN_FILE_BYTES + 1)
    except HTTPException:
        raise
    except OSError as exc:
        raise _auth_config_error() from exc

    if len(token) > MAX_BEARER_TOKEN_FILE_BYTES:
        raise _auth_config_error()
    try:
        decoded_token = token.decode("utf-8")
    except UnicodeError as exc:
        raise _auth_config_error() from exc
    return decoded_token.strip() or None


def _configured_bearer_token() -> str | None:
    """Return the configured API bearer token without exposing it in logs."""
    if settings.API_AUTH_BEARER_TOKEN is not None:
        token = settings.API_AUTH_BEARER_TOKEN.get_secret_value().strip()
        return token or None

    if settings.API_AUTH_BEARER_TOKEN_FILE:
        return _read_bearer_token_file(settings.API_AUTH_BEARER_TOKEN_FILE)

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
