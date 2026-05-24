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

@router.get("/accounts", response_model=List[WebdavAccountResponse])
async def get_webdav_accounts(auth_context: AuthContext = Depends(get_auth_context)):
    user_id = auth_context.user_id
    return webdav_service.get_connected_accounts(user_id)

@router.get("/folders", response_model=List[ProjectFolderResponse])
async def get_project_folders(auth_context: AuthContext = Depends(get_auth_context)):
    user_id = auth_context.user_id
    return webdav_service.get_project_folders(user_id)
