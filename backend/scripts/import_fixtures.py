import asyncio
import tempfile
import logging
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
import sys
import os

# Add backend directory to sys.path so we can import modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.archive import extract_backup_async
from services.email_parser import parse_eml
from services.embedding import chunk_text, generate_embeddings
from services.mailbox_routing import resolve_mailbox_account_id_for_email
from services.threading_service import assign_thread_id
from db.session import AsyncSessionLocal
from db.models import Email, MailboxAccount, TenantConfig
from sqlalchemy import select
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_zip_file(zip_path: str | Path, session: AsyncSession):
    owner_user_id = settings.LEGACY_EMAIL_OWNER_USER_ID
    if not owner_user_id:
        logger.error("LEGACY_EMAIL_OWNER_USER_ID is required for ZIP fixture imports.")
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Extracting {zip_path}...")
        extracted_files = await extract_backup_async(zip_path, temp_dir)

        for file_path in extracted_files:
            if not str(file_path).endswith(".eml"):
                continue

            try:
                email_data = parse_eml(file_path)
            except Exception as e:
                logger.error(f"Failed to parse {file_path}: {e}")
                continue

            chunks = chunk_text(email_data["body"])
            embedding = None
            if chunks:
                try:
                    tenant_config = await session.scalar(
                        select(TenantConfig).where(TenantConfig.user_id == "default")
                    )
                    api_key = (
                        tenant_config.openai_api_key
                        if tenant_config and tenant_config.openai_api_key
                        else os.getenv("OPENAI_API_KEY")
                    ) or ""
                    embeddings = await generate_embeddings([chunks[0]], api_key)
                    if embeddings:
                        embedding = embeddings[0]
                except Exception as e:
                    logger.error(
                        f"Failed to generate embedding for {email_data['message_id']}: {e}"
                    )

            # Upsert into database
            thread_id = await assign_thread_id(session, email_data)
            mailbox_accounts_result = await session.execute(
                select(MailboxAccount).where(
                    MailboxAccount.user_id == owner_user_id,
                    MailboxAccount.is_active.is_(True),
                )
            )
            mailbox_account_id = resolve_mailbox_account_id_for_email(
                mailbox_accounts_result.scalars().all(),
                sender=email_data["sender"],
                reply_to=email_data.get("reply_to"),
                recipients=email_data["recipients"],
            )

            if mailbox_account_id is not None:
                legacy_existing_result = await session.execute(
                    select(Email).where(
                        Email.user_id == owner_user_id,
                        Email.mailbox_account_id.is_(None),
                        Email.message_id == email_data["message_id"],
                    )
                )
                legacy_existing = legacy_existing_result.scalar_one_or_none()
                if legacy_existing:
                    legacy_existing.mailbox_account_id = mailbox_account_id
                    legacy_existing.sender = email_data["sender"]
                    legacy_existing.reply_to = email_data.get("reply_to")
                    legacy_existing.recipients = email_data["recipients"]
                    legacy_existing.subject = email_data["subject"]
                    legacy_existing.in_reply_to = email_data.get("in_reply_to")
                    legacy_existing.references = email_data.get("references")
                    legacy_existing.thread_id = thread_id
                    legacy_existing.date = email_data["date"]
                    legacy_existing.body = email_data["body"]
                    legacy_existing.embedding = embedding
                    continue

            stmt = insert(Email).values(
                user_id=owner_user_id,
                mailbox_account_id=mailbox_account_id,
                message_id=email_data["message_id"],
                sender=email_data["sender"],
                reply_to=email_data.get("reply_to"),
                recipients=email_data["recipients"],
                subject=email_data["subject"],
                in_reply_to=email_data.get("in_reply_to"),
                references=email_data.get("references"),
                thread_id=thread_id,
                date=email_data["date"],
                body=email_data["body"],
                embedding=embedding,
            )
            update_values = dict(
                user_id=stmt.excluded.user_id,
                mailbox_account_id=stmt.excluded.mailbox_account_id,
                sender=stmt.excluded.sender,
                reply_to=stmt.excluded.reply_to,
                recipients=stmt.excluded.recipients,
                subject=stmt.excluded.subject,
                in_reply_to=stmt.excluded.in_reply_to,
                references=stmt.excluded.references,
                thread_id=stmt.excluded.thread_id,
                date=stmt.excluded.date,
                body=stmt.excluded.body,
                embedding=stmt.excluded.embedding,
            )
            if mailbox_account_id is None:
                stmt = stmt.on_conflict_do_update(
                    index_elements=["user_id", "message_id"],
                    index_where=Email.mailbox_account_id.is_(None),
                    set_=update_values,
                )
            else:
                stmt = stmt.on_conflict_do_update(
                    index_elements=["user_id", "mailbox_account_id", "message_id"],
                    set_=update_values,
                )
            await session.execute(stmt)

        await session.commit()
        logger.info(f"Finished processing {zip_path}")


async def main():
    root_dir = Path(__file__).resolve().parent.parent.parent
    fixtures_dir = root_dir / "secret_fixtures"

    if not fixtures_dir.exists():
        logger.error(f"Fixtures directory {fixtures_dir} does not exist.")
        return

    async with AsyncSessionLocal() as session:
        for zip_file in fixtures_dir.glob("*.zip"):
            await process_zip_file(zip_file, session)


if __name__ == "__main__":
    asyncio.run(main())
