from scripts.bootstrap_db import schema_backfill_sql


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
    assert any("existing emails require explicit non-default" in statement for statement in statements)
    assert any(
        "create index if not exists ix_emails_thread_id" in statement
        for statement in statements
    )


def test_schema_backfill_uses_only_explicit_non_default_owner_ids(monkeypatch):
    monkeypatch.setenv("NARUON_IMPORT_USER_ID", "import-user")
    monkeypatch.setenv("NARUON_IMPORT_ORGANIZATION_ID", "import-org")

    statements = [str(statement).lower() for statement in schema_backfill_sql()]

    assert any(
        "update emails set user_id" in statement
        and "where user_id is null" in statement
        for statement in statements
    )
    assert any(
        "update emails set organization_id" in statement
        and "where organization_id is null" in statement
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
