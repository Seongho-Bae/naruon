import os

# Set required environment variables before importing settings
os.environ["DATABASE_URL"] = "postgresql+asyncpg://localhost:5432/test_db"

import pytest
from pydantic import ValidationError

from core.config import Settings, settings


def test_global_config():
    assert hasattr(settings, "DATABASE_URL")
    assert hasattr(settings, "DEBUG")
    assert hasattr(settings, "ENCRYPTION_KEY")


def test_openai_config():
    from core.config import settings

    assert hasattr(settings, "OPENAI_EMBEDDING_MODEL")
    assert hasattr(settings, "OPENAI_MODEL")


def test_database_url_is_required_without_env_or_env_file(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_database_url_rejects_default_postgres_credentials():
    username = "postgres"
    password = "postgres"

    with pytest.raises(ValidationError, match="default PostgreSQL credentials"):
        Settings(
            _env_file=None,
            DATABASE_URL=(
                f"postgresql+asyncpg://{username}:{password}@localhost:5432/ai_email"
            ),
        )
