import datetime
import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from db.models import WorkspaceRunnerConfig
from db.session import get_db

router = APIRouter(prefix="/api/runner-config", tags=["runner-config"])

WORKSPACE_ID = "default-workspace"


class RunnerConfigResponse(BaseModel):
    workspace_id: str
    configured: bool
    fingerprint: str | None = None
    updated_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class RunnerRotateResponse(BaseModel):
    workspace_id: str
    registration_token: str


def _check_org_admin(user_id: str = Depends(get_current_user)) -> str:
    if user_id != "admin":
        raise HTTPException(status_code=403, detail="Organization admin access required")
    return user_id


def _fingerprint(token: str | None) -> str | None:
    if not token:
        return None
    return f"***{hashlib.sha256(token.encode('utf-8')).hexdigest()[:8]}"


@router.get("", response_model=RunnerConfigResponse)
async def get_runner_config(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(_check_org_admin),
):
    result = await db.execute(
        select(WorkspaceRunnerConfig).where(WorkspaceRunnerConfig.workspace_id == WORKSPACE_ID)
    )
    config = result.scalar_one_or_none()

    if not config:
        return RunnerConfigResponse(workspace_id=WORKSPACE_ID, configured=False, fingerprint=None, updated_at=None)

    return RunnerConfigResponse(
        workspace_id=config.workspace_id,
        configured=bool(config.registration_token),
        fingerprint=_fingerprint(config.registration_token),
        updated_at=config.updated_at,
    )


@router.post("/rotate", response_model=RunnerRotateResponse)
async def rotate_runner_token(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(_check_org_admin),
):
    result = await db.execute(
        select(WorkspaceRunnerConfig).where(WorkspaceRunnerConfig.workspace_id == WORKSPACE_ID)
    )
    config = result.scalar_one_or_none()

    token = f"nrn_{secrets.token_urlsafe(24)}"
    if not config:
        config = WorkspaceRunnerConfig(workspace_id=WORKSPACE_ID, registration_token=token)
        db.add(config)
    else:
        config.registration_token = token

    await db.commit()
    await db.refresh(config)
    return RunnerRotateResponse(workspace_id=config.workspace_id, registration_token=token)
