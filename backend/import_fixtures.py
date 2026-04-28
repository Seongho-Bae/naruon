import asyncio
import sys
from pathlib import Path

from db.session import AsyncSessionLocal
from db.models import Email, Attachment
from services.email_parser import parse_eml
from services.embedding import generate_embeddings
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
    try:
        parsed = parse_eml(eml_file)
    except Exception as e:
        print(f"Failed to parse {eml_file}: {e}")
        return False

    existing = await session.execute(
        select(Email).where(Email.message_id == parsed["message_id"])
    )
    if existing.scalar_one_or_none():
        print(f"Email {parsed['message_id']} already exists, skipping.")
        return False

    body_text = parsed["body"] if parsed["body"].strip() else "Empty body"
    try:
        body_emb = await generate_fixture_embedding(body_text)
    except Exception as e:
        print(f"Failed to generate embedding for {eml_file}: {e}")
        return False

    thread_id = await assign_thread_id(session, parsed)

    email_obj = Email(
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
    await session.commit()
    print(f"Imported {eml_file.name} with {len(parsed.get('attachments', []))} attachments.")
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
