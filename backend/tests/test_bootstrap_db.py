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
    ProjectFolder,
    RevokedSessionToken,
    SecurityAuditEvent,
    SenderRelationship,
    TenantConfig,
    TicketTask,
    WebdavAccount,
)


def _get_schema_statements(monkeypatch):
    monkeypatch.delenv("NARUON_IMPORT_USER_ID", raising=False)
    monkeypatch.delenv("NARUON_IMPORT_ORGANIZATION_ID", raising=False)
    return [str(statement).lower() for statement in schema_backfill_sql()]


def _execute_schema_backfill(sync_conn):
    for statement in schema_backfill_sql():
        sync_conn.execute(statement)


def test_schema_backfill_adds_email_columns(monkeypatch):
    statements = _get_schema_statements(monkeypatch)
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
        'alter table emails add column if not exists "references"' in statement
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


def test_schema_backfill_adds_sender_relationship_columns_and_indexes(monkeypatch):
    statements = _get_schema_statements(monkeypatch)
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
        "create index if not exists ix_sender_relationships_owner_source" in statement
        for statement in statements
    )
    assert any(
        "create unique index if not exists uq_sender_relationships_scope_source"
        in statement
        for statement in statements
    )


def test_schema_backfill_adds_email_indexes(monkeypatch):
    statements = _get_schema_statements(monkeypatch)
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
    assert any(
        "create index if not exists ix_emails_thread_id" in statement
        for statement in statements
    )
    assert any(
        "create index if not exists ix_emails_date" in statement
        for statement in statements
    )


