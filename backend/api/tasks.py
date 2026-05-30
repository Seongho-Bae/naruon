import datetime
from typing import Literal, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import AuthContext, get_auth_context
from api.emails import canonical_thread_key
from db.models import Email, TicketTask
from db.session import get_db
from services.reply_tracking_service import check_missing_replies
from services.text_safety import contains_html_markup

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


TaskStatus = Literal["open", "in_progress", "blocked", "done"]
TaskPriority = Literal["low", "normal", "high", "urgent"]
REPLY_SLA_SOURCE_TYPE = "reply_sla"


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


class ReplySlaEscalationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overdue_hours: int = Field(default=48, ge=1, le=720)
    limit: int = Field(default=10, ge=1, le=50)


class ReplySlaPolicyResponse(BaseModel):
    overdue_hours: int


class ReplySlaEscalationResponse(BaseModel):
    evaluated: int
    created: int
    policy: ReplySlaPolicyResponse
    tasks: list[TicketTaskResponse]


class UpdateTicketTaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: TaskStatus | None = None
    priority: TaskPriority | None = None


def _normalize_execution_items(items: list[str]) -> list[str]:
    normalized = []
    for item in items:
        trimmed = item.replace("\x00", "").strip()
        if trimmed:
            if contains_html_markup(trimmed):
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


def _safe_email_subject(subject: str | None) -> str:
    trimmed = (subject or "제목 없음").replace("\x00", " ").strip()
    if not trimmed or contains_html_markup(trimmed):
        return "제목 정리 필요"
    return " ".join(trimmed.split())[:120]


def _reply_sla_task_title(email: Email) -> str:
    return f"답변 SLA 확인: {_safe_email_subject(email.subject)}"


def _email_date_utc(email: Email) -> datetime.datetime:
    message_date = email.date
    if message_date.tzinfo is None:
        return message_date.replace(tzinfo=datetime.timezone.utc)
    return message_date


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


