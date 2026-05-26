import logging
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Email, TicketTask

logger = logging.getLogger(__name__)


async def extract_knowledge_from_self_sent(db: AsyncSession, email: Email):
    """
    Extracts knowledge from a self-sent email and creates a TicketTask.
    In a real implementation, this would call an LLM service.
    """
    if not email.body:
        return None

    logger.info(f"Extracting knowledge from self-sent email: {email.subject}")

    # Mock LLM extraction
    title = f"[Memo] {email.subject or 'Self-note'}"

    # Create a TicketTask
    task = TicketTask(
        user_id=email.user_id,
        organization_id=email.organization_id,
        title=title,
        status="open",
        priority="normal",
        source_type="email_auto_extract",
        related_email_id=email.id,
        related_thread_id=email.thread_id,
    )
    db.add(task)
    await db.commit()
    return task
