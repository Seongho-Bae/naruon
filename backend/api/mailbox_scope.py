from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import MailboxAccount


async def require_owned_mailbox_account(
    db: AsyncSession, current_user: str, mailbox_account_id: int | None
) -> None:
    if mailbox_account_id is None:
        return

    account_id = await db.scalar(
        select(MailboxAccount.id).where(
            MailboxAccount.id == mailbox_account_id,
            MailboxAccount.user_id == current_user,
        )
    )
    if account_id is None:
        raise HTTPException(status_code=404, detail="Mailbox account not found")
