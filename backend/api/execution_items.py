import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import AuthContext, get_auth_context
from db.models import Email, ExecutionItem
from db.session import get_db

router = APIRouter(prefix="/api/execution-items")


class ExecutionItemResponse(BaseModel):
    id: int
    user_id: str
    organization_id: str | None = None
    workspace_id: str
    source_mailbox_account_id: int | None = None
    source_email_id: int | None = None
    source_thread_id: str | None = None
    source_message_id: str | None = None
    source_snippet: str | None = None
    title: str
    sender: str
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    completed_at: datetime.datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ExecutionItemListResponse(BaseModel):
    items: list[ExecutionItemResponse]


class QueueExecutionItemRequest(BaseModel):
    email_id: int


class UpdateExecutionItemRequest(BaseModel):
    status: Literal["queued", "done"]


def _snapshot_email_fields(item: ExecutionItem, email: Email) -> None:
    item.source_mailbox_account_id = email.mailbox_account_id
    item.source_email_id = email.id
    item.source_thread_id = email.thread_id
    item.source_message_id = email.message_id
    item.source_snippet = email.body[:200] + ("..." if len(email.body) > 200 else "")
    item.title = email.subject or "(제목 없음)"
    item.sender = email.sender


@router.get("", response_model=ExecutionItemListResponse)
async def list_execution_items(
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    result = await db.execute(
        select(ExecutionItem).where(
            ExecutionItem.user_id == auth_context.user_id,
            ExecutionItem.workspace_id == auth_context.workspace_id,
        )
    )
    items = sorted(
        result.scalars().all(), key=lambda item: item.updated_at, reverse=True
    )
    return {"items": items}


@router.post("/from-email")
async def queue_execution_item_from_email(
    request: QueueExecutionItemRequest,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    email_result = await db.execute(
        select(Email).where(
            Email.id == request.email_id, Email.user_id == auth_context.user_id
        )
    )
    email = email_result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Source email not found")

    result = await db.execute(
        select(ExecutionItem).where(
            ExecutionItem.user_id == auth_context.user_id,
            ExecutionItem.workspace_id == auth_context.workspace_id,
            ExecutionItem.source_email_id == request.email_id,
        )
    )
    item = result.scalar_one_or_none()
    now = datetime.datetime.now(datetime.timezone.utc)

    if item:
        _snapshot_email_fields(item, email)
        item.status = "queued"
        item.completed_at = None
        item.updated_at = now
    else:
        item = ExecutionItem(
            user_id=auth_context.user_id,
            organization_id=auth_context.organization_id,
            workspace_id=auth_context.workspace_id,
            source_mailbox_account_id=email.mailbox_account_id,
            source_email_id=email.id,
            source_thread_id=email.thread_id,
            source_message_id=email.message_id,
            source_snippet=email.body[:200] + ("..." if len(email.body) > 200 else ""),
            title=email.subject or "(제목 없음)",
            sender=email.sender,
            status="queued",
            created_at=now,
            updated_at=now,
        )
        db.add(item)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        existing_result = await db.execute(
            select(ExecutionItem).where(
                ExecutionItem.user_id == auth_context.user_id,
                ExecutionItem.workspace_id == auth_context.workspace_id,
                ExecutionItem.source_email_id == request.email_id,
            )
        )
        item = existing_result.scalar_one_or_none()
        if not item:
            raise
    await db.refresh(item)
    return {"item": item}


@router.patch("/{item_id}")
async def update_execution_item(
    item_id: int,
    request: UpdateExecutionItemRequest,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
):
    result = await db.execute(
        select(ExecutionItem).where(
            ExecutionItem.id == item_id,
            ExecutionItem.user_id == auth_context.user_id,
            ExecutionItem.workspace_id == auth_context.workspace_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Execution item not found")

    item.status = request.status
    item.updated_at = datetime.datetime.now(datetime.timezone.utc)
    item.completed_at = item.updated_at if request.status == "done" else None

    await db.commit()
    await db.refresh(item)
    return {"item": item}
