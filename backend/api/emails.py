from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, func, or_, select, text
from collections.abc import Sequence
from db.session import get_db
from db.models import Email, EmailSendAttempt, TenantConfig
from pydantic import BaseModel, EmailStr, Field, field_validator
import datetime
from services.email_client import send_email
from services.threading_service import normalize_message_id
import logging
from api.auth import get_current_user
from core.config import settings
from core.network_targets import MailTargetValidationError, validate_mail_server_target

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/emails")


async def enforce_email_send_rate_limit(db: AsyncSession, current_user: str) -> None:
    """Limit outbound email sends per authenticated user in a DB-backed window."""
    max_per_window = settings.EMAIL_SEND_MAX_PER_WINDOW
    window_seconds = settings.EMAIL_SEND_RATE_LIMIT_WINDOW_SECONDS
    if max_per_window <= 0 or window_seconds <= 0:
        return

    now = datetime.datetime.now(datetime.timezone.utc)
    window_start = now - datetime.timedelta(seconds=window_seconds)
    await db.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
        {"lock_key": f"email-send-rate-limit:{current_user}"},
    )
    await db.execute(
        delete(EmailSendAttempt).where(EmailSendAttempt.attempted_at < window_start)
    )
    attempts_in_window = await db.scalar(
        select(func.count())
        .select_from(EmailSendAttempt)
        .where(
            EmailSendAttempt.user_id == current_user,
            EmailSendAttempt.attempted_at >= window_start,
        )
    )
    if (attempts_in_window or 0) >= max_per_window:
        raise HTTPException(status_code=429, detail="Email send rate limit exceeded")

    db.add(EmailSendAttempt(user_id=current_user, attempted_at=now))
    await db.commit()


def canonical_thread_key(email: Email) -> str:
    return (
        normalize_message_id(email.thread_id)
        or normalize_message_id(email.message_id)
        or email.message_id
    )


def thread_lookup_values(thread_id: str) -> list[str]:
    normalized = normalize_message_id(thread_id) or thread_id
    return list({thread_id, normalized, f"<{normalized}>"})


def email_belongs_to_user(email: Email, current_user: str) -> bool:
    """Return whether a loaded email belongs to the authenticated principal."""
    return email.user_id == current_user


def visible_emails_for_user(emails: Sequence[Email], current_user: str) -> list[Email]:
    """Filter loaded rows as a defense-in-depth guard for object authorization."""
    return [email for email in emails if email_belongs_to_user(email, current_user)]


class EmailListItem(BaseModel):
    id: int
    thread_id: str | None = None
    subject: str | None
    sender: str
    reply_to: str | None = None
    date: datetime.datetime
    snippet: str
    reply_count: int | None = None


class EmailDetailResponse(BaseModel):
    id: int
    message_id: str
    thread_id: str | None = None
    sender: str
    reply_to: str | None = None
    recipients: str | None
    subject: str | None
    date: datetime.datetime
    body: str
    in_reply_to: str | None = None
    references: str | None = None


@router.get("", response_model=dict[str, list[EmailListItem]])
async def get_emails(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    candidate_window = min(max(limit * 10, 200), 2000)
    result = await db.execute(
        select(Email)
        .where(Email.user_id == current_user)
        .order_by(Email.date.desc())
        .limit(candidate_window)
    )
    emails = visible_emails_for_user(result.scalars().all(), current_user)
    emails = sorted(emails, key=lambda item: item.date)

    grouped = {}
    reply_counts = {}
    for email in emails:
        group_key = canonical_thread_key(email)
        if group_key not in grouped:
            grouped[group_key] = email
            reply_counts[group_key] = 1
        else:
            reply_counts[group_key] += 1
            if email.date > grouped[group_key].date:
                grouped[group_key] = email

    sorted_groups = sorted(grouped.values(), key=lambda x: x.date, reverse=True)[:limit]

    items = []
    for email in sorted_groups:
        group_key = canonical_thread_key(email)
        snippet = email.body[:100] + "..." if len(email.body) > 100 else email.body
        items.append(
            EmailListItem(
                id=email.id,
                subject=email.subject,
                sender=email.sender,
                reply_to=email.reply_to,
                date=email.date,
                snippet=snippet,
                thread_id=group_key,
                reply_count=reply_counts[group_key],
            )
        )
    return {"emails": items}


@router.get("/{email_id}", response_model=EmailDetailResponse)
async def get_email(
    email_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    result = await db.execute(
        select(Email).where(Email.id == email_id, Email.user_id == current_user)
    )
    email = result.scalar_one_or_none()
    if not email or not email_belongs_to_user(email, current_user):
        raise HTTPException(status_code=404, detail="Email not found")
    return EmailDetailResponse(
        id=email.id,
        message_id=email.message_id,
        sender=email.sender,
        reply_to=email.reply_to,
        recipients=email.recipients,
        subject=email.subject,
        date=email.date,
        body=email.body,
        thread_id=canonical_thread_key(email),
        in_reply_to=email.in_reply_to,
        references=email.references,
    )


@router.get(
    "/thread/{thread_id:path}", response_model=dict[str, list[EmailDetailResponse]]
)
async def get_email_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    lookup_values = thread_lookup_values(thread_id)
    result = await db.execute(
        select(Email)
        .where(
            Email.user_id == current_user,
            or_(
                Email.thread_id.in_(lookup_values), Email.message_id.in_(lookup_values)
            ),
        )
        .order_by(Email.date.asc())
    )
    emails = visible_emails_for_user(result.scalars().all(), current_user)
    emails = sorted(emails, key=lambda item: item.date)
    if not emails:
        raise HTTPException(status_code=404, detail="Thread not found")

    items = []
    for email in emails:
        items.append(
            EmailDetailResponse(
                id=email.id,
                message_id=email.message_id,
                sender=email.sender,
                reply_to=email.reply_to,
                recipients=email.recipients,
                subject=email.subject,
                date=email.date,
                body=email.body,
                thread_id=canonical_thread_key(email),
                in_reply_to=email.in_reply_to,
                references=email.references,
            )
        )
    return {"thread": items}


class SendEmailRequest(BaseModel):
    to: EmailStr
    subject: str = Field(min_length=1, max_length=180)
    body: str = Field(min_length=1, max_length=20_000)
    in_reply_to: str | None = None  # O3: email threading support
    references: str | None = None

    @field_validator("subject", "body")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field must not be blank")
        return stripped


@router.post("/send")
async def send_email_endpoint(
    request: SendEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    await enforce_email_send_rate_limit(db, current_user)

    try:
        tenant_config = await db.scalar(
            select(TenantConfig).where(TenantConfig.user_id == current_user)
        )

        if (
            not tenant_config
            or not tenant_config.smtp_server
            or not tenant_config.smtp_port
            or not tenant_config.smtp_username
        ):
            raise HTTPException(status_code=400, detail="SMTP is not configured")

        try:
            smtp_server, smtp_port = validate_mail_server_target(
                tenant_config.smtp_server, tenant_config.smtp_port, "smtp"
            )
        except MailTargetValidationError:
            raise HTTPException(status_code=400, detail="SMTP server is not allowed")

        smtp_username = tenant_config.smtp_username

        send_result = await send_email(
            request.to,
            request.subject,
            request.body,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            in_reply_to=request.in_reply_to,
            references=request.references,
        )
        if send_result.get("status") not in {"sent", "simulated"}:
            raise HTTPException(status_code=500, detail="Failed to send email")
        return send_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An internal error occurred while sending the email"
        )
