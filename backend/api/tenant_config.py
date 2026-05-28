from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict
from typing import Optional

from db.models import TenantConfig
from db.session import get_db
from api.auth import (
    AuthContext,
    get_auth_context,
    get_current_user_role,
    is_admin_role,
)
from services.tenant_config_scope import (
    get_scoped_tenant_config,
    new_scoped_tenant_config,
)
from services.email_client import (
    validate_imap_destination,
    validate_imap_port,
    validate_pop3_destination,
    validate_pop3_port,
    validate_smtp_destination,
    validate_smtp_host,
    validate_smtp_port,
)

router = APIRouter(prefix="/api/config")

@router.get("/global")
async def get_global_config(
    role: str = Depends(get_current_user_role)
):
    if not is_admin_role(role):
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return {"status": "ok", "global_settings": {}}


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
    pop3_username: Optional[str] = None
    pop3_password: Optional[str] = None
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
    pop3_username: Optional[str] = None
    pop3_password: Optional[str] = None
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
    "pop3_password",
    "oauth_client_secret",
    "openai_api_key",
    "google_client_secret",
}

MAILBOX_MANAGE_FORBIDDEN = (
    "Mailbox settings are personal and can only be managed by the authenticated user"
)
MAILBOX_VIEW_FORBIDDEN = (
    "Mailbox settings are personal and can only be viewed by the authenticated user"
)
def _field_value(
    config_data: dict, db_config: TenantConfig | None, field_name: str
):
    if field_name in config_data:
        return config_data[field_name]
    if db_config is not None:
        return getattr(db_config, field_name)
    return None


def _validate_smtp_config(smtp_server: str | None, smtp_port: int | None) -> None:
    try:
        if smtp_server is not None:
            validate_smtp_host(smtp_server, resolve_host=True)
        if smtp_port is not None:
            validate_smtp_port(smtp_port)
        if smtp_server is not None and smtp_port is not None:
            validate_smtp_destination(smtp_server, smtp_port)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

def _validate_imap_config(imap_server: str | None, imap_port: int | None) -> None:
    try:
        if imap_server is not None and imap_port is not None:
            validate_imap_destination(imap_server, imap_port)
        elif imap_server is not None:
            validate_imap_destination(imap_server, 993)
        elif imap_port is not None:
            validate_imap_port(imap_port)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"imap_server/imap_port validation failed: {exc}",
        ) from exc

def _validate_pop3_config(pop3_server: str | None, pop3_port: int | None) -> None:
    try:
        if pop3_server is not None and pop3_port is not None:
            validate_pop3_destination(pop3_server, pop3_port)
        elif pop3_server is not None:
            validate_pop3_destination(pop3_server, 995)
        elif pop3_port is not None:
            validate_pop3_port(pop3_port)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"pop3_server/pop3_port validation failed: {exc}",
        ) from exc

def validate_mail_config_update(
    config_data: dict, db_config: TenantConfig | None
) -> None:
    smtp_server = _field_value(config_data, db_config, "smtp_server")
    smtp_port = _field_value(config_data, db_config, "smtp_port")
    imap_server = _field_value(config_data, db_config, "imap_server")
    imap_port = _field_value(config_data, db_config, "imap_port")
    pop3_server = _field_value(config_data, db_config, "pop3_server")
    pop3_port = _field_value(config_data, db_config, "pop3_port")

    _validate_smtp_config(smtp_server, smtp_port)
    _validate_imap_config(imap_server, imap_port)
    _validate_pop3_config(pop3_server, pop3_port)


@router.post("")
async def create_or_update_config(
    config: TenantConfigCreate,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    if config.user_id != auth_context.user_id:
        raise HTTPException(status_code=403, detail=MAILBOX_MANAGE_FORBIDDEN)

    db_config = await get_scoped_tenant_config(
        db,
        auth_context.user_id,
        auth_context.organization_id,
    )

    config_data = config.model_dump(exclude_unset=True)
    validate_mail_config_update(config_data, db_config)

    if db_config:
        for key, value in config_data.items():
            if key in SECRET_FIELDS and value == "********":
                continue
            setattr(db_config, key, value)
    else:
        for key in SECRET_FIELDS:
            if key in config_data and config_data[key] == "********":
                config_data[key] = None
        db_config = new_scoped_tenant_config(
            user_id=auth_context.user_id,
            organization_id=auth_context.organization_id,
        )
        for key, value in config_data.items():
            setattr(db_config, key, value)
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
    auth_context: AuthContext = Depends(get_auth_context),
):
    if user_id != auth_context.user_id:
        raise HTTPException(status_code=403, detail=MAILBOX_VIEW_FORBIDDEN)

    db_config = await get_scoped_tenant_config(
        db,
        auth_context.user_id,
        auth_context.organization_id,
    )

    if not db_config:
        return TenantConfigResponse(user_id=user_id)

    response = TenantConfigResponse.model_validate(db_config)

    for secret_field in SECRET_FIELDS:
        if getattr(response, secret_field):
            setattr(response, secret_field, "********")

    return response
