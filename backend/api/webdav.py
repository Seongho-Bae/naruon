from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List

from api.auth import get_auth_context, AuthContext
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

@router.get("/accounts", response_model=List[WebdavAccountResponse])
async def get_webdav_accounts(auth_context: AuthContext = Depends(get_auth_context)):
    user_id = auth_context.user_id
    return webdav_service.get_connected_accounts(user_id)

@router.get("/folders", response_model=List[ProjectFolderResponse])
async def get_project_folders(auth_context: AuthContext = Depends(get_auth_context)):
    user_id = auth_context.user_id
    return webdav_service.get_project_folders(user_id)

@router.post("/writeback-intent", response_model=WritebackIntentResponse)
async def get_webdav_writeback_intent(req: WritebackIntentRequest, auth_context: AuthContext = Depends(get_auth_context)):
    user_id = auth_context.user_id
    result = webdav_service.determine_webdav_writeback_intent(user_id, target_account_id=req.target_account_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=422, detail=result.get("message"))
    return WritebackIntentResponse(**result)