@router.post("/reply-sla-escalations", response_model=ReplySlaEscalationResponse)
async def create_reply_sla_escalations(
    request: ReplySlaEscalationRequest,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
) -> ReplySlaEscalationResponse:
    pending_replies = await check_missing_replies(
        db, auth_context.user_id, auth_context.organization_id
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    overdue_cutoff = now - datetime.timedelta(hours=request.overdue_hours)
    overdue_replies = sorted(
        [
            email
            for email in pending_replies
            if _email_date_utc(email) <= overdue_cutoff
        ],
        key=_email_date_utc,
    )[: request.limit]

    if not overdue_replies:
        return ReplySlaEscalationResponse(
            evaluated=len(pending_replies),
            created=0,
            policy=ReplySlaPolicyResponse(overdue_hours=request.overdue_hours),
            tasks=[],
        )

    email_ids = [email.id for email in overdue_replies]



    existing_result = await db.execute(
        select(TicketTask)
        .where(
            TicketTask.user_id == auth_context.user_id,
            TicketTask.organization_id == auth_context.organization_id,
            TicketTask.related_email_id.in_(email_ids),
            TicketTask.source_type == REPLY_SLA_SOURCE_TYPE,
        )
        .order_by(TicketTask.updated_at.desc())
    )

    existing_tasks_by_email = {}
    for task in existing_result.scalars().all():
        if task.related_email_id not in existing_tasks_by_email:
            existing_tasks_by_email[task.related_email_id] = task



    created_count = 0
    escalated_tasks: list[tuple[TicketTask, str | None]] = []

    for email in overdue_replies:
        if email.id in existing_tasks_by_email:
            task = existing_tasks_by_email[email.id]
            if task.status != "done":
                task.title = _reply_sla_task_title(email)
                task.status = "blocked"
                task.priority = "urgent"
                task.related_thread_id = canonical_thread_key(email)
                task.updated_at = now
            escalated_tasks.append((task, email.message_id))
        else:
            task = TicketTask(
                user_id=auth_context.user_id,
                organization_id=auth_context.organization_id,
                title=_reply_sla_task_title(email),
                status="blocked",
                priority="urgent",
                source_type=REPLY_SLA_SOURCE_TYPE,
                related_email_id=email.id,
                related_thread_id=canonical_thread_key(email),
            )
            db.add(task)
            created_count += 1
            escalated_tasks.append((task, email.message_id))

    try:
        if created_count > 0 or any(
            email.id in existing_tasks_by_email for email in overdue_replies
        ):
            await db.commit()

            # Fetch updated values efficiently instead of looping db.refresh.
            if created_count > 0:
                refreshed_result = await db.execute(
                    select(TicketTask)
                    .where(
                        TicketTask.user_id == auth_context.user_id,
                        TicketTask.organization_id == auth_context.organization_id,
                        TicketTask.related_email_id.in_(email_ids),
                        TicketTask.source_type == REPLY_SLA_SOURCE_TYPE,
                    )
                    .order_by(TicketTask.updated_at.desc())
                )
                refreshed_tasks_by_email = {
                    t.related_email_id: t for t in refreshed_result.scalars().all()
                }

                # Replace un-refreshed tasks to avoid validation errors.
                for i in range(len(escalated_tasks)):
                    task, message_id = escalated_tasks[i]
                    if task.related_email_id in refreshed_tasks_by_email:
                        escalated_tasks[i] = (
                            refreshed_tasks_by_email[task.related_email_id],
                            message_id,
                        )
    except IntegrityError:
        await db.rollback()
        created_count = 0
        escalated_tasks.clear()

        for email in overdue_replies:
            task = TicketTask(
                user_id=auth_context.user_id,
                organization_id=auth_context.organization_id,
                title=_reply_sla_task_title(email),
                status="blocked",
                priority="urgent",
                source_type=REPLY_SLA_SOURCE_TYPE,
                related_email_id=email.id,
                related_thread_id=canonical_thread_key(email),
            )
            try:
                db.add(task)
                await db.commit()
                await db.refresh(task)
                created_count += 1
            except IntegrityError:
                await db.rollback()
                existing_result = await db.execute(
                    select(TicketTask)
                    .where(
                        TicketTask.user_id == auth_context.user_id,
                        TicketTask.organization_id == auth_context.organization_id,
                        TicketTask.related_email_id == email.id,
                        TicketTask.source_type == REPLY_SLA_SOURCE_TYPE,
                    )
                    .order_by(TicketTask.updated_at.desc())
                )
                existing_tasks_fallback = existing_result.scalars().all()
                if not existing_tasks_fallback:
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "error_code": "reply_sla_task_conflict",
                            "message": "Reply SLA task conflict",
                        },
                    ) from None
                task = existing_tasks_fallback[0]

                if task.status != "done":
                    task.title = _reply_sla_task_title(email)
                    task.status = "blocked"
                    task.priority = "urgent"
                    task.related_thread_id = canonical_thread_key(email)
                    task.updated_at = now
                    await db.commit()
                    await db.refresh(task)
            escalated_tasks.append((task, email.message_id))

    return ReplySlaEscalationResponse(
        evaluated=len(pending_replies),
        created=created_count,
        policy=ReplySlaPolicyResponse(overdue_hours=request.overdue_hours),
        tasks=[
            _task_response(task, source_email_id)
            for task, source_email_id in escalated_tasks
        ],
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


@router.patch("/{task_uid}", response_model=TicketTaskResponse)
async def update_ticket_task(
    task_uid: str,
    request: UpdateTicketTaskRequest,
    db: AsyncSession = Depends(get_db),
    auth_context: AuthContext = Depends(get_auth_context),
) -> TicketTaskResponse:
    if request.status is None and request.priority is None:
        raise HTTPException(
            status_code=422, detail="At least one ticket field is required"
        )

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
            TicketTask.task_uid == task_uid,
            TicketTask.user_id == auth_context.user_id,
            TicketTask.organization_id == auth_context.organization_id,
        )
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")

    task, source_email_id = row
    if request.status is not None:
        task.status = request.status
    if request.priority is not None:
        task.priority = request.priority
    task.updated_at = datetime.datetime.now(datetime.timezone.utc)

    await db.commit()
    await db.refresh(task)
    return _task_response(task, source_email_id)


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
