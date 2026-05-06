from pathlib import Path
from stat import S_ISREG

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.auth_tokens import verified_signed_subject
from core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)
MAX_SIGNING_SECRET_FILE_BYTES = 10 * 1024
MIN_SIGNING_SECRET_BYTES = 32


def _auth_config_error() -> HTTPException:
    """Return a generic authentication configuration error."""
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Authentication is not configured",
    )


def _read_signing_secret_file(secret_file: str) -> str | None:
    """Read a small regular-file signing secret without unbounded memory use."""
    secret_path = Path(secret_file)
    try:
        secret_stat = secret_path.stat()
        if not S_ISREG(secret_stat.st_mode):
            raise _auth_config_error()
        if secret_stat.st_size > MAX_SIGNING_SECRET_FILE_BYTES:
            raise _auth_config_error()
        with secret_path.open("rb") as secret_handle:
            secret = secret_handle.read(MAX_SIGNING_SECRET_FILE_BYTES + 1)
    except HTTPException:
        raise
    except OSError as exc:
        raise _auth_config_error() from exc

    if len(secret) > MAX_SIGNING_SECRET_FILE_BYTES:
        raise _auth_config_error()
    try:
        decoded_secret = secret.decode("utf-8")
    except UnicodeError as exc:
        raise _auth_config_error() from exc
    return decoded_secret.strip() or None


def _configured_signing_secret() -> str | None:
    """Return the configured API token signing secret without exposing it."""
    if settings.API_AUTH_SIGNING_SECRET is not None:
        secret = settings.API_AUTH_SIGNING_SECRET.get_secret_value().strip()
        return secret or None

    if settings.API_AUTH_SIGNING_SECRET_FILE:
        return _read_signing_secret_file(settings.API_AUTH_SIGNING_SECRET_FILE)

    return None


def _has_sufficient_entropy(secret: str) -> bool:
    """Reject placeholder-size signing secrets that are too short for HMAC."""
    return len(secret.encode("utf-8")) >= MIN_SIGNING_SECRET_BYTES


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """
    Authenticate API callers with a signed subject-bearing bearer token.

    The backend no longer trusts request-controlled identity headers, a shared
    static bearer token, or a hardcoded local user. A deployment must configure
    a signing secret (or secret file), and callers must present a signed token
    with a non-expired `sub` claim before protected endpoints grant access.
    """
    signing_secret = _configured_signing_secret()

    if not signing_secret or not _has_sufficient_entropy(signing_secret):
        raise _auth_config_error()

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    subject = verified_signed_subject(credentials.credentials, signing_secret)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return subject
