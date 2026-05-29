from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from api.auth import get_auth_context, AuthContext
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
    source_id: str
    display_label: str
    writeback_enabled: bool
    etag: str | None = None

class ProjectFolderResponse(BaseModel):
    folder_uid: str
    project_name: str
    webdav_path: str
    owner_user_id: str
    organization_id: str | None

class WritebackIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_source_id: str | None = None

class WritebackIntentResponse(BaseModel):
    intent: str
    source_id: str | None
    target_label: str | None
    requires_if_match: bool
    if_match: str | None = None
    provenance: str
    status: str | None = None
    message: str | None = None

class KnowledgeMaterializationIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_task_id: str
    target_source_id: str | None = None

class KnowledgeMaterializationIntentResponse(BaseModel):
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

@router.get("/accounts", response_model=List[WebdavAccountResponse])
async def get_webdav_accounts(
    auth_context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    user_id = auth_context.user_id
    return await webdav_service.get_connected_accounts_from_db(
        db,
        user_id,
        auth_context.organization_id,
    )

@router.get("/folders", response_model=List[ProjectFolderResponse])
async def get_project_folders(
    auth_context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
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
    user_id = auth_context.user_id
    result = await webdav_service.determine_webdav_writeback_intent_from_db(
        db,
        user_id,
        auth_context.organization_id,
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
    result = await webdav_service.determine_knowledge_materialization_intent_from_db(
        db,
        auth_context.user_id,
        auth_context.organization_id,
        req.source_task_id,
        target_source_id=req.target_source_id,
    )
    if result.get("status") == "error":
        status_code = WEB_DAV_ERROR_STATUS_CODES.get(
            str(result.get("error_code") or ""),
            422,
        )
        raise HTTPException(status_code=status_code, detail=result.get("message"))
    return KnowledgeMaterializationIntentResponse(**result)
