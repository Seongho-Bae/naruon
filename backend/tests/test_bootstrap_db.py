from scripts.bootstrap_db import schema_backfill_sql


def test_schema_backfill_adds_threading_columns_for_existing_tables():
    statements = [str(statement).lower() for statement in schema_backfill_sql()]

    assert any("alter table emails add column if not exists reply_to" in statement for statement in statements)
    assert any("alter table emails add column if not exists thread_id" in statement for statement in statements)
    assert any("alter table emails add column if not exists in_reply_to" in statement for statement in statements)
    assert any("alter table emails add column if not exists \"references\"" in statement for statement in statements)
    assert any("create index if not exists ix_emails_thread_id" in statement for statement in statements)
