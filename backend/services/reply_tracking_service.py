import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Email, TenantConfig
from services.email_service import detect_reply_tracking
import datetime

logger = logging.getLogger(__name__)

async def check_missing_replies(session: AsyncSession, user_id: str, organization_id: str | None) -> list[Email]:
    """
    Checks for sent emails that expect a reply but haven't received one.
    Returns a list of such emails.
    """
    # Find user's own email address
    tenant_config = await session.execute(
        select(TenantConfig).where(TenantConfig.user_id == user_id)
    )
    config = tenant_config.scalar_one_or_none()
    
    if not config or not config.smtp_username:
        logger.info(f"Cannot track replies for {user_id} - no SMTP username configured")
        return []
        
    my_email = config.smtp_username
    
    # We should ideally fetch emails sent by me in the last X days
    # that have detect_reply_tracking == True, and no other emails in the same thread
    # where sender != my_email and date > sent_email.date
    
    # For simplicity in this demo logic, we'll fetch recently sent emails
    # and check them.
    recent_limit = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    
    stmt = select(Email).where(
        Email.user_id == user_id,
        Email.sender == my_email,
        Email.date > recent_limit
    )
    result = await session.execute(stmt)
    sent_emails = result.scalars().all()
    
    flagged = []
    for email in sent_emails:
        if detect_reply_tracking({"body": email.body}):
            # Check if there are replies
            reply_stmt = select(Email).where(
                Email.thread_id == email.thread_id,
                Email.sender != my_email,
                Email.date > email.date
            )
            reply_res = await session.execute(reply_stmt)
            if not reply_res.scalars().first():
                flagged.append(email)
                
    logger.info(f"Found {len(flagged)} emails awaiting replies for user {user_id}")
    return flagged
