from sqlalchemy import select
import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from api.auth import AuthContext, get_auth_context
from db.models import AuditLog, LLMProvider
from pydantic import BaseModel

router = APIRouter(prefix="/api/llm-providers", tags=["llm-providers"])


class LLMProviderCreate(BaseModel):
    name: str
    provider_type: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    is_active: bool = False


class LLMProviderUpdate(BaseModel):
    name: Optional[str] = None
    provider_type: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None


class LLMProviderResponse(BaseModel):
    id: int
    name: str
    provider_type: str
    base_url: Optional[str] = None
    is_active: bool
    configured: bool
    fingerprint: Optional[str] = None
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


def _get_fingerprint(api_key: str | None) -> str | None:
    if not api_key:
        return None
    if len(api_key) > 8:
        return f"***{api_key[-4:]}"
    return "***"


async def require_provider_admin(
    auth_context: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    if auth_context.role not in {"platform_admin", "organization_admin"}:
        raise HTTPException(
            status_code=403, detail="Organization admin access required"
        )
    if not auth_context.organization_id:
        raise HTTPException(status_code=403, detail="Organization scope is required")
    return auth_context


@router.get("", response_model=List[LLMProviderResponse])
async def list_providers(
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(require_provider_admin),
):
    result = await db.execute(
        select(LLMProvider).where(
            LLMProvider.organization_id == auth_context.organization_id
        )
    )
    providers = result.scalars().all()

    responses = []
    for p in providers:
        responses.append(
            LLMProviderResponse(
                id=p.id,
                name=p.name,
                provider_type=p.provider_type,
                base_url=p.base_url,
                is_active=p.is_active,
                configured=bool(p.api_key),
                fingerprint=_get_fingerprint(p.api_key),
                updated_at=p.updated_at,
            )
        )
    return responses


@router.post("", response_model=LLMProviderResponse)
async def create_provider(
    data: LLMProviderCreate,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(require_provider_admin),
):
    provider = LLMProvider(
        name=data.name,
        provider_type=data.provider_type,
        base_url=data.base_url,
        api_key=data.api_key,
        is_active=data.is_active,
        organization_id=auth_context.organization_id,
    )
    db.add(provider)
    audit = AuditLog(
        user_id=auth_context.user_id,
        action="create",
        resource_type="llm_provider",
        details=f"Created provider {data.name}",
    )
    db.add(audit)
    try:
        await db.commit()
        await db.refresh(provider)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Provider name already exists")

    return LLMProviderResponse(
        id=provider.id,
        name=provider.name,
        provider_type=provider.provider_type,
        base_url=provider.base_url,
        is_active=provider.is_active,
        configured=bool(provider.api_key),
        fingerprint=_get_fingerprint(provider.api_key),
        updated_at=provider.updated_at,
    )


@router.put("/{provider_id}", response_model=LLMProviderResponse)
async def update_provider(
    provider_id: int,
    data: LLMProviderUpdate,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(require_provider_admin),
):
    result = await db.execute(
        select(LLMProvider).where(
            LLMProvider.id == provider_id,
            LLMProvider.organization_id == auth_context.organization_id,
        )
    )
    provider = result.scalars().first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    updated = False
    if data.name is not None:
        provider.name = data.name
        updated = True
    if data.provider_type is not None:
        provider.provider_type = data.provider_type
        updated = True
    if data.base_url is not None:
        provider.base_url = data.base_url
        updated = True
    if data.api_key is not None:
        provider.api_key = data.api_key
        updated = True
    if data.is_active is not None:
        provider.is_active = data.is_active
        updated = True

    if updated:
        audit = AuditLog(
            user_id=auth_context.user_id,
            action="update",
            resource_type="llm_provider",
            resource_id=str(provider.id),
            details=f"Updated provider {provider.name}",
        )
        db.add(audit)
        try:
            await db.commit()
            await db.refresh(provider)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=409, detail="Provider name already exists")

    return LLMProviderResponse(
        id=provider.id,
        name=provider.name,
        provider_type=provider.provider_type,
        base_url=provider.base_url,
        is_active=provider.is_active,
        configured=bool(provider.api_key),
        fingerprint=_get_fingerprint(provider.api_key),
        updated_at=provider.updated_at,
    )


@router.delete("/{provider_id}", status_code=204)
async def delete_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(require_provider_admin),
):
    result = await db.execute(
        select(LLMProvider).where(
            LLMProvider.id == provider_id,
            LLMProvider.organization_id == auth_context.organization_id,
        )
    )
    provider = result.scalars().first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    await db.delete(provider)
    audit = AuditLog(
        user_id=auth_context.user_id,
        action="delete",
        resource_type="llm_provider",
        resource_id=str(provider.id),
        details=f"Deleted provider {provider.name}",
    )
    db.add(audit)
    await db.commit()
