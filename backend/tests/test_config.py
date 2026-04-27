from core.config import settings

def test_email_config():
    assert hasattr(settings, "SMTP_SERVER")
    assert hasattr(settings, "IMAP_SERVER")
    assert hasattr(settings, "OAUTH_CLIENT_ID")
