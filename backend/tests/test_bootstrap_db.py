import asyncpg
import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import create_async_engine

from core.config import settings
from db.models import Base
from scripts.bootstrap_db import schema_backfill_sql
from db.models import (
    CalendarWritebackSource,
    ConnectorSignalEvent,
    SenderRelationship,
    WebdavAccount,
)


def test_schema_backfill_adds_threading_columns_for_existing_tables(monkeypatch):
    monkeypatch.delenv("NARUON_IMPORT_USER_ID", raising=False)
    monkeypatch.delenv("NARUON_IMPORT_ORGANIZATION_ID", raising=False)

    statements = [str(statement).lower() for statement in schema_backfill_sql()]

    assert any(
        "alter table emails add column if not exists reply_to" in statement
        for statement in statements
    )
    assert any(
        "alter table emails add column if not exists user_id" in statement
        for statement in statements
    )
    assert any(
        "alter table emails add column if not exists organization_id" in statement
        for statement in statements
    )
    assert any(
        "alter table emails add column if not exists thread_id" in statement
        for statement in statements
    )
    assert any(
        "alter table emails add column if not exists in_reply_to" in statement
        for statement in statements
    )
    assert any(
        "alter table sender_relationships add column if not exists source_message_id"
        in statement
        for statement in statements
    )
    assert any(
        "alter table sender_relationships add column if not exists source_thread_id"
        in statement
        for statement in statements
    )
    assert any(
        "drop constraint if exists uq_sender_relationships_user_email" in statement
        for statement in statements
    )
    assert any(
        "create index if not exists ix_sender_relationships_owner_source"
        in statement
        for statement in statements
    )
    assert any(
        "create unique index if not exists uq_sender_relationships_scope_source"
        in statement
        for statement in statements
    )
    assert any(
        'alter table emails add column if not exists "references"' in statement
        for statement in statements
    )
    assert any(
        "create index if not exists ix_emails_user_id" in statement
        for statement in statements
    )
    assert any(
        "create index if not exists ix_emails_organization_id" in statement
        for statement in statements
    )
    assert any(
        "drop index if exists ix_emails_message_id" in statement
        for statement in statements
    )
    assert any(
        "create index if not exists ix_emails_message_id" in statement
        and "unique" not in statement
        for statement in statements
    )
    assert any(
        "create unique index if not exists uq_emails_owner_message_id" in statement
        for statement in statements
    )
    assert not any("update emails set user_id" in statement for statement in statements)
    assert not any(
        "update emails set organization_id" in statement for statement in statements
    )
    assert any(
        "existing emails require explicit non-default" in statement
        for statement in statements
    )
    assert any(
        "create index if not exists ix_emails_thread_id" in statement
        for statement in statements
    )
    assert any(
        "alter table llm_providers add column if not exists user_id" in statement
        for statement in statements
    )
    assert any(
        "alter table llm_providers add column if not exists organization_id"
        in statement
        for statement in statements
    )
    assert any(
        "create table if not exists calendar_writeback_sources" in statement
        for statement in statements
    )
    assert any("source_uid varchar primary key" in statement for statement in statements)
    assert any("workspace_id varchar not null" in statement for statement in statements)
    assert any("provider_name varchar not null" in statement for statement in statements)
    assert any("source_protocol varchar not null" in statement for statement in statements)
    assert any("source_host varchar not null" in statement for statement in statements)
    assert any(
        "writeback_enabled boolean not null default false" in statement
        for statement in statements
    )
    assert any("etag_value varchar" in statement for statement in statements)
    assert any(
        "create index if not exists ix_calendar_writeback_sources_scope"
        in statement
        for statement in statements
    )
    assert any(
        "alter table webdav_accounts add column if not exists source_uid"
        in statement
        for statement in statements
    )
    assert any(
        "alter table webdav_accounts add column if not exists organization_id"
        in statement
        for statement in statements
    )
    assert any(
        "alter table webdav_accounts add column if not exists writeback_enabled"
        in statement
        for statement in statements
    )
    assert any(
        "update webdav_accounts set source_uid" in statement
        and "webdav_src_" in statement
        and "md5" in statement
        for statement in statements
    )
    assert any(
        "alter table webdav_accounts alter column source_uid set not null"
        in statement
        for statement in statements
    )
    assert any(
        "create unique index if not exists uq_webdav_accounts_source_uid"
        in statement
        for statement in statements
    )
    assert any(
        "create index if not exists ix_webdav_accounts_organization_id"
        in statement
        for statement in statements
    )
    assert any(
        "create index if not exists ix_llm_providers_organization_id" in statement
        for statement in statements
    )
    assert any(
        "existing llm providers require explicit non-default" in statement
        for statement in statements
    )
    assert any(
        "create unique index if not exists uq_llm_providers_org_name" in statement
        for statement in statements
    )
    assert any(
        "drop index if exists ix_llm_providers_name" in statement
        for statement in statements
    )
    assert any(
        "alter table tenant_configs add column if not exists pop3_username"
        in statement
        for statement in statements
    )
    assert any(
        "alter table tenant_configs add column if not exists pop3_password"
        in statement
        for statement in statements
    )


