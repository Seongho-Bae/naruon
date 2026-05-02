import os
import uuid
import datetime
from typing import Any

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import RevokedAuthToken
from db.session import get_db

AUTH_TOKEN_SECRET_ENV = "AUTH_TOKEN_SECRET"
TOKEN_SCHEME = "Bearer"
TOKEN_ALGORITHM = "HS256"

router = APIRouter(prefix="/api/auth")


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid bearer authentication is required",
        headers={"WWW-Authenticate": TOKEN_SCHEME},
    )


def _load_auth_secret() -> str:
    secret = os.environ.get(AUTH_TOKEN_SECRET_ENV, "").strip()
    if not secret:
        raise _unauthorized()
    return secret


def _decode_verified_payload(token: str, secret: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[TOKEN_ALGORITHM],
            options={"require": ["sub", "exp", "jti"]},
        )
    except jwt.PyJWTError as exc:
        raise _unauthorized() from exc

    if not isinstance(payload, dict):
        raise _unauthorized()
    return payload


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise _unauthorized()

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != TOKEN_SCHEME.lower() or not token:
        raise _unauthorized()
    return token


def _subject_from_payload(payload: dict[str, Any]) -> str:
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise _unauthorized()
    return subject


def _token_id_from_payload(payload: dict[str, Any]) -> str:
    token_id = payload.get("jti")
    if not isinstance(token_id, str) or not token_id.strip():
        raise _unauthorized()
    return token_id


def _expires_at_from_payload(payload: dict[str, Any]) -> datetime.datetime:
    expires_at = payload.get("exp")
    if not isinstance(expires_at, (int, float)):
        raise _unauthorized()
    return datetime.datetime.fromtimestamp(expires_at, tz=datetime.timezone.utc)


async def _token_is_revoked(payload: dict[str, Any], db: AsyncSession) -> bool:
    token_id = _token_id_from_payload(payload)
    revoked_token_id = await db.scalar(
        select(RevokedAuthToken.jti).where(RevokedAuthToken.jti == token_id)
    )
    return revoked_token_id is not None


async def _raise_if_token_revoked(payload: dict[str, Any], db: object) -> None:
    if not hasattr(db, "scalar"):
        return
    if await _token_is_revoked(payload, db):
        raise _unauthorized()


def create_user_token(user_id: str, ttl_seconds: int = 3600) -> str:
    """Create a signed JWT bearer-token value for local tooling and tests."""
    if not user_id.strip():
        raise ValueError("user_id is required")
    now = datetime.datetime.now(datetime.timezone.utc)
    return jwt.encode(
        {
            "sub": user_id,
            "iat": now,
            "exp": now + datetime.timedelta(seconds=ttl_seconds),
            "jti": uuid.uuid4().hex,
        },
        _load_auth_secret(),
        algorithm=TOKEN_ALGORITHM,
    )


async def get_current_user(
    authorization: str | None = Header(None, alias="Authorization"),
    db: AsyncSession | None = Depends(get_db),
) -> str:
    """Return the authenticated user from a signed bearer token."""
    token = _extract_bearer_token(authorization)
    payload = _decode_verified_payload(token, _load_auth_secret())
    await _raise_if_token_revoked(payload, db)
    return _subject_from_payload(payload)


@router.post("/revoke")
async def revoke_current_token(
    authorization: str | None = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Revoke the current JWT by storing its jti until token expiration."""
    token = _extract_bearer_token(authorization)
    payload = _decode_verified_payload(token, _load_auth_secret())
    if await _token_is_revoked(payload, db):
        return {"status": "revoked"}

    try:
        db.add(
            RevokedAuthToken(
                jti=_token_id_from_payload(payload),
                user_id=_subject_from_payload(payload),
                expires_at=_expires_at_from_payload(payload),
            )
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
    return {"status": "revoked"}
