import asyncio
from collections.abc import Sequence
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import (
    AuthContext,
    get_auth_context,
    is_system_admin_role,
    is_tenant_admin_role,
)
from db.models import CalendarWritebackSource
from db.session import get_db
from services.calendar_service import create_calendar_event, validate_calendar_todo_text
from services.exceptions import CalendarServiceError, UnsafeCalendarTodoError

router = APIRouter(prefix="/api/calendar")


class SyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    todos: list[str]


class WritebackSource(BaseModel):
    source_id: str
    provider: str
    protocol: Literal["caldav", "carddav", "webdav", "local"]
    owner_id: str
    organization_id: str | None
    capabilities: list[str]
    writeback_enabled: bool
    etag: str | None = None


class WritebackIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["create", "update"]
    summary: str
    target_source_id: str | None = None


class WritebackIntentResponse(BaseModel):
    workspace_id: str
    target_source_id: str
    protocol: str
    writeback_mode: Literal["customer_owned"]
    requires_if_match: bool
    if_match: str | None
    provenance: dict[str, str]
    audit_event: str


CUSTOMER_OWNED_PROTOCOLS = {"caldav", "carddav", "webdav"}


def _registry_capabilities(source: CalendarWritebackSource) -> list[str]:
    capabilities = ["read"]
    if source.writeback_enabled:
        capabilities.extend(["write", "etag"])
    return capabilities


def _writeback_source_from_registry(
    registry_source: CalendarWritebackSource,
) -> WritebackSource:
    return WritebackSource(
        source_id=registry_source.source_uid,
        provider=registry_source.provider_name,
        protocol=registry_source.source_protocol,
        owner_id=registry_source.user_id,
        organization_id=registry_source.organization_id,
        capabilities=_registry_capabilities(registry_source),
        writeback_enabled=bool(registry_source.writeback_enabled),
        etag=registry_source.etag_value,
    )


def _registry_scope_statement(auth_context: AuthContext):
    statement = (
        select(CalendarWritebackSource)
        .where(CalendarWritebackSource.source_protocol == "caldav")
        .order_by(
            CalendarWritebackSource.created_at.asc(),
            CalendarWritebackSource.source_uid.asc(),
        )
    )
    if is_system_admin_role(auth_context.role):
        return statement

    organization_filter = (
        CalendarWritebackSource.organization_id == auth_context.organization_id
        if auth_context.organization_id is not None
        else CalendarWritebackSource.organization_id.is_(None)
    )
    return statement.where(
        CalendarWritebackSource.user_id == auth_context.user_id,
        organization_filter,
    )


def _has_writeback_capability(source: WritebackSource) -> bool:
    return (
        source.writeback_enabled
        and "write" in source.capabilities
        and source.protocol in CUSTOMER_OWNED_PROTOCOLS
    )


async def get_writeback_sources(
    auth_context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
) -> tuple[WritebackSource, ...]:
    """
    Return server-authoritative writeback sources for the authenticated user.

    This currently resolves persisted CalDAV source-registry rows only. Provider
    mutations are still out of scope: the endpoint returns intent metadata and
    ETag/If-Match requirements so later connector execution can fail closed.
    """
    result = await db.execute(_registry_scope_statement(auth_context))
    return tuple(
        _writeback_source_from_registry(source) for source in result.scalars().all()
    )


@router.get("/writeback-sources", response_model=tuple[WritebackSource, ...])
async def list_writeback_sources(
    available_sources: tuple[WritebackSource, ...] = Depends(get_writeback_sources),
) -> tuple[WritebackSource, ...]:
    return available_sources


async def get_calendar_user_token(
    auth_context: AuthContext = Depends(get_auth_context),
) -> dict | None:
    """
    Return server-authoritative calendar credentials for the authenticated user.

    The current slice has no persisted Google credential registry yet. The
    production default therefore fails closed, and tests may override this
    dependency with fixture-owned credentials. A connector registry can replace
    this placeholder with a lookup scoped by `auth_context`.
    """
    return None


def _select_writeback_source(
    sources: Sequence[WritebackSource],
    owner_id: str,
    organization_id: str | None,
) -> WritebackSource | None:
    for source in sources:
        if (
            not _has_writeback_capability(source)
            or source.owner_id != owner_id
            or source.organization_id != organization_id
        ):
            continue
        return source
    return None


def _find_writeback_source_by_id(
    sources: Sequence[WritebackSource], target_source_id: str
) -> WritebackSource | None:
    for source in sources:
        if source.source_id == target_source_id:
            return source
    return None


def _can_target_writeback_source(
    target_source: WritebackSource, auth_context: AuthContext
) -> bool:
    if is_system_admin_role(auth_context.role):
        return True
    if target_source.organization_id != auth_context.organization_id:
        return False
    return target_source.owner_id == auth_context.user_id


def _authorize_targeted_writeback_source(
    sources: Sequence[WritebackSource],
    target_source_id: str,
    auth_context: AuthContext,
) -> WritebackSource | None:
    target_source = _find_writeback_source_by_id(sources, target_source_id)
    if target_source is None:
        raise HTTPException(
            status_code=403,
            detail="Not authorized for requested writeback source",
        )

    if not _can_target_writeback_source(target_source, auth_context):
        raise HTTPException(
            status_code=403,
            detail="Not authorized for requested writeback source",
        )
    if not _has_writeback_capability(target_source):
        return None
    return target_source


@router.post("/sync")
async def sync_todos(
    request: SyncRequest,
    user_token: dict | None = Depends(get_calendar_user_token),
):
    if user_token is None:
        raise HTTPException(
            status_code=422,
            detail="No server-authoritative calendar credentials are configured",
        )
    try:
        safe_todos = [validate_calendar_todo_text(todo) for todo in request.todos]
        coros = [create_calendar_event(safe_todo, user_token) for safe_todo in safe_todos]
        results = await asyncio.gather(*coros)
        return {"synced": len(results), "events": list(results)}
    except UnsafeCalendarTodoError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except CalendarServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/writeback-intent", response_model=WritebackIntentResponse)
async def create_writeback_intent(
    request: WritebackIntentRequest,
    auth_context: AuthContext = Depends(get_auth_context),
    available_sources: tuple[WritebackSource, ...] = Depends(get_writeback_sources),
) -> WritebackIntentResponse:
    if request.target_source_id is not None:
        target_source = _authorize_targeted_writeback_source(
            available_sources,
            request.target_source_id,
            auth_context,
        )
    else:
        target_source = _select_writeback_source(
            available_sources,
            auth_context.user_id,
            auth_context.organization_id,
        )
    if target_source is None:
        raise HTTPException(
            status_code=422, detail="No customer-owned writeback source is available"
        )

    requires_if_match = request.action == "update"
    if requires_if_match and not target_source.etag:
        raise HTTPException(
            status_code=409, detail="ETag is required for writeback updates"
        )

    return WritebackIntentResponse(
        workspace_id=auth_context.workspace_id,
        target_source_id=target_source.source_id,
        protocol=target_source.protocol,
        writeback_mode="customer_owned",
        requires_if_match=requires_if_match,
        if_match=target_source.etag if requires_if_match else None,
        provenance={
            "created_by": auth_context.user_id,
            "source_provider": target_source.provider,
            "source_protocol": target_source.protocol,
        },
        audit_event="calendar.writeback_intent.created",
    )
