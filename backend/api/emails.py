from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select
from db.session import get_db
from db.models import Email, MailboxAccount, TenantConfig
from pydantic import BaseModel, EmailStr
import datetime
import html
from services.email_client import send_email
from services.email_parser import sanitize_email_html_to_text
from services.threading_service import normalize_message_id
import logging
from api.auth import get_current_user
from api.mailbox_scope import require_owned_mailbox_account

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/emails")


def canonical_thread_key(email: Email) -> str:
    return (
        normalize_message_id(email.thread_id)
        or normalize_message_id(email.message_id)
        or email.message_id
    )


def thread_lookup_values(thread_id: str) -> list[str]:
    normalized = normalize_message_id(thread_id) or thread_id
    return list({thread_id, normalized, f"<{normalized}>"})


def sanitize_email_body_for_response(body: str) -> str:
    decoded_body = html.unescape(body)
    if "<" not in decoded_body or ">" not in decoded_body:
        return body
    return sanitize_email_html_to_text(decoded_body)


class EmailListItem(BaseModel):
    id: int
    mailbox_account_id: int | None = None
    thread_id: str | None = None
    subject: str | None
    sender: str
    reply_to: str | None = None
    date: datetime.datetime
    snippet: str
    reply_count: int | None = None


class EmailDetailResponse(BaseModel):
    id: int
    mailbox_account_id: int | None = None
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
    mailbox_account_id: int | None = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    await require_owned_mailbox_account(db, current_user, mailbox_account_id)

    candidate_window = min(max(limit * 10, 200), 2000)
    statement = select(Email).where(Email.user_id == current_user)
    if mailbox_account_id is not None:
        statement = statement.where(Email.mailbox_account_id == mailbox_account_id)
    result = await db.execute(
        statement.order_by(Email.date.desc()).limit(candidate_window)
    )
    emails = result.scalars().all()
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
        safe_body = sanitize_email_body_for_response(email.body)
        snippet = safe_body[:100] + "..." if len(safe_body) > 100 else safe_body
        items.append(
            EmailListItem(
                id=email.id,
                mailbox_account_id=email.mailbox_account_id,
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
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return EmailDetailResponse(
        id=email.id,
        mailbox_account_id=email.mailbox_account_id,
        message_id=email.message_id,
        sender=email.sender,
        reply_to=email.reply_to,
        recipients=email.recipients,
        subject=email.subject,
        date=email.date,
        body=sanitize_email_body_for_response(email.body),
        thread_id=canonical_thread_key(email),
        in_reply_to=email.in_reply_to,
        references=email.references,
    )


@router.get(
    "/thread/{thread_id:path}", response_model=dict[str, list[EmailDetailResponse]]
)
async def get_email_thread(
    thread_id: str,
    mailbox_account_id: int | None = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    await require_owned_mailbox_account(db, current_user, mailbox_account_id)

    lookup_values = thread_lookup_values(thread_id)
    statement = select(Email).where(
        Email.user_id == current_user,
        or_(Email.thread_id.in_(lookup_values), Email.message_id.in_(lookup_values)),
    )
    if mailbox_account_id is not None:
        statement = statement.where(
            or_(
                Email.mailbox_account_id == mailbox_account_id,
                Email.mailbox_account_id.is_(None),
            )
        )
    result = await db.execute(statement.order_by(Email.date.asc()))
    emails = result.scalars().all()
    emails = sorted(emails, key=lambda item: item.date)
    if not emails:
        raise HTTPException(status_code=404, detail="Thread not found")

    items = []
    for email in emails:
        items.append(
            EmailDetailResponse(
                id=email.id,
                mailbox_account_id=email.mailbox_account_id,
                message_id=email.message_id,
                sender=email.sender,
                reply_to=email.reply_to,
                recipients=email.recipients,
                subject=email.subject,
                date=email.date,
                body=sanitize_email_body_for_response(email.body),
                thread_id=canonical_thread_key(email),
                in_reply_to=email.in_reply_to,
                references=email.references,
            )
        )
    return {"thread": items}


class SendEmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    mailbox_account_id: int | None = None
    in_reply_to: str | None = None  # O3: email threading support
    references: str | None = None


@router.post("/send")
async def send_email_endpoint(
    request: SendEmailRequest,
    user_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    if user_id and user_id != current_user:
        raise HTTPException(status_code=403, detail="Not authorized")
    target_user_id = user_id or current_user

    try:
        mailbox_account = None
        if request.mailbox_account_id is not None:
            mailbox_account = await db.scalar(
                select(MailboxAccount).where(
                    MailboxAccount.id == request.mailbox_account_id,
                    MailboxAccount.user_id == target_user_id,
                )
            )
            if not mailbox_account:
                raise HTTPException(status_code=404, detail="Mailbox account not found")
        else:
            mailbox_account = await db.scalar(
                select(MailboxAccount).where(
                    MailboxAccount.user_id == target_user_id,
                    MailboxAccount.is_default_reply.is_(True),
                    MailboxAccount.is_active.is_(True),
                )
            )

        if (
            mailbox_account
            and mailbox_account.smtp_server
            and mailbox_account.smtp_port
            and mailbox_account.smtp_username
        ):
            try:
                smtp_server = mailbox_account.smtp_server
                smtp_port = mailbox_account.smtp_port
                smtp_username = mailbox_account.smtp_username
                smtp_password = mailbox_account.smtp_password
            except Exception as exc:
                if "ENCRYPTION_KEY is required" in str(exc):
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            "Server encryption key is not configured. "
                            "Contact your workspace administrator."
                        ),
                    ) from exc
                raise
        else:
            tenant_config = await db.scalar(
                select(TenantConfig).where(TenantConfig.user_id == target_user_id)
            )

            if (
                not tenant_config
                or not tenant_config.smtp_server
                or not tenant_config.smtp_port
                or not tenant_config.smtp_username
            ):
                raise HTTPException(status_code=400, detail="SMTP is not configured")

            try:
                smtp_server = tenant_config.smtp_server
                smtp_port = tenant_config.smtp_port
                smtp_username = tenant_config.smtp_username
                smtp_password = tenant_config.smtp_password
            except Exception as exc:
                if "ENCRYPTION_KEY is required" in str(exc):
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            "Server encryption key is not configured. "
                            "Contact your workspace administrator."
                        ),
                    ) from exc
                raise

        send_result = await send_email(
            request.to,
            request.subject,
            request.body,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
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
