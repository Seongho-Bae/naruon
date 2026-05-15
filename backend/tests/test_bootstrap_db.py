from scripts.bootstrap_db import schema_backfill_sql


def test_schema_backfill_adds_threading_columns_for_existing_tables():
    statements = [str(statement).lower() for statement in schema_backfill_sql()]

    assert any(
        "alter table emails add column if not exists user_id" in statement
        for statement in statements
    )
    assert any(
        "drop index if exists ix_emails_message_id" in statement
        for statement in statements
    )
    assert any(
        "create unique index if not exists uq_emails_owner_message_when_mailbox_null"
        in statement
        for statement in statements
    )
    assert any(
        "create unique index if not exists uq_emails_owner_mailbox_message" in statement
        for statement in statements
    )
    assert any(
        "alter table emails add column if not exists reply_to" in statement
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
    assert any(
        "create index if not exists ix_emails_thread_id" in statement
        for statement in statements
    )


def test_schema_backfill_does_not_force_legacy_llm_providers_into_org_local_dev():
    statements = [str(statement).lower() for statement in schema_backfill_sql()]

    assert not any(
        "update llm_providers set organization_id = 'org-local-dev'" in statement
        for statement in statements
    )
    assert any(
        "alter table llm_providers drop constraint if exists llm_providers_name_key"
        in statement
        for statement in statements
    )
    assert any(
        "create unique index if not exists uq_llm_providers_organization_name"
        in statement
        for statement in statements
    )


def test_schema_backfill_supports_explicit_legacy_llm_provider_org_mapping():
    statements = [
        str(statement).lower() for statement in schema_backfill_sql("org-acme")
    ]

    assert any(
        "update llm_providers set organization_id" in statement
        for statement in statements
    )


def test_schema_backfill_supports_explicit_legacy_email_owner_mapping():
    statements = [
        str(statement).lower() for statement in schema_backfill_sql(None, "testuser")
    ]

    assert any(
        "alter table emails add column if not exists user_id" in statement
        for statement in statements
    )
    assert any("update emails set user_id" in statement for statement in statements)


def test_schema_backfill_fails_closed_when_legacy_email_owner_mapping_is_missing():
    statements = [str(statement).lower() for statement in schema_backfill_sql()]

    assert any("emails where user_id is null" in statement for statement in statements)
    assert any("legacy_email_owner_user_id" in statement for statement in statements)
