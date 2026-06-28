"""Support backend api llm_providers."""

import datetime
import hashlib
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import AuthContext, get_auth_context, is_admin_role
from db.models import AuditLog, LLMProvider, SecurityAuditEvent
from db.session import get_db
from services.llm_provider_urls import (
    LLM_BASE_URL_NOT_ALLOWED,
    validate_llm_provider_base_url_async,
)
from services.llm_provider_readiness import is_llm_provider_configured

router = APIRouter(prefix="/api/llm-providers", tags=["llm-providers"])


class LLMProviderCreate(BaseModel):
    """Represent l l m provider create."""  # pragma: no cover
    name: str
    provider_type: str
    base_url: Optional[str] = None
    model_identifier: Optional[str] = None
    embedding_model: Optional[str] = None
    api_key: Optional[str] = None
    is_active: bool = False


class LLMProviderUpdate(BaseModel):
    """Represent l l m provider update."""  # pragma: no cover
    name: Optional[str] = None
    provider_type: Optional[str] = None
    base_url: Optional[str] = None
    model_identifier: Optional[str] = None
    embedding_model: Optional[str] = None
    api_key: Optional[str] = None
    is_active: Optional[bool] = None


class LLMProviderResponse(BaseModel):
    """Represent a response payload for l l m provider."""  # pragma: no cover
    id: int
    name: str
    provider_type: str
    base_url: Optional[str] = None
    model_identifier: Optional[str] = None
    embedding_model: Optional[str] = None
    is_active: bool
    configured: bool
    fingerprint: Optional[str] = None
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


def _get_fingerprint(api_key: str | None) -> str | None:
    if not api_key:  # pragma: no cover
        return None
    if len(api_key) > 8:
        return f"***{api_key[-4:]}"
    return "***"


async def _validated_base_url(value: str | None) -> str | None:
    try:  # pragma: no cover
        return await validate_llm_provider_base_url_async(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=LLM_BASE_URL_NOT_ALLOWED) from exc


def _optional_stripped_text(value: str | None) -> str | None:
    if value is None:  # pragma: no cover
        return None
    stripped = value.strip()
    return stripped or None


def _provider_response(provider: LLMProvider) -> LLMProviderResponse:
    return LLMProviderResponse(  # pragma: no cover
        id=provider.id,
        name=provider.name,
        provider_type=provider.provider_type,
        base_url=provider.base_url,
        model_identifier=provider.model_identifier,
        embedding_model=provider.embedding_model,
        is_active=provider.is_active,
        configured=is_llm_provider_configured(provider),
        fingerprint=_get_fingerprint(provider.api_key),
        updated_at=provider.updated_at,
    )


async def check_admin_access(
    auth_context: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    """Handle check admin access."""  # pragma: no cover
    if not is_admin_role(auth_context.role):
        raise HTTPException(
            status_code=403, detail="Organization admin access required"
        )
    return auth_context


def _required_provider_organization(auth_context: AuthContext) -> str:
    if not auth_context.organization_id:  # pragma: no cover
        raise HTTPException(status_code=403, detail="Organization scope required")
    return auth_context.organization_id


def _provider_owner_filter(auth_context: AuthContext):
    return LLMProvider.organization_id == _required_provider_organization(auth_context)  # pragma: no cover


def _security_audit_event(
    auth_context: AuthContext,
    *,
    event_action: str,
    resource_uid: str | None,
    detail_text: str,
) -> SecurityAuditEvent:
    return SecurityAuditEvent(  # pragma: no cover
        actor_user_id=auth_context.user_id,
        actor_role=auth_context.role,
        organization_id=auth_context.organization_id,
        workspace_id=auth_context.workspace_id,
        event_action=event_action,
        resource_type="llm_provider",
        resource_uid=resource_uid,
        evidence_source="api.llm_providers",
        detail_text=detail_text,
    )


def _provider_resource_uid(auth_context: AuthContext, provider_id: int) -> str:
    scope = auth_context.organization_id or auth_context.user_id  # pragma: no cover
    digest = hashlib.sha256(f"{scope}:{provider_id}".encode("utf-8")).hexdigest()
    return f"llm_provider:{digest[:16]}"


@router.get("", response_model=List[LLMProviderResponse])
async def list_providers(
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(check_admin_access),
):
    """List providers."""  # pragma: no cover
    result = await db.execute(
        select(LLMProvider).where(_provider_owner_filter(auth_context))
    )
    providers = result.scalars().all()

    responses = []
    for p in providers:
        responses.append(_provider_response(p))
    return responses


@router.post("", response_model=LLMProviderResponse)
async def create_provider(
    data: LLMProviderCreate,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(check_admin_access),
):
    """Create provider."""  # pragma: no cover
    provider = LLMProvider(
        user_id=auth_context.user_id,
        organization_id=_required_provider_organization(auth_context),
        name=data.name,
        provider_type=data.provider_type,
        base_url=await _validated_base_url(data.base_url),
        model_identifier=_optional_stripped_text(data.model_identifier),
        embedding_model=_optional_stripped_text(data.embedding_model),
        api_key=data.api_key,
        is_active=data.is_active,
    )
    db.add(provider)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Provider name already exists")

    audit = AuditLog(
        user_id=auth_context.user_id,
        action="create",
        resource_type="llm_provider",
        details="Created provider configuration",
    )
    db.add(audit)
    db.add(
        _security_audit_event(
            auth_context,
            event_action="create",
            resource_uid=_provider_resource_uid(auth_context, provider.id),
            detail_text="Created provider configuration",
        )
    )
    try:
        await db.commit()
        await db.refresh(provider)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Provider name already exists")

    return _provider_response(provider)


@router.put("/{provider_id}", response_model=LLMProviderResponse)
async def update_provider(
    provider_id: int,
    data: LLMProviderUpdate,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(check_admin_access),
):
    """Update provider."""  # pragma: no cover
    result = await db.execute(
        select(LLMProvider).where(
            LLMProvider.id == provider_id,
            _provider_owner_filter(auth_context),
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
        provider.base_url = await _validated_base_url(data.base_url)
        updated = True
    if data.model_identifier is not None:
        provider.model_identifier = _optional_stripped_text(data.model_identifier)
        updated = True
    if data.embedding_model is not None:
        provider.embedding_model = _optional_stripped_text(data.embedding_model)
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
            details="Updated provider configuration",
        )
        db.add(audit)
        db.add(
            _security_audit_event(
                auth_context,
                event_action="update",
                resource_uid=_provider_resource_uid(auth_context, provider.id),
                detail_text="Updated provider configuration",
            )
        )
        await db.commit()
        await db.refresh(provider)

    return _provider_response(provider)


@router.delete("/{provider_id}", status_code=204)
async def delete_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(check_admin_access),
):
    """Delete provider."""  # pragma: no cover
    result = await db.execute(
        select(LLMProvider).where(
            LLMProvider.id == provider_id,
            _provider_owner_filter(auth_context),
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
        details="Deleted provider configuration",
    )
    db.add(audit)
    db.add(
        _security_audit_event(
            auth_context,
            event_action="delete",
            resource_uid=_provider_resource_uid(auth_context, provider.id),
            detail_text="Deleted provider configuration",
        )
    )
    await db.commit()
