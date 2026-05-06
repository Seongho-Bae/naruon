import asyncio

from sqlalchemy import text

from core.config import settings
from db.models import Base
from db.session import engine


def schema_backfill_sql(default_email_owner_id: str = "default"):
    owner_id = default_email_owner_id.strip() or "default"
    return [
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS user_id varchar"),
        text(
            "UPDATE emails SET user_id = :default_email_owner_id "
            "WHERE user_id IS NULL OR btrim(user_id) = ''"
        ).bindparams(default_email_owner_id=owner_id),
        text("ALTER TABLE emails ALTER COLUMN user_id SET NOT NULL"),
        text("CREATE INDEX IF NOT EXISTS ix_emails_user_id ON emails (user_id)"),
        text("ALTER TABLE emails DROP CONSTRAINT IF EXISTS emails_message_id_key"),
        text("DROP INDEX IF EXISTS ix_emails_message_id"),
        text("CREATE INDEX IF NOT EXISTS ix_emails_message_id ON emails (message_id)"),
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_emails_user_id_message_id "
            "ON emails (user_id, message_id)"
        ),
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS thread_id varchar"),
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS in_reply_to varchar"),
        text('ALTER TABLE emails ADD COLUMN IF NOT EXISTS "references" varchar'),
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS reply_to varchar"),
        text("CREATE INDEX IF NOT EXISTS ix_emails_thread_id ON emails (thread_id)"),
    ]


async def bootstrap_db() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        owner_id = (settings.API_AUTH_USER_ID or "default").strip() or "default"
        for statement in schema_backfill_sql(owner_id):
            await conn.execute(statement)


if __name__ == "__main__":
    asyncio.run(bootstrap_db())