def test_schema_backfill_adds_llm_provider_columns_and_indexes(monkeypatch):
    statements = _get_schema_statements(monkeypatch)
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
        "alter table llm_providers add column if not exists model_identifier"
        in statement
        for statement in statements
    )
    assert any(
        "alter table llm_providers add column if not exists embedding_model"
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


def test_schema_backfill_creates_calendar_writeback_sources_table(monkeypatch):
    statements = _get_schema_statements(monkeypatch)
    assert any(
        "create table if not exists calendar_writeback_sources" in statement
        for statement in statements
    )
    assert any(
        "source_uid varchar primary key" in statement for statement in statements
    )
    assert any("workspace_id varchar not null" in statement for statement in statements)
    assert any(
        "provider_name varchar not null" in statement for statement in statements
    )
    assert any(
        "source_protocol varchar not null" in statement for statement in statements
    )
    assert any("source_host varchar not null" in statement for statement in statements)
    assert any(
        "writeback_enabled boolean not null default false" in statement
        for statement in statements
    )
    assert any("etag_value varchar" in statement for statement in statements)
    assert any(
        "create index if not exists ix_calendar_writeback_sources_scope" in statement
        for statement in statements
    )


def test_schema_backfill_creates_security_audit_events_table(monkeypatch):
    statements = _get_schema_statements(monkeypatch)
    assert any(
        "create table if not exists security_audit_events" in statement
        for statement in statements
    )
    assert any(
        "actor_user_id varchar not null" in statement for statement in statements
    )
    assert any("event_action varchar not null" in statement for statement in statements)
    assert any("resource_uid varchar" in statement for statement in statements)


def test_schema_backfill_adds_webdav_account_columns_and_indexes(monkeypatch):
    statements = _get_schema_statements(monkeypatch)
    assert any(
        "alter table webdav_accounts add column if not exists source_uid" in statement
        for statement in statements
    )
    assert any(
        "alter table webdav_accounts add column if not exists organization_id"
        in statement
        for statement in statements
    )
    assert any(
        "alter table webdav_accounts add column if not exists workspace_id" in statement
        for statement in statements
    )
    assert any(
        "alter table webdav_accounts add column if not exists writeback_enabled"
        in statement
        for statement in statements
    )
    assert any(
        "alter table webdav_accounts add column if not exists etag_value" in statement
        for statement in statements
    )
    assert any(
        "update webdav_accounts set source_uid" in statement
        and "webdav_src_" in statement
        and "md5" in statement
        and "random()::text" in statement
        and "clock_timestamp()::text" in statement
        for statement in statements
    )
    assert not any("account_id::text" in statement for statement in statements)
    assert any(
        "update webdav_accounts set workspace_id" in statement
        and "'workspace-' || organization_id" in statement
        for statement in statements
    )
    assert any(
        "alter table webdav_accounts alter column source_uid set not null" in statement
        for statement in statements
    )
    assert any(
        "alter table webdav_accounts alter column workspace_id set not null"
        in statement
        for statement in statements
    )
    assert any(
        "create unique index if not exists uq_webdav_accounts_source_uid" in statement
        for statement in statements
    )
    assert any(
        "create index if not exists ix_webdav_accounts_organization_id" in statement
        for statement in statements
    )
    assert any(
        "create index if not exists ix_webdav_accounts_workspace_scope" in statement
        and "user_id, organization_id, workspace_id" in statement
        for statement in statements
    )


def test_schema_backfill_adds_project_folder_columns_and_indexes(monkeypatch):
    statements = _get_schema_statements(monkeypatch)
    assert any(
        "alter table project_folders add column if not exists folder_uid" in statement
        for statement in statements
    )
    assert any(
        "alter table project_folders add column if not exists organization_id"
        in statement
        for statement in statements
    )
    assert any(
        "update project_folders set folder_uid" in statement
        and "webdav_folder_" in statement
        and "md5" in statement
        and "random()::text" in statement
        and "clock_timestamp()::text" in statement
        for statement in statements
    )
    assert any(
        "alter table project_folders alter column folder_uid set not null" in statement
        for statement in statements
    )
    assert any(
        "create unique index if not exists uq_project_folders_folder_uid" in statement
        for statement in statements
    )
    assert any(
        "create index if not exists ix_project_folders_owner_scope" in statement
        and "user_id, organization_id" in statement
        for statement in statements
    )


def test_schema_backfill_adds_tenant_config_columns_and_indexes(monkeypatch):
    statements = _get_schema_statements(monkeypatch)
    assert any(
        "alter table tenant_configs add column if not exists pop3_username" in statement
        for statement in statements
    )
    assert any(
        "alter table tenant_configs add column if not exists pop3_password" in statement
        for statement in statements
    )
    assert any(
        "alter table tenant_configs add column if not exists organization_id"
        in statement
        for statement in statements
    )
    assert any(
        "alter table tenant_configs drop constraint if exists tenant_configs_user_id_key"
        in statement
        for statement in statements
    )
    assert any(
        "drop index if exists ix_tenant_configs_user_id" in statement
        for statement in statements
    )
    assert any(
        "create index if not exists ix_tenant_configs_owner_scope" in statement
        and "user_id, organization_id" in statement
        for statement in statements
    )
    assert any(
        "create unique index if not exists uq_tenant_configs_owner_scope" in statement
        and "coalesce(organization_id, '')" in statement
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
    assert any(
        "update tenant_configs" in statement
        and "set organization_id = :organization_id" in statement
        and "where user_id = :user_id and organization_id is null" in statement
        for statement in statements
    )
    assert sum("update tenant_configs" in statement for statement in statements) == 1


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


def test_tenant_config_model_declares_owner_scope_unique_index():
    indexes = {index.name: index for index in TenantConfig.__table__.indexes}

    source_index = indexes["uq_tenant_configs_owner_scope"]

    assert source_index.unique is True
    expression_text = " ".join(
        str(expression).lower() for expression in source_index.expressions
    )
    assert "user_id" in expression_text
    assert "coalesce" in expression_text
    assert "organization_id" in expression_text


def test_ticket_task_reply_sla_unique_index_is_bootstrapped():
    statements = [str(statement).lower() for statement in schema_backfill_sql()]
    indexes = {index.name: index for index in TicketTask.__table__.indexes}
    dedupe_statement_index = next(
        index
        for index, statement in enumerate(statements)
        if "with ranked_tasks as" in statement
        and "delete from ticket_tasks" in statement
        and "source_type = 'reply_sla'" in statement
        and "task_id desc" in statement
        and "row_rank > 1" in statement
    )
    unique_index_statement_index = next(
        index
        for index, statement in enumerate(statements)
        if "create unique index if not exists uq_ticket_tasks_reply_sla_email"
        in statement
    )

    assert "uq_ticket_tasks_reply_sla_email" in indexes
    assert indexes["uq_ticket_tasks_reply_sla_email"].unique is True
    assert dedupe_statement_index < unique_index_statement_index
    assert any(
        "create unique index if not exists uq_ticket_tasks_reply_sla_email" in statement
        and "where source_type = 'reply_sla'" in statement
        for statement in statements
    )


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


def test_project_folder_model_exposes_opaque_folder_uid():
    column_names = {column.name for column in ProjectFolder.__table__.columns}

    assert "folder_uid" in column_names
    assert "organization_id" in column_names
    assert ProjectFolder.__table__.c.folder_uid.nullable is False
    assert ProjectFolder.__table__.c.folder_uid.unique is True


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


def test_security_audit_event_model_uses_two_word_names():
    assert SecurityAuditEvent.__tablename__ == "security_audit_events"
    column_names = {column.name for column in SecurityAuditEvent.__table__.columns}
    index_names = {index.name for index in SecurityAuditEvent.__table__.indexes}

    assert column_names == {
        "event_uid",
        "actor_user_id",
        "actor_role",
        "organization_id",
        "workspace_id",
        "event_action",
        "resource_type",
        "resource_uid",
        "evidence_source",
        "detail_text",
        "observed_at",
    }
    assert all("_" in column_name for column_name in column_names)
    assert "ix_security_audit_events_scope_time" in index_names
    assert "ix_security_audit_events_actor_scope" in index_names


def test_schema_backfill_creates_connector_signal_events():
    statements = [str(statement).lower() for statement in schema_backfill_sql()]

    assert any(
        "create table if not exists connector_signal_events" in statement
        for statement in statements
    )
    assert any(
        "ix_connector_signal_events_scope_time" in statement for statement in statements
    )
    assert any(
        "ix_security_audit_events_scope_time" in statement for statement in statements
    )
    assert any(
        "ix_security_audit_events_actor_scope" in statement for statement in statements
    )


def test_schema_backfill_creates_revoked_session_tokens_table():
    statements = [str(statement).lower() for statement in schema_backfill_sql()]

    assert any(
        "create table if not exists revoked_session_tokens" in statement
        for statement in statements
    )
    assert any("token_digest varchar primary key" in statement for statement in statements)
    assert any("revocation_reason varchar not null" in statement for statement in statements)
    assert any("expires_at timestamptz not null" in statement for statement in statements)
    assert any(
        "ix_revoked_session_tokens_scope_time" in statement
        for statement in statements
    )

    column_names = {column.name for column in RevokedSessionToken.__table__.columns}
    assert column_names == {
        "token_digest",
        "user_id",
        "organization_id",
        "workspace_id",
        "revocation_reason",
        "revoked_at",
        "expires_at",
    }
    assert all("_" in column_name for column_name in column_names)


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_connector_signal_events_real_postgres_bootstrap_smoke():
    engine = create_async_engine(settings.DATABASE_URL)
    duplicate_count = 0
    kept_title = ""
    smoke_user_id = "reply-sla-bootstrap-smoke-user"
    smoke_organization_id = "reply-sla-bootstrap-smoke-org"
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(
                text("DROP INDEX IF EXISTS uq_ticket_tasks_reply_sla_email")
            )
            await conn.execute(
                text("DELETE FROM ticket_tasks WHERE user_id = :user_id"),
                {"user_id": smoke_user_id},
            )
            await conn.execute(
                text("DELETE FROM emails WHERE user_id = :user_id"),
                {"user_id": smoke_user_id},
            )
            email_result = await conn.execute(
                text("""
                    INSERT INTO emails (
                        user_id, organization_id, message_id, sender, recipients,
                        subject, "date", body
                    )
                    VALUES (
                        :user_id, :organization_id, :message_id, :sender,
                        :recipients, :subject, now(), :body
                    )
                    RETURNING id
                    """),
                {
                    "user_id": smoke_user_id,
                    "organization_id": smoke_organization_id,
                    "message_id": "<reply-sla-bootstrap-smoke@example.com>",
                    "sender": "smoke@example.com",
                    "recipients": "owner@example.com",
                    "subject": "Bootstrap duplicate reply SLA",
                    "body": "bootstrap duplicate smoke",
                },
            )
            email_id = email_result.scalar_one()
            await conn.execute(
                text("""
                    INSERT INTO ticket_tasks (
                        task_uid, user_id, organization_id, task_title,
                        status_code, priority_code, source_type, email_id,
                        thread_id, created_at, updated_at
                    )
                    VALUES
                    (
                        'reply_sla_bootstrap_old', :user_id, :organization_id,
                        'old duplicate', 'blocked', 'urgent', 'reply_sla',
                        :email_id, 'thread-bootstrap-smoke',
                        now() - interval '2 hours', now() - interval '2 hours'
                    ),
                    (
                        'reply_sla_bootstrap_new', :user_id, :organization_id,
                        'new duplicate', 'blocked', 'urgent', 'reply_sla',
                        :email_id, 'thread-bootstrap-smoke',
                        now() - interval '1 hour', now() - interval '1 hour'
                    )
                    """),
                {
                    "user_id": smoke_user_id,
                    "organization_id": smoke_organization_id,
                    "email_id": email_id,
                },
            )
            await conn.run_sync(_execute_schema_backfill)
            result = await conn.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'connector_signal_events'
                    """))
            column_names = {row[0] for row in result.fetchall()}
            duplicate_result = await conn.execute(
                text("""
                    SELECT
                        count(*) OVER () AS task_count,
                        task_title
                    FROM ticket_tasks
                    WHERE user_id = :user_id
                        AND organization_id = :organization_id
                        AND source_type = 'reply_sla'
                        AND email_id = :email_id
                    ORDER BY updated_at DESC, task_id DESC
                    LIMIT 1
                    """),
                {
                    "user_id": smoke_user_id,
                    "organization_id": smoke_organization_id,
                    "email_id": email_id,
                },
            )
            duplicate_count, kept_title = duplicate_result.one()
            await conn.execute(
                text("DELETE FROM ticket_tasks WHERE user_id = :user_id"),
                {"user_id": smoke_user_id},
            )
            await conn.execute(
                text("DELETE FROM emails WHERE user_id = :user_id"),
                {"user_id": smoke_user_id},
            )
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
    assert duplicate_count == 1
    assert kept_title == "new duplicate"
