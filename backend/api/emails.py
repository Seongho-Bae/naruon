from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from db.models import Email, TenantConfig
from pydantic import BaseModel, EmailStr
import datetime
from services.email_client import send_email
import logging
from api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/emails")


class EmailListItem(BaseModel):
    id: int
    thread_id: str | None = None
    subject: str | None
    sender: str
    date: datetime.datetime
    snippet: str
    reply_count: int | None = None

class EmailDetailResponse(BaseModel):
    id: int
    message_id: str
    thread_id: str | None = None
    sender: str
    recipients: str | None
    subject: str | None
    date: datetime.datetime
    body: str


@router.get("", response_model=dict[str, list[EmailListItem]])
async def get_emails(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Email).order_by(Email.date.desc()).limit(limit * 3))
    emails = result.scalars().all()

    grouped = {}
    reply_counts = {}
    for email in emails:
        group_key = email.thread_id if email.thread_id else email.message_id
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
        group_key = email.thread_id if email.thread_id else email.message_id
        snippet = email.body[:100] + "..." if len(email.body) > 100 else email.body
        items.append(
            EmailListItem(
                id=email.id,
                subject=email.subject,
                sender=email.sender,
                date=email.date,
                snippet=snippet,
                thread_id=email.thread_id,
                reply_count=reply_counts[group_key],
            )
        )
    return {"emails": items}


@router.get("/{email_id}", response_model=EmailDetailResponse)
async def get_email(email_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Email).where(Email.id == email_id))
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return EmailDetailResponse(
        id=email.id,
        message_id=email.message_id,
        sender=email.sender,
        recipients=email.recipients,
        subject=email.subject,
        date=email.date,
        body=email.body,
        thread_id=email.thread_id,
    )


@router.get("/thread/{thread_id}", response_model=dict[str, list[EmailDetailResponse]])
async def get_email_thread(thread_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Email).where(Email.thread_id == thread_id).order_by(Email.date.asc())
    )
    emails = result.scalars().all()
    if not emails:
        raise HTTPException(status_code=404, detail="Thread not found")

    items = []
    for email in emails:
        items.append(
            EmailDetailResponse(
                id=email.id,
                message_id=email.message_id,
                sender=email.sender,
                recipients=email.recipients,
                subject=email.subject,
                date=email.date,
                body=email.body,
                thread_id=email.thread_id,
            )
        )
    return {"thread": items}


class SendEmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    in_reply_to: str | None = None
    references: str | None = None


@router.post("/send")
async def send_email_endpoint(
    request: SendEmailRequest, user_id: str | None = None, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)
):
    if user_id and user_id != current_user:
        raise HTTPException(status_code=403, detail="Not authorized")
    target_user_id = user_id or current_user

    try:
        tenant_config = await db.scalar(select(TenantConfig).where(TenantConfig.user_id == target_user_id))
        
        if not tenant_config or not tenant_config.smtp_server or not tenant_config.smtp_port or not tenant_config.smtp_username:
            raise HTTPException(status_code=400, detail="SMTP is not configured")
            
        smtp_server = tenant_config.smtp_server
        smtp_port = tenant_config.smtp_port
        smtp_username = tenant_config.smtp_username
        
        success = await send_email(
            request.to, 
            request.subject, 
            request.body,
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            smtp_username=smtp_username
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send email")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An internal error occurred while sending the email"
        )
