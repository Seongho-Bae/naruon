import os

# Set required environment variables before importing settings
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test_db"

from core.config import settings

def test_global_config():
    assert hasattr(settings, "DATABASE_URL")
    assert hasattr(settings, "DEBUG")
    assert hasattr(settings, "ENCRYPTION_KEY")

def test_openai_config():
    from core.config import settings
    assert hasattr(settings, "OPENAI_EMBEDDING_MODEL")
    assert hasattr(settings, "OPENAI_MODEL")
