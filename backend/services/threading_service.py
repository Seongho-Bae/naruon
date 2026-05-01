import uuid
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select
from db.models import Email
from services.email_parser import EmailData


def normalize_message_id(value: str | None) -> str | None:
    """Return the canonical persisted form for a Message-ID-like header."""
    if value is None:
        return None

    normalized = str(value).strip().strip("<>").strip()
    return normalized or None


def extract_reference_ids(value: str | None) -> list[str]:
    """Extract canonical message IDs from a References header in header order."""
    if not value:
        return []

    refs = re.findall(r"<([^>]+)>", str(value))
    if not refs:
        refs = str(value).split()

    normalized_refs: list[str] = []
    for ref in refs:
        normalized = normalize_message_id(ref)
        if normalized and normalized not in normalized_refs:
            normalized_refs.append(normalized)
    return normalized_refs


async def _find_existing_thread_id(
    session: AsyncSession, message_id: str, user_id: str
) -> str | None:
    bracketed = f"<{message_id}>"
    result = await session.execute(
        select(Email.thread_id).where(
            Email.user_id == user_id,
            or_(Email.message_id == message_id, Email.message_id == bracketed),
        )
    )
    return result.scalar_one_or_none()

async def assign_thread_id(
    session: AsyncSession, email_data: EmailData, user_id: str = "default"
) -> str:
    """
    Determine the thread_id for a new email based on in_reply_to and references.
    If no existing match is found, generate a new thread_id.
    """
    in_reply_to = normalize_message_id(email_data.get("in_reply_to"))
    references = extract_reference_ids(email_data.get("references"))

    existing_candidates = []
    if in_reply_to:
        existing_candidates.append(in_reply_to)
    existing_candidates.extend(ref for ref in references if ref not in existing_candidates)

    for candidate in existing_candidates:
        thread_id = await _find_existing_thread_id(session, candidate, user_id)
        if thread_id:
            return normalize_message_id(thread_id) or thread_id

    # If the parent/root has not been imported yet, use the oldest known ancestor
    # as the deterministic thread root so later imports converge on one thread.
    if references:
        return references[0]

    if in_reply_to:
        return in_reply_to

    msg_id = normalize_message_id(email_data.get("message_id"))
    if msg_id:
        return msg_id

    return uuid.uuid4().hex
