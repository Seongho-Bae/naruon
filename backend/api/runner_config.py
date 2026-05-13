import datetime
import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user_role, get_current_workspace_id
from db.models import WorkspaceRunnerConfig
from db.session import get_db

router = APIRouter(prefix="/api/runner-config", tags=["runner-config"])


class RunnerConfigResponse(BaseModel):
    workspace_id: str
    configured: bool
    fingerprint: str | None = None
    updated_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class RunnerRotateResponse(BaseModel):
    workspace_id: str
    registration_token: str


def _check_org_admin(user_role: str = Depends(get_current_user_role)) -> str:
    if user_role != "organization_admin":
        raise HTTPException(status_code=403, detail="Organization admin access required")
    return user_role


def _fingerprint(token: str | None) -> str | None:
    if not token:
        return None
    return f"***{hashlib.sha256(token.encode('utf-8')).hexdigest()[:8]}"


@router.get("", response_model=RunnerConfigResponse)
async def get_runner_config(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(_check_org_admin),
    workspace_id: str = Depends(get_current_workspace_id),
):
    result = await db.execute(
        select(WorkspaceRunnerConfig).where(WorkspaceRunnerConfig.workspace_id == workspace_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        return RunnerConfigResponse(workspace_id=workspace_id, configured=False, fingerprint=None, updated_at=None)

    try:
        return RunnerConfigResponse(
            workspace_id=config.workspace_id,
            configured=bool(config.registration_token),
            fingerprint=_fingerprint(config.registration_token),
            updated_at=config.updated_at,
        )
    except Exception as exc:
        if "ENCRYPTION_KEY is required" not in str(exc):
            raise
        raise HTTPException(
            status_code=503,
            detail="Server encryption key is not configured. Contact your workspace administrator.",
        ) from exc


@router.post("/rotate", response_model=RunnerRotateResponse)
async def rotate_runner_token(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(_check_org_admin),
    workspace_id: str = Depends(get_current_workspace_id),
):
    result = await db.execute(
        select(WorkspaceRunnerConfig).where(WorkspaceRunnerConfig.workspace_id == workspace_id)
    )
    config = result.scalar_one_or_none()

    token = f"nrn_{secrets.token_urlsafe(24)}"
    if not config:
        config = WorkspaceRunnerConfig(workspace_id=workspace_id, registration_token=token)
        db.add(config)
    else:
        config.registration_token = token

    try:
        await db.commit()
        await db.refresh(config)
    except Exception as exc:
        if "ENCRYPTION_KEY is required" not in str(exc):
            raise
        raise HTTPException(
            status_code=503,
            detail="Server encryption key is not configured. Contact your workspace administrator.",
        ) from exc
    return RunnerRotateResponse(workspace_id=config.workspace_id, registration_token=token)
