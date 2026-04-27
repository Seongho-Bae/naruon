from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from db.models import Email
from pydantic import BaseModel, EmailStr
import datetime
from services.email_client import send_email
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/emails")


class EmailListItem(BaseModel):
    id: int
    subject: str | None
    sender: str
    date: datetime.datetime
    snippet: str


class EmailDetailResponse(BaseModel):
    id: int
    message_id: str
    sender: str
    recipients: str | None
    subject: str | None
    date: datetime.datetime
    body: str


@router.get("", response_model=dict[str, list[EmailListItem]])
async def get_emails(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Email).order_by(Email.date.desc()).limit(limit))
    emails = result.scalars().all()

    items = []
    for email in emails:
        snippet = email.body[:100] + "..." if len(email.body) > 100 else email.body
        items.append(
            EmailListItem(
                id=email.id,
                subject=email.subject,
                sender=email.sender,
                date=email.date,
                snippet=snippet,
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
    )

class SendEmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str

@router.post("/send")
async def send_email_endpoint(request: SendEmailRequest, user_id: str | None = None): # TODO: Add authentication
    try:
        success = await send_email(request.to, request.subject, request.body)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send email")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while sending the email")
