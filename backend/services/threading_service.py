import uuid
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Email
from services.email_parser import EmailData

async def assign_thread_id(session: AsyncSession, email_data: EmailData) -> str:
    """
    Determine the thread_id for a new email based on in_reply_to and references.
    If no existing match is found, generate a new thread_id.
    """
    in_reply_to = email_data.get("in_reply_to")
    references_str = email_data.get("references")
    
    # 1. Try to find the parent email using in_reply_to
    if in_reply_to:
        # Some headers have brackets like <msg-id>
        in_reply_to_clean = in_reply_to.strip("<>")
        query = select(Email.thread_id).where(Email.message_id == in_reply_to_clean)
        result = await session.execute(query)
        thread_id = result.scalar_one_or_none()
        if thread_id:
            return thread_id
            
        # Also try matching exact string if it didn't have brackets or we stripped them but the DB has brackets
        query = select(Email.thread_id).where(Email.message_id == in_reply_to)
        result = await session.execute(query)
        thread_id = result.scalar_one_or_none()
        if thread_id:
            return thread_id

    # 2. Try to find any email from the references
    if references_str:
        # Extract message IDs from references string (usually space-separated, sometimes with <>)
        refs = re.findall(r'<([^>]+)>', references_str)
        if not refs:
            refs = references_str.split()
            
        for ref in refs:
            ref_clean = ref.strip("<>")
            # Try both stripped and unstripped
            query = select(Email.thread_id).where((Email.message_id == ref_clean) | (Email.message_id == ref))
            result = await session.execute(query)
            thread_id = result.scalar_one_or_none()
            if thread_id:
                return thread_id

    # 3. No match found, generate a new thread_id
    # We can use the message_id if available, otherwise a UUID
    msg_id = email_data.get("message_id")
    if msg_id:
        return msg_id.strip("<>")
    
    return uuid.uuid4().hex
