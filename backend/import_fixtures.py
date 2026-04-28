import asyncio
import sys
from pathlib import Path

from db.session import AsyncSessionLocal
from db.models import Email, Attachment
from services.email_parser import parse_eml
from services.embedding import generate_embeddings
from services.threading_service import assign_thread_id
from sqlalchemy import select


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
            try:
                parsed = parse_eml(eml_file)
            except Exception as e:
                print(f"Failed to parse {eml_file}: {e}")
                continue

            # Check if email already exists
            existing = await session.execute(
                select(Email).where(Email.message_id == parsed["message_id"])
            )
            if existing.scalar_one_or_none():
                print(f"Email {parsed['message_id']} already exists, skipping.")
                continue

            # Generate embedding for the body
            body_text = parsed["body"] if parsed["body"].strip() else "Empty body"
            try:
                body_emb = (await generate_embeddings([body_text]))[0]
            except Exception as e:
                print(f"Failed to generate embedding for {eml_file}: {e}")
                continue
                
            thread_id = await assign_thread_id(session, parsed)

            # simplified thread extraction logic
            thread_id = parsed["message_id"]
            refs_str = parsed.get("references")
            if refs_str:
                refs = str(refs_str).split()
                if refs:
                    thread_id = refs[0]
            elif parsed.get("in_reply_to"):
                thread_id = str(parsed.get("in_reply_to"))

            email_obj = Email(
                message_id=parsed["message_id"],
                thread_id=parsed["thread_id"],
                sender=parsed["sender"],
                recipients=parsed["recipients"],
                subject=parsed["subject"],
                in_reply_to=parsed.get("in_reply_to"),
                references=parsed.get("references"),
                thread_id=thread_id,
                date=parsed["date"],
                body=parsed["body"],
                embedding=body_emb,
                thread_id=thread_id,
            )

            # Generate embeddings for attachments
            for att in parsed.get("attachments", []):
                att_text = (
                    att["content"] if att["content"].strip() else "Empty attachment"
                )
                try:
                    att_emb = (await generate_embeddings([att_text]))[0]
                    email_obj.attachments.append(
                        Attachment(
                            filename=att["filename"],
                            content=att["content"],
                            embedding=att_emb,
                        )
                    )
                except Exception as e:
                    print(
                        f"Failed to generate embedding for attachment {att['filename']}: {e}"
                    )

            session.add(email_obj)
            await session.commit()
            print(
                f"Imported {eml_file.name} with {len(parsed.get('attachments', []))} attachments."
            )


if __name__ == "__main__":
    asyncio.run(main())
