import datetime
import re
from typing import Literal, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import AuthContext, get_auth_context
from api.emails import canonical_thread_key
from db.models import Email, TicketTask
from db.session import get_db

router = APIRouter(prefix="/api/tasks", tags=["tasks"])
HTML_TAG_PATTERN = re.compile(r"<\s*/?\s*[A-Za-z][^>]*>")


TaskStatus = Literal["open", "in_progress", "blocked", "done"]
TaskPriority = Literal["low", "normal", "high", "urgent"]


class CreateTasksFromEmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_email_id: str
    thread_id: str | None = None
    items: list[str]


class TicketTaskResponse(BaseModel):
    id: str
    title: str
    status: TaskStatus
    priority: TaskPriority
    source_type: str
    source_email_id: str | None
    related_thread_id: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class CreateTasksFromEmailResponse(BaseModel):
    created: int
    tasks: list[TicketTaskResponse]


def _normalize_execution_items(items: list[str]) -> list[str]:
    normalized = []
    for item in items:
        trimmed = item.replace("\x00", "").strip()
        if trimmed:
            if HTML_TAG_PATTERN.search(trimmed):
                raise HTTPException(
                    status_code=422, detail="Execution items must be plain text"
                )
            normalized.append(trimmed)
    return normalized


def _email_matches_auth(email: Email, auth_context: AuthContext) -> bool:
    return (
        email.user_id == auth_context.user_id
        and email.organization_id == auth_context.organization_id
    )


def _task_response(task: TicketTask, source_email_id: str | None) -> TicketTaskResponse:
    scoped_thread_id = task.related_thread_id if source_email_id is not None else None
    return TicketTaskResponse(
        id=task.task_uid,
        title=task.title,
        status=cast(TaskStatus, task.status),
        priority=cast(TaskPriority, task.priority),
        source_type=task.source_type,
        source_email_id=source_email_id,
        related_thread_id=scoped_thread_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("", response_model=list[TicketTaskResponse])
async def list_ticket_tasks(
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
) -> list[TicketTaskResponse]:
    result = await db.execute(
        select(TicketTask, Email.message_id)
        .outerjoin(
            Email,
            and_(
                TicketTask.related_email_id == Email.id,
                Email.user_id == auth_context.user_id,
                Email.organization_id == auth_context.organization_id,
            ),
        )
        .where(
            TicketTask.user_id == auth_context.user_id,
            TicketTask.organization_id == auth_context.organization_id,
        )
        .order_by(TicketTask.updated_at.desc())
    )
    return [
        _task_response(task, source_email_id) for task, source_email_id in result.all()
    ]


@router.post("/from-email", response_model=CreateTasksFromEmailResponse)
async def create_tasks_from_email(
    request: CreateTasksFromEmailRequest,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
) -> CreateTasksFromEmailResponse:
    items = _normalize_execution_items(request.items)
    if not items:
        raise HTTPException(
            status_code=422, detail="At least one execution item is required"
        )
    if len(items) > 50:
        raise HTTPException(status_code=422, detail="Too many execution items")

    email_result = await db.execute(
        select(Email).where(
            Email.message_id == request.source_email_id,
            Email.user_id == auth_context.user_id,
            Email.organization_id == auth_context.organization_id,
        )
    )
    email = email_result.scalar_one_or_none()
    if email is None or not _email_matches_auth(email, auth_context):
        raise HTTPException(status_code=404, detail="Source email not found")

    thread_id = canonical_thread_key(email) or request.thread_id
    tasks = [
        TicketTask(
            user_id=auth_context.user_id,
            organization_id=auth_context.organization_id,
            title=item,
            status="open",
            priority="normal",
            source_type="email",
            related_email_id=email.id,
            related_thread_id=thread_id,
        )
        for item in items
    ]
    for task in tasks:
        db.add(task)

    await db.commit()
    for task in tasks:
        await db.refresh(task)

    return CreateTasksFromEmailResponse(
        created=len(tasks),
        tasks=[_task_response(task, email.message_id) for task in tasks],
    )
