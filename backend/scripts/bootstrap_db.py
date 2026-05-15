import asyncio

from sqlalchemy import text

from core.config import settings
from db.models import Base
from db.session import engine


def schema_backfill_sql(
    legacy_llm_provider_organization_id: str | None = None,
    legacy_email_owner_user_id: str | None = None,
):
    statements = [
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS user_id varchar"),
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS mailbox_account_id integer"),
        text("ALTER TABLE emails DROP CONSTRAINT IF EXISTS emails_message_id_key"),
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS thread_id varchar"),
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS in_reply_to varchar"),
        text('ALTER TABLE emails ADD COLUMN IF NOT EXISTS "references" varchar'),
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS reply_to varchar"),
        text("CREATE INDEX IF NOT EXISTS ix_emails_user_id ON emails (user_id)"),
        text(
            "CREATE INDEX IF NOT EXISTS ix_emails_mailbox_account_id ON emails (mailbox_account_id)"
        ),
        text("DROP INDEX IF EXISTS ix_emails_message_id"),
        text("CREATE INDEX IF NOT EXISTS ix_emails_message_id ON emails (message_id)"),
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_emails_owner_message_when_mailbox_null ON emails (user_id, message_id) WHERE mailbox_account_id IS NULL"
        ),
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_emails_owner_mailbox_message ON emails (user_id, mailbox_account_id, message_id) WHERE mailbox_account_id IS NOT NULL"
        ),
        text("CREATE INDEX IF NOT EXISTS ix_emails_thread_id ON emails (thread_id)"),
        text(
            "ALTER TABLE llm_providers ADD COLUMN IF NOT EXISTS organization_id varchar"
        ),
        text(
            "ALTER TABLE llm_providers DROP CONSTRAINT IF EXISTS llm_providers_name_key"
        ),
        text(
            "CREATE INDEX IF NOT EXISTS ix_llm_providers_organization_id ON llm_providers (organization_id)"
        ),
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_llm_providers_organization_name ON llm_providers (organization_id, name)"
        ),
        text(
            "ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS organization_id varchar"
        ),
        text(
            "CREATE INDEX IF NOT EXISTS ix_prompt_templates_organization_id ON prompt_templates (organization_id)"
        ),
        text(
            "ALTER TABLE execution_items ADD COLUMN IF NOT EXISTS source_mailbox_account_id integer"
        ),
        text(
            "ALTER TABLE execution_items ADD COLUMN IF NOT EXISTS source_snippet text"
        ),
        text(
            "CREATE INDEX IF NOT EXISTS ix_execution_items_source_mailbox_account_id ON execution_items (source_mailbox_account_id)"
        ),
        text(
            "ALTER TABLE mailbox_accounts ADD COLUMN IF NOT EXISTS pop3_server varchar"
        ),
        text("ALTER TABLE mailbox_accounts ADD COLUMN IF NOT EXISTS pop3_port integer"),
        text(
            "ALTER TABLE mailbox_accounts ADD COLUMN IF NOT EXISTS pop3_username varchar"
        ),
        text(
            "ALTER TABLE mailbox_accounts ADD COLUMN IF NOT EXISTS pop3_password text"
        ),
    ]
    if legacy_llm_provider_organization_id:
        statements.append(
            text(
                "UPDATE llm_providers SET organization_id = :organization_id WHERE organization_id IS NULL"
            ).bindparams(organization_id=legacy_llm_provider_organization_id)
        )
    if legacy_email_owner_user_id:
        statements.append(
            text(
                "UPDATE emails SET user_id = :user_id WHERE user_id IS NULL"
            ).bindparams(user_id=legacy_email_owner_user_id)
        )
    else:
        statements.append(text("""
                DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM emails WHERE user_id IS NULL) THEN
                        RAISE EXCEPTION 'LEGACY_EMAIL_OWNER_USER_ID must be set before enabling owner-scoped email reads with legacy ownerless email rows';
                    END IF;
                END $$;
                """))
    return statements


async def bootstrap_db() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        for statement in schema_backfill_sql(
            settings.LEGACY_LLM_PROVIDER_ORGANIZATION_ID,
            settings.LEGACY_EMAIL_OWNER_USER_ID,
        ):
            await conn.execute(statement)


if __name__ == "__main__":
    asyncio.run(bootstrap_db())
