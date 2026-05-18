import asyncio
import os

from sqlalchemy import text

from db.models import Base
from db.session import engine

DEFAULT_EMAIL_BACKFILL_USER_ID = os.environ.get("NARUON_IMPORT_USER_ID", "default")


def schema_backfill_sql():
    return [
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS thread_id varchar"),
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS user_id varchar"),
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS in_reply_to varchar"),
        text('ALTER TABLE emails ADD COLUMN IF NOT EXISTS "references" varchar'),
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS reply_to varchar"),
        text("CREATE INDEX IF NOT EXISTS ix_emails_user_id ON emails (user_id)"),
        text("UPDATE emails SET user_id = :user_id WHERE user_id IS NULL").bindparams(
            user_id=DEFAULT_EMAIL_BACKFILL_USER_ID
        ),
        text("CREATE INDEX IF NOT EXISTS ix_emails_thread_id ON emails (thread_id)"),
    ]


async def bootstrap_db() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        for statement in schema_backfill_sql():
            await conn.execute(statement)


if __name__ == "__main__":
    asyncio.run(bootstrap_db())
