from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from api.auth import get_auth_context, AuthContext
from db.session import get_db
from services.webdav_service import webdav_service

router = APIRouter(prefix="/api/webdav", tags=["webdav"])

class WebdavAccountResponse(BaseModel):
    account_id: int
    server_url: str
    username: str

class ProjectFolderResponse(BaseModel):
    folder_id: int
    project_name: str
    webdav_path: str

class WritebackIntentRequest(BaseModel):
    target_account_id: int | None = None

class WritebackIntentResponse(BaseModel):
    intent: str
    source_id: int | None
    server_url: str | None
    requires_if_match: bool
    provenance: str
    status: str | None = None
    message: str | None = None

class KnowledgeMaterializationIntentRequest(BaseModel):
    source_task_id: str
    target_account_id: int | None = None

class KnowledgeMaterializationIntentResponse(BaseModel):
    intent: str
    status: str
    task_id: str
    source_type: str
    source_email_id: str | None
    source_thread_id: str | None
    source_id: int | None
    server_url: str | None
    target_path: str
    requires_if_match: bool
    provenance: str
    provider_write_executed: bool
    audit_event: str

@router.get("/accounts", response_model=List[WebdavAccountResponse])
async def get_webdav_accounts(
    auth_context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    user_id = auth_context.user_id
    return await webdav_service.get_connected_accounts_from_db(db, user_id)

@router.get("/folders", response_model=List[ProjectFolderResponse])
async def get_project_folders(
    auth_context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    user_id = auth_context.user_id
    return await webdav_service.get_project_folders_from_db(db, user_id)

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
        target_account_id=req.target_account_id,
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
        target_account_id=req.target_account_id,
    )
    if result.get("status") == "error":
        status_code = (
            404 if "not found" in str(result.get("message", "")).lower() else 422
        )
        raise HTTPException(status_code=status_code, detail=result.get("message"))
    return KnowledgeMaterializationIntentResponse(**result)
