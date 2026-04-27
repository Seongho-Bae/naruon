import os

# Set required environment variables before importing settings
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test_db"

from core.config import settings

def test_email_config():
    assert hasattr(settings, "SMTP_SERVER")
    assert hasattr(settings, "SMTP_PORT")
    assert hasattr(settings, "IMAP_SERVER")
    assert hasattr(settings, "IMAP_PORT")
    assert hasattr(settings, "OAUTH_CLIENT_ID")
    assert hasattr(settings, "OAUTH_CLIENT_SECRET")
    assert hasattr(settings, "OAUTH_REDIRECT_URI")

def test_openai_config():
    from core.config import settings
    assert hasattr(settings, "OPENAI_API_KEY")
