from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from db.models import TenantConfig
from db.session import get_db

router = APIRouter(prefix="/api/config")


class TenantConfigCreate(BaseModel):
    user_id: str
    openai_api_key: Optional[str] = None


class TenantConfigResponse(BaseModel):
    user_id: str
    openai_api_key: Optional[str] = None


@router.post("")
async def create_or_update_config(
    config: TenantConfigCreate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TenantConfig).where(TenantConfig.user_id == config.user_id)
    )
    db_config = result.scalar_one_or_none()

    if db_config:
        if config.openai_api_key and config.openai_api_key != "********":
            db_config.openai_api_key = config.openai_api_key
    else:
        db_config = TenantConfig(
            user_id=config.user_id,
            openai_api_key=(
                config.openai_api_key if config.openai_api_key != "********" else None
            ),
        )
        db.add(db_config)

    await db.commit()
    return {"status": "ok"}


@router.get("", response_model=TenantConfigResponse)
async def get_config(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TenantConfig).where(TenantConfig.user_id == user_id)
    )
    db_config = result.scalar_one_or_none()

    if not db_config:
        return {"user_id": user_id, "openai_api_key": None}

    return {
        "user_id": db_config.user_id,
        "openai_api_key": "********" if db_config.openai_api_key else None,
    }
