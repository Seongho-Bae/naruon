from scripts.bootstrap_db import schema_backfill_sql


def test_schema_backfill_adds_threading_columns_for_existing_tables():
    statements = [str(statement).lower() for statement in schema_backfill_sql()]

    assert any(
        "alter table emails add column if not exists user_id" in statement
        for statement in statements
    )
    assert any("update emails set user_id" in statement for statement in statements)
    assert any(
        "alter table emails alter column user_id set not null" in statement
        for statement in statements
    )
    assert any(
        "create index if not exists ix_emails_user_id" in statement
        for statement in statements
    )
    assert any(
        "drop constraint if exists emails_message_id_key" in statement
        for statement in statements
    )
    assert any(
        "drop index if exists ix_emails_message_id" in statement
        for statement in statements
    )
    assert any(
        "create index if not exists ix_emails_message_id" in statement
        for statement in statements
    )
    assert any(
        "create unique index if not exists uq_emails_user_id_message_id" in statement
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
