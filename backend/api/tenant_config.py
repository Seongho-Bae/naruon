from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict
from typing import Optional

from db.models import TenantConfig
from db.session import get_db
from api.auth import get_current_user

router = APIRouter(prefix="/api/config")


class TenantConfigCreate(BaseModel):
    user_id: str
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    imap_server: Optional[str] = None
    imap_port: Optional[int] = None
    imap_username: Optional[str] = None
    imap_password: Optional[str] = None
    pop3_server: Optional[str] = None
    pop3_port: Optional[int] = None
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    oauth_redirect_uri: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None


class TenantConfigResponse(BaseModel):
    user_id: str
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    imap_server: Optional[str] = None
    imap_port: Optional[int] = None
    imap_username: Optional[str] = None
    imap_password: Optional[str] = None
    pop3_server: Optional[str] = None
    pop3_port: Optional[int] = None
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    oauth_redirect_uri: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


SECRET_FIELDS = {
    "smtp_password",
    "imap_password",
    "oauth_client_secret",
    "openai_api_key",
    "google_client_secret",
}


@router.post("")
async def create_or_update_config(
    config: TenantConfigCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    if config.user_id != current_user:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(TenantConfig).where(TenantConfig.user_id == config.user_id)
    )
    db_config = result.scalar_one_or_none()

    config_data = config.model_dump(exclude_unset=True)

    if db_config:
        for key, value in config_data.items():
            if key in SECRET_FIELDS and value == "********":
                continue
            setattr(db_config, key, value)
    else:
        for key in SECRET_FIELDS:
            if key in config_data and config_data[key] == "********":
                config_data[key] = None
        db_config = TenantConfig(**config_data)
        db.add(db_config)

    try:
        await db.commit()
    except Exception as exc:
        if "ENCRYPTION_KEY is required" not in str(exc):
            raise
        raise HTTPException(
            status_code=503,
            detail="Server encryption key is not configured. Contact your workspace administrator.",
        ) from exc
    return {"status": "ok"}


@router.get("", response_model=TenantConfigResponse)
async def get_config(
    user_id: str, 
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(TenantConfig).where(TenantConfig.user_id == user_id)
    )
    db_config = result.scalar_one_or_none()

    if not db_config:
        return TenantConfigResponse(user_id=user_id)

    response = TenantConfigResponse.model_validate(db_config)

    for secret_field in SECRET_FIELDS:
        if getattr(response, secret_field):
            setattr(response, secret_field, "********")

    return response
