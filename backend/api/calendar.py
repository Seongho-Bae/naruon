from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.auth import AuthContext, get_auth_context
from services.calendar_service import create_calendar_event
from services.exceptions import CalendarServiceError

router = APIRouter(prefix="/api/calendar")


class SyncRequest(BaseModel):
    todos: list[str]
    user_token: dict


class WritebackSource(BaseModel):
    source_id: str
    provider: str
    protocol: Literal["caldav", "carddav", "webdav", "local"]
    owner_id: str
    capabilities: list[str]
    writeback_enabled: bool
    etag: str | None = None


class WritebackIntentRequest(BaseModel):
    action: Literal["create", "update"]
    summary: str
    sources: list[WritebackSource]


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


@router.post("/sync")
async def sync_todos(request: SyncRequest):
    try:
        results = []
        for todo in request.todos:
            event = await create_calendar_event(todo, request.user_token)
            results.append(event)
        return {"synced": len(results), "events": results}
    except CalendarServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/writeback-intent", response_model=WritebackIntentResponse)
async def create_writeback_intent(
    request: WritebackIntentRequest,
    auth_context: AuthContext = Depends(get_auth_context),
) -> WritebackIntentResponse:
    target_source = next(
        (
            source
            for source in request.sources
            if source.writeback_enabled
            and "write" in source.capabilities
            and source.protocol in CUSTOMER_OWNED_PROTOCOLS
        ),
        None,
    )
    if target_source is None:
        raise HTTPException(status_code=422, detail="No customer-owned writeback source is available")

    if target_source.owner_id != auth_context.user_id:
        raise HTTPException(status_code=403, detail="Writeback source belongs to a different owner")

    requires_if_match = request.action == "update"
    if requires_if_match and not target_source.etag:
        raise HTTPException(status_code=409, detail="ETag is required for writeback updates")

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