def test_schema_backfill_uses_only_explicit_non_default_owner_ids(monkeypatch):
    monkeypatch.setenv("NARUON_IMPORT_USER_ID", "import-user")
    monkeypatch.setenv("NARUON_IMPORT_ORGANIZATION_ID", "import-org")

    statements = [str(statement).lower() for statement in schema_backfill_sql()]

    assert any(
        "update emails" in statement
        and "set user_id" in statement
        and "organization_id = :organization_id" in statement
        and "where user_id is null and organization_id is null" in statement
        for statement in statements
    )
    assert sum("update emails" in statement for statement in statements) == 1
    assert any(
        "update llm_providers" in statement
        and "set user_id" in statement
        and "organization_id = :organization_id" in statement
        and "where user_id is null and organization_id is null" in statement
        for statement in statements
    )
    assert sum("update llm_providers" in statement for statement in statements) == 1


def test_schema_backfill_stops_partially_owned_legacy_rows(monkeypatch):
    monkeypatch.setenv("NARUON_IMPORT_USER_ID", "import-user")
    monkeypatch.setenv("NARUON_IMPORT_ORGANIZATION_ID", "import-org")

    statements = [str(statement).lower() for statement in schema_backfill_sql()]

    assert any(
        "where user_id is null and organization_id is null" in statement
        for statement in statements
    )
    assert any(
        "existing emails require explicit non-default" in statement
        for statement in statements
    )


def test_schema_backfill_rejects_default_owner_ids(monkeypatch):
    monkeypatch.setenv("NARUON_IMPORT_USER_ID", "default")
    monkeypatch.setenv("NARUON_IMPORT_ORGANIZATION_ID", "default")

    statements = [str(statement).lower() for statement in schema_backfill_sql()]

    assert not any("update emails set user_id" in statement for statement in statements)
    assert not any(
        "update emails set organization_id" in statement for statement in statements
    )


def test_sender_relationship_model_declares_source_unique_index():
    indexes = {index.name: index for index in SenderRelationship.__table__.indexes}

    source_index = indexes["uq_sender_relationships_scope_source"]

    assert source_index.unique is True
    expression_text = " ".join(
        str(expression).lower() for expression in source_index.expressions
    )
    assert "user_id" in expression_text
    assert "coalesce" in expression_text
    assert "organization_id" in expression_text
    assert "sender_email" in expression_text
    assert "source_message_id" in expression_text
    assert "source_thread_id" in expression_text


def test_calendar_writeback_source_model_uses_two_word_names():
    assert CalendarWritebackSource.__tablename__ == "calendar_writeback_sources"
    column_names = {column.name for column in CalendarWritebackSource.__table__.columns}

    assert column_names == {
        "source_uid",
        "user_id",
        "organization_id",
        "workspace_id",
        "account_ref",
        "provider_name",
        "source_protocol",
        "source_host",
        "writeback_enabled",
        "etag_value",
        "created_at",
    }
    assert all("_" in column_name for column_name in column_names)


def test_webdav_account_model_exposes_opaque_source_uid():
    column_names = {column.name for column in WebdavAccount.__table__.columns}

    assert "source_uid" in column_names
    assert "organization_id" in column_names
    assert "writeback_enabled" in column_names
    assert WebdavAccount.__table__.c.source_uid.nullable is False
    assert WebdavAccount.__table__.c.source_uid.unique is True
    assert WebdavAccount.__table__.c.writeback_enabled.nullable is False


def test_connector_signal_event_model_uses_two_word_names():
    assert ConnectorSignalEvent.__tablename__ == "connector_signal_events"
    column_names = {column.name for column in ConnectorSignalEvent.__table__.columns}

    assert column_names == {
        "event_uid",
        "organization_id",
        "workspace_id",
        "signal_key",
        "state_code",
        "detail_text",
        "observed_at",
    }
    assert all("_" in column_name for column_name in column_names)


def test_schema_backfill_creates_connector_signal_events():
    statements = [str(statement).lower() for statement in schema_backfill_sql()]

    assert any(
        "create table if not exists connector_signal_events" in statement
        for statement in statements
    )
    assert any(
        "ix_connector_signal_events_scope_time" in statement
        for statement in statements
    )


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_connector_signal_events_real_postgres_bootstrap_smoke():
    engine = create_async_engine(settings.DATABASE_URL)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)
            for statement in schema_backfill_sql():
                await conn.execute(statement)
            result = await conn.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'connector_signal_events'
                    """
                )
            )
            column_names = {row[0] for row in result.fetchall()}
    except (
        ConnectionRefusedError,
        OSError,
        OperationalError,
        asyncpg.CannotConnectNowError,
        asyncpg.InvalidAuthorizationSpecificationError,
        asyncpg.InvalidCatalogNameError,
        asyncpg.InvalidPasswordError,
    ):
        await engine.dispose()
        pytest.skip("PostgreSQL smoke path unavailable")
    except Exception:
        await engine.dispose()
        raise
    finally:
        await engine.dispose()

    assert {
        "event_uid",
        "organization_id",
        "workspace_id",
        "signal_key",
        "state_code",
        "detail_text",
        "observed_at",
    }.issubset(column_names)
