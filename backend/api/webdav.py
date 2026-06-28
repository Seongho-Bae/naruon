"""Support backend api webdav."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from api.auth import get_auth_context, AuthContext
from api.runner_ws import manager as runner_manager
from db.session import get_db
from services.webdav_service import webdav_service

router = APIRouter(prefix="/api/webdav", tags=["webdav"])
WEB_DAV_ERROR_STATUS_CODES = {
    "not_found": 404,
    "validation_error": 422,
    "missing_provenance": 422,
    "no_webdav_account": 422,
    "webdav_account_not_found": 422,
}

class WebdavAccountResponse(BaseModel):
    """Represent a response payload for webdav account."""
    source_id: str
    display_label: str
    writeback_enabled: bool
    etag: str | None = None

class ProjectFolderResponse(BaseModel):
    """Represent a response payload for project folder."""
    folder_uid: str
    project_name: str
    webdav_path: str
    owner_user_id: str
    organization_id: str | None

class WritebackIntentRequest(BaseModel):
    """Represent a request payload for writeback intent."""
    model_config = ConfigDict(extra="forbid")

    target_source_id: str | None = None

class WritebackIntentResponse(BaseModel):
    """Represent a response payload for writeback intent."""
    intent: str
    source_id: str | None
    target_label: str | None
    requires_if_match: bool
    if_match: str | None = None
    provenance: str
    status: str | None = None
    message: str | None = None

class KnowledgeMaterializationIntentRequest(BaseModel):
    """Represent a request payload for knowledge materialization intent."""
    model_config = ConfigDict(extra="forbid")

    source_task_id: str
    target_source_id: str | None = None
    execute_provider: bool = False

class KnowledgeMaterializationIntentResponse(BaseModel):
    """Represent a response payload for knowledge materialization intent."""
    intent: str
    status: str
    task_id: str
    source_type: str
    source_email_id: str | None
    source_thread_id: str | None
    source_id: str | None
    target_label: str | None
    target_path: str
    requires_if_match: bool
    if_match: str | None = None
    provenance: str
    provider_write_executed: bool
    audit_event: str
    runner_request_id: str | None = None
    provider_status: int | None = None
    error_code: str | None = None
    retry_item_uid: str | None = None

@router.get("/accounts", response_model=List[WebdavAccountResponse])
async def get_webdav_accounts(
    auth_context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Return webdav accounts."""
    user_id = auth_context.user_id
    return await webdav_service.get_connected_accounts_from_db(
        db,
        user_id,
        auth_context.organization_id,
        auth_context.workspace_id,
    )

@router.get("/folders", response_model=List[ProjectFolderResponse])
async def get_project_folders(
    auth_context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Return project folders."""
    user_id = auth_context.user_id
    return await webdav_service.get_project_folders_from_db(
        db,
        user_id,
        auth_context.organization_id,
    )

@router.post("/writeback-intent", response_model=WritebackIntentResponse)
async def get_webdav_writeback_intent(
    req: WritebackIntentRequest,
    auth_context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Return webdav writeback intent."""
    user_id = auth_context.user_id
    result = await webdav_service.determine_webdav_writeback_intent_from_db(
        db,
        user_id,
        auth_context.organization_id,
        auth_context.workspace_id,
        target_source_id=req.target_source_id,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=422, detail=result.get("message"))
    return WritebackIntentResponse(**result)

@router.post(
    "/knowledge-materialization-intent",
    response_model=KnowledgeMaterializationIntentResponse,
)
async def get_knowledge_materialization_intent(
    req: KnowledgeMaterializationIntentRequest,
    auth_context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Return knowledge materialization intent."""
    result = await webdav_service.determine_knowledge_materialization_intent_from_db(
        db,
        auth_context.user_id,
        auth_context.organization_id,
        auth_context.workspace_id,
        req.source_task_id,
        target_source_id=req.target_source_id,
    )
    if result.get("status") == "error":
        status_code = WEB_DAV_ERROR_STATUS_CODES.get(
            str(result.get("error_code") or ""),
            422,
        )
        raise HTTPException(status_code=status_code, detail=result.get("message"))
    if req.execute_provider:
        dispatch_result = await runner_manager.dispatch_command(
            auth_context.organization_id,
            auth_context.workspace_id,
            _knowledge_materialization_runner_command(result),
        )
        result = _merge_materialization_dispatch_result(result, dispatch_result)
    return KnowledgeMaterializationIntentResponse(**result)


def _knowledge_materialization_runner_command(result: dict) -> dict[str, object]:
    return {
        "action": "write_webdav",
        "account": result["source_id"],
        "source_id": result["source_id"],
        "target_path": result["target_path"],
        "if_match": result.get("if_match"),
        "content_type": "text/markdown; charset=utf-8",
        "content": _knowledge_materialization_content(result),
    }


def _knowledge_materialization_content(result: dict) -> str:
    task_id = str(result["task_id"])
    lines = [
        f"# {task_id}",
        "",
        f"- Source type: {result['source_type']}",
        f"- Source email: {result.get('source_email_id') or 'unknown'}",
        f"- Source thread: {result.get('source_thread_id') or 'unknown'}",
        "",
    ]
    return "\n".join(lines)


def _merge_materialization_dispatch_result(
    intent_result: dict,
    dispatch_result: dict,
) -> dict:
    result = dict(intent_result)
    result["status"] = str(dispatch_result.get("status") or "error")
    result["provider_write_executed"] = bool(
        dispatch_result.get("provider_write_executed", False)
    )
    result["runner_request_id"] = dispatch_result.get("request_id")
    result["provider_status"] = dispatch_result.get("provider_status")
    result["error_code"] = dispatch_result.get("error_code")
    result["retry_item_uid"] = dispatch_result.get("retry_item_uid")
    result["audit_event"] = (
        "webdav.self_sent_knowledge_write.executed"
        if result["provider_write_executed"]
        else "webdav.self_sent_knowledge_write.dispatch_failed"
    )
    return result
