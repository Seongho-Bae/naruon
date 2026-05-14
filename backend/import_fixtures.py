import asyncio
import sys
from pathlib import Path

from db.session import AsyncSessionLocal
from db.models import Email, Attachment, MailboxAccount
from core.config import settings
from services.email_parser import parse_eml
from services.embedding import generate_embeddings
from services.mailbox_routing import resolve_mailbox_account_id_for_email
from services.threading_service import assign_thread_id
import os
from sqlalchemy import select

EMBEDDING_DIMENSION = 1536


async def generate_fixture_embedding(text: str) -> list[float]:
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    if not openai_api_key:
        return [0.0] * EMBEDDING_DIMENSION

    return (await generate_embeddings([text], openai_api_key=openai_api_key))[0]


async def import_eml_file(session, eml_file: Path) -> bool:
    owner_user_id = settings.LEGACY_EMAIL_OWNER_USER_ID
    if not owner_user_id:
        print("LEGACY_EMAIL_OWNER_USER_ID is required for importing email fixtures.")
        return False

    try:
        parsed = parse_eml(eml_file)
    except Exception as e:
        print(f"Failed to parse {eml_file}: {e}")
        return False

    body_text = parsed["body"] if parsed["body"].strip() else "Empty body"
    try:
        body_emb = await generate_fixture_embedding(body_text)
    except Exception as e:
        print(f"Failed to generate embedding for {eml_file}: {e}")
        return False

    thread_id = await assign_thread_id(session, parsed)
    mailbox_accounts_result = await session.execute(
        select(MailboxAccount).where(
            MailboxAccount.user_id == owner_user_id, MailboxAccount.is_active.is_(True)
        )
    )
    mailbox_account_id = resolve_mailbox_account_id_for_email(
        mailbox_accounts_result.scalars().all(),
        sender=parsed["sender"],
        reply_to=parsed.get("reply_to"),
        recipients=parsed["recipients"],
    )
    existing = await session.execute(
        select(Email).where(
            Email.user_id == owner_user_id,
            Email.mailbox_account_id == mailbox_account_id,
            Email.message_id == parsed["message_id"],
        )
    )
    existing_email = existing.scalar_one_or_none()
    if existing_email:
        print(f"Email {parsed['message_id']} already exists, skipping.")
        return False

    if mailbox_account_id is not None:
        legacy_existing_result = await session.execute(
            select(Email).where(
                Email.user_id == owner_user_id,
                Email.mailbox_account_id.is_(None),
                Email.message_id == parsed["message_id"],
            )
        )
        legacy_existing = legacy_existing_result.scalar_one_or_none()
        if legacy_existing:
            legacy_existing.mailbox_account_id = mailbox_account_id
            legacy_existing.sender = parsed["sender"]
            legacy_existing.reply_to = parsed.get("reply_to")
            legacy_existing.recipients = parsed["recipients"]
            legacy_existing.subject = parsed["subject"]
            legacy_existing.in_reply_to = parsed.get("in_reply_to")
            legacy_existing.references = parsed.get("references")
            legacy_existing.date = parsed["date"]
            legacy_existing.body = parsed["body"]
            legacy_existing.embedding = body_emb
            legacy_existing.thread_id = thread_id
            try:
                await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"Failed to commit {eml_file}: {e}")
                return False
            print(
                f"Upgraded legacy email {parsed['message_id']} to mailbox account {mailbox_account_id}."
            )
            return True

    email_obj = Email(
        user_id=owner_user_id,
        mailbox_account_id=mailbox_account_id,
        message_id=parsed["message_id"],
        sender=parsed["sender"],
        reply_to=parsed.get("reply_to"),
        recipients=parsed["recipients"],
        subject=parsed["subject"],
        in_reply_to=parsed.get("in_reply_to"),
        references=parsed.get("references"),
        date=parsed["date"],
        body=parsed["body"],
        embedding=body_emb,
        thread_id=thread_id,
    )

    for att in parsed.get("attachments", []):
        att_text = att["content"] if att["content"].strip() else "Empty attachment"
        try:
            att_emb = await generate_fixture_embedding(att_text)
            email_obj.attachments.append(
                Attachment(
                    filename=att["filename"],
                    content=att["content"],
                    embedding=att_emb,
                )
            )
        except Exception as e:
            print(f"Failed to generate embedding for attachment {att['filename']}: {e}")

    session.add(email_obj)
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        print(f"Failed to commit {eml_file}: {e}")
        return False
    print(
        f"Imported {eml_file.name} with {len(parsed.get('attachments', []))} attachments."
    )
    return True


async def main():
    fixtures_dir = Path(__file__).parent / "tests" / "fixtures"
    if not fixtures_dir.exists():
        print(f"Fixtures directory {fixtures_dir} does not exist.")
        sys.exit(1)

    eml_files = list(fixtures_dir.glob("*.eml"))
    if not eml_files:
        print(f"No .eml files found in {fixtures_dir}.")
        return

    async with AsyncSessionLocal() as session:
        for eml_file in eml_files:
            await import_eml_file(session, eml_file)


if __name__ == "__main__":
    asyncio.run(main())
