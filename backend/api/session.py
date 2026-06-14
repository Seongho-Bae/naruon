from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.auth import AuthContext, get_auth_context


router = APIRouter(prefix="/api/auth", tags=["auth"])


class SessionResponse(BaseModel):
    user_id: str
    organization_id: str | None
    workspace_id: str


@router.get("/session", response_model=SessionResponse)
async def current_session(
    auth_context: AuthContext = Depends(get_auth_context),
) -> SessionResponse:
    return SessionResponse(
        user_id=auth_context.user_id,
        organization_id=auth_context.organization_id,
        workspace_id=auth_context.workspace_id,
    )
