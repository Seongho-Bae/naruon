from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_alembic_scaffold_exists_with_model_metadata_target():
    alembic_ini = BACKEND_ROOT / "alembic.ini"
    env_py = BACKEND_ROOT / "alembic" / "env.py"

    assert alembic_ini.exists()
    assert env_py.exists()

    alembic_ini_text = alembic_ini.read_text()
    env_text = env_py.read_text()

    assert "script_location = alembic" in alembic_ini_text
    assert "sqlalchemy.url =" in alembic_ini_text
    assert "from db.models import Base" in env_text
    assert "target_metadata = Base.metadata" in env_text
    assert "settings.DATABASE_URL" in env_text


def test_initial_alembic_revision_records_current_schema_path():
    versions_dir = BACKEND_ROOT / "alembic" / "versions"
    revisions = sorted(versions_dir.glob("*.py"))

    assert revisions
    revision_text = "\n".join(path.read_text() for path in revisions)

    assert 'revision = "0001_initial_control_plane"' in revision_text
    assert "down_revision = None" in revision_text
    assert "CREATE EXTENSION IF NOT EXISTS vector" in revision_text
    assert "Base.metadata.create_all" in revision_text
    assert "schema_backfill_sql" in revision_text


def test_provider_writeback_retry_queue_has_incremental_revision():
    versions_dir = BACKEND_ROOT / "alembic" / "versions"
    revision_text = "\n".join(path.read_text() for path in sorted(versions_dir.glob("*.py")))

    assert 'revision = "0002_provider_retry_queue"' in revision_text
    assert 'down_revision = "0001_initial_control_plane"' in revision_text
    assert "op.create_table(" in revision_text
    assert '"provider_writeback_retry_items"' in revision_text
    assert '"retry_item_uid"' in revision_text
    assert '"command_payload_encrypted"' in revision_text
    assert '"retry_state"' in revision_text
    assert "ix_provider_writeback_retry_items_scope_state" in revision_text
    assert "has_table" in revision_text
    assert "op.create_index(" in revision_text
    assert "if_not_exists=True" in revision_text
    assert "op.drop_index(" in revision_text
    assert "if_exists=True" in revision_text


def test_migration_runner_uses_alembic_upgrade_head_not_bootstrap_create_all():
    migration_runner = BACKEND_ROOT / "scripts" / "migrate_db.py"

    assert migration_runner.exists()
    runner_text = migration_runner.read_text()

    assert "command.upgrade" in runner_text
    assert '"head"' in runner_text
    assert "script_location" in runner_text
    assert "bootstrap_db" not in runner_text
    assert "create_all" not in runner_text


def test_backend_requirements_include_alembic():
    requirements = (BACKEND_ROOT / "requirements.txt").read_text()

    assert any(
        line.split("==", maxsplit=1)[0] == "alembic"
        for line in requirements.splitlines()
    )
