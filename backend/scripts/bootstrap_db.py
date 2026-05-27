import asyncio
import os

from sqlalchemy import text

from db.models import Base
from db.session import engine

INVALID_EMAIL_BACKFILL_OWNER_IDS = {None, "", "default"}


def _explicit_email_backfill_owner_ids() -> tuple[str | None, str | None]:
    user_id = os.environ.get("NARUON_IMPORT_USER_ID")
    organization_id = os.environ.get("NARUON_IMPORT_ORGANIZATION_ID")
    if (
        user_id in INVALID_EMAIL_BACKFILL_OWNER_IDS
        or organization_id in INVALID_EMAIL_BACKFILL_OWNER_IDS
    ):
        return None, None
    return user_id, organization_id


def schema_backfill_sql():
    backfill_user_id, backfill_organization_id = _explicit_email_backfill_owner_ids()
    statements = [
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS thread_id varchar"),
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS user_id varchar"),
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS organization_id varchar"),
        text("ALTER TABLE llm_providers ADD COLUMN IF NOT EXISTS user_id varchar"),
        text(
            "ALTER TABLE llm_providers ADD COLUMN IF NOT EXISTS organization_id varchar"
        ),
        text(
            "CREATE TABLE IF NOT EXISTS calendar_writeback_sources ("
            "source_uid varchar PRIMARY KEY, "
            "user_id varchar NOT NULL, "
            "organization_id varchar, "
            "workspace_id varchar NOT NULL, "
            "account_ref varchar, "
            "provider_name varchar NOT NULL, "
            "source_protocol varchar NOT NULL, "
            "source_host varchar NOT NULL, "
            "writeback_enabled boolean NOT NULL DEFAULT false, "
            "etag_value varchar, "
            "created_at timestamptz DEFAULT CURRENT_TIMESTAMP"
            ")"
        ),
        text("ALTER TABLE webdav_accounts ADD COLUMN IF NOT EXISTS source_uid varchar"),
        text(
            "ALTER TABLE webdav_accounts "
            "ADD COLUMN IF NOT EXISTS organization_id varchar"
        ),
        text(
            "ALTER TABLE webdav_accounts "
            "ADD COLUMN IF NOT EXISTS writeback_enabled boolean NOT NULL DEFAULT false"
        ),
        text("ALTER TABLE tenant_configs ADD COLUMN IF NOT EXISTS pop3_username varchar"),
        text("ALTER TABLE tenant_configs ADD COLUMN IF NOT EXISTS pop3_password varchar"),
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS in_reply_to varchar"),
        text('ALTER TABLE emails ADD COLUMN IF NOT EXISTS "references" varchar'),
        text("ALTER TABLE emails ADD COLUMN IF NOT EXISTS reply_to varchar"),
        text(
            "ALTER TABLE sender_relationships "
            "ADD COLUMN IF NOT EXISTS source_message_id varchar"
        ),
        text(
            "ALTER TABLE sender_relationships "
            "ADD COLUMN IF NOT EXISTS source_thread_id varchar"
        ),
        text("CREATE INDEX IF NOT EXISTS ix_emails_user_id ON emails (user_id)"),
        text(
            "CREATE INDEX IF NOT EXISTS ix_emails_organization_id "
            "ON emails (organization_id)"
        ),
        text(
            "CREATE INDEX IF NOT EXISTS ix_sender_relationships_owner_source "
            "ON sender_relationships "
            "(user_id, organization_id, source_message_id, source_thread_id)"
        ),
        text(
            "CREATE INDEX IF NOT EXISTS ix_llm_providers_user_id "
            "ON llm_providers (user_id)"
        ),
        text(
            "CREATE INDEX IF NOT EXISTS ix_llm_providers_organization_id "
            "ON llm_providers (organization_id)"
        ),
        text(
            "CREATE INDEX IF NOT EXISTS ix_calendar_writeback_sources_scope "
            "ON calendar_writeback_sources "
            "(user_id, organization_id, source_protocol)"
        ),
        text(
            "UPDATE webdav_accounts "
            "SET source_uid = 'webdav_src_' || md5("
            "account_id::text || ':' || user_id || ':' || server_url"
            ") "
            "WHERE source_uid IS NULL OR source_uid = ''"
        ),
        text("ALTER TABLE webdav_accounts ALTER COLUMN source_uid SET NOT NULL"),
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_webdav_accounts_source_uid "
            "ON webdav_accounts (source_uid)"
        ),
        text(
            "CREATE INDEX IF NOT EXISTS ix_webdav_accounts_organization_id "
            "ON webdav_accounts (organization_id)"
        ),
        text("ALTER TABLE emails DROP CONSTRAINT IF EXISTS emails_message_id_key"),
        text(
            "ALTER TABLE sender_relationships "
            "DROP CONSTRAINT IF EXISTS uq_sender_relationships_user_email"
        ),
        text(
            "ALTER TABLE llm_providers DROP CONSTRAINT IF EXISTS llm_providers_name_key"
        ),
        text("DROP INDEX IF EXISTS ix_llm_providers_name"),
        text("DROP INDEX IF EXISTS ix_emails_message_id"),
        text("CREATE INDEX IF NOT EXISTS ix_emails_message_id ON emails (message_id)"),
    ]
    if backfill_user_id is not None and backfill_organization_id is not None:
        statements.extend(
            [
                text(
                    "UPDATE emails "
                    "SET user_id = :user_id, "
                    "organization_id = :organization_id "
                    "WHERE user_id IS NULL AND organization_id IS NULL"
                ).bindparams(
                    user_id=backfill_user_id,
                    organization_id=backfill_organization_id,
                ),
                text(
                    "UPDATE llm_providers "
                    "SET user_id = :user_id, "
                    "organization_id = :organization_id "
                    "WHERE user_id IS NULL AND organization_id IS NULL"
                ).bindparams(
                    user_id=backfill_user_id,
                    organization_id=backfill_organization_id,
                ),
            ]
        )
    statements.extend(
        [
            text(
                "DO $$ "
                "BEGIN "
                "IF EXISTS ("
                "SELECT 1 FROM emails "
                "WHERE user_id IS NULL OR organization_id IS NULL"
                ") THEN "
                "RAISE EXCEPTION "
                "'Existing emails require explicit non-default "
                "NARUON_IMPORT_USER_ID and NARUON_IMPORT_ORGANIZATION_ID "
                "before owner backfill'; "
                "END IF; "
                "END $$"
            ),
            text("ALTER TABLE emails ALTER COLUMN user_id SET NOT NULL"),
            text("ALTER TABLE emails ALTER COLUMN organization_id SET NOT NULL"),
            text(
                "DO $$ "
                "BEGIN "
                "IF EXISTS ("
                "SELECT 1 FROM llm_providers "
                "WHERE user_id IS NULL OR organization_id IS NULL"
                ") THEN "
                "RAISE EXCEPTION "
                "'Existing llm providers require explicit non-default "
                "NARUON_IMPORT_USER_ID and NARUON_IMPORT_ORGANIZATION_ID "
                "before owner backfill'; "
                "END IF; "
                "END $$"
            ),
            text("ALTER TABLE llm_providers ALTER COLUMN user_id SET NOT NULL"),
            text("ALTER TABLE llm_providers ALTER COLUMN organization_id SET NOT NULL"),
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_emails_owner_message_id "
                "ON emails (user_id, organization_id, message_id)"
            ),
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_llm_providers_org_name "
                "ON llm_providers (organization_id, name)"
            ),
            text(
                "CREATE INDEX IF NOT EXISTS ix_emails_thread_id ON emails (thread_id)"
            ),
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "uq_sender_relationships_scope_source "
                "ON sender_relationships "
                "(user_id, coalesce(organization_id, ''), sender_email, "
                "coalesce(source_message_id, ''), coalesce(source_thread_id, ''))"
            ),
        ]
    )
    return statements


async def bootstrap_db() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        for statement in schema_backfill_sql():
            await conn.execute(statement)


if __name__ == "__main__":
    asyncio.run(bootstrap_db())
