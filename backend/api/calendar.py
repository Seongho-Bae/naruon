from collections.abc import Sequence
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from api.auth import AuthContext, ensure_organization_access, get_auth_context
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
    organization_id: str
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


async def get_writeback_sources(
    auth_context: AuthContext = Depends(get_auth_context),
) -> tuple[WritebackSource, ...]:
    """
    Return server-authoritative writeback sources for the authenticated user.

    The current slice has no persisted connector/source registry yet, so the
    production default is intentionally empty. Tests may override this dependency
    with fixture-owned sources, and the future connector registry should replace
    this placeholder with a database-backed lookup scoped by `auth_context`.
    """
    return ()


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
    target_source_id: str | None,
    owner_id: str,
    organization_id: str | None,
) -> WritebackSource | None:
    for source in sources:
        if (
            not source.writeback_enabled
            or "write" not in source.capabilities
            or source.protocol not in CUSTOMER_OWNED_PROTOCOLS
            or (target_source_id is not None and source.source_id != target_source_id)
            or source.owner_id != owner_id
            or source.organization_id != organization_id
        ):
            continue
        return source
    return None


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
        results = []
        for safe_todo in safe_todos:
            event = await create_calendar_event(safe_todo, user_token)
            results.append(event)
        return {"synced": len(results), "events": results}
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
    target_source = _select_writeback_source(
        available_sources,
        request.target_source_id,
        auth_context.user_id,
        auth_context.organization_id,
    )
    if target_source is None:
        raise HTTPException(
            status_code=422, detail="No customer-owned writeback source is available"
        )

    ensure_organization_access(auth_context, target_source.organization_id)

    if target_source.owner_id != auth_context.user_id:
        raise HTTPException(
            status_code=403, detail="Writeback source belongs to a different owner"
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
