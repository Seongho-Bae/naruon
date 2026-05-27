import os
import secrets
from typing import Any, cast

import pytest
from pydantic import ValidationError

TEST_AUTH_SESSION_HMAC_SECRET = os.environ.setdefault(
    "AUTH_SESSION_HMAC_SECRET", secrets.token_urlsafe(48)
)

# Set required environment variables before importing settings
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test_db"

from core.config import Settings, settings  # noqa: E402


def _settings_without_env_file() -> Settings:
    return Settings(**cast(dict[str, Any], {"_env_file": None}))


def test_global_config():
    assert hasattr(settings, "DATABASE_URL")
    assert hasattr(settings, "DEBUG")
    assert hasattr(settings, "RUNTIME_ENVIRONMENT")
    assert hasattr(settings, "ENCRYPTION_KEY")


def test_production_settings_do_not_expose_dev_header_bypass_controls():
    assert "TRUST_DEV_HEADERS" not in settings.__class__.model_fields
    assert "DEV_AUTH_TOKEN" not in settings.__class__.model_fields


def test_database_url_is_required(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        _settings_without_env_file()


def test_database_url_loads_from_environment(monkeypatch):
    database_url = "postgresql+asyncpg://test:test@localhost:5432/test_db"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("AUTH_SESSION_HMAC_SECRET", TEST_AUTH_SESSION_HMAC_SECRET)

    loaded_settings = _settings_without_env_file()

    assert loaded_settings.DATABASE_URL == database_url


def test_production_settings_reject_missing_auth_session_hmac_secret(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
    )
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", "production")
    monkeypatch.delenv("AUTH_SESSION_HMAC_SECRET", raising=False)

    with pytest.raises(ValidationError, match="AUTH_SESSION_HMAC_SECRET is required"):
        _settings_without_env_file()


def test_production_settings_reject_short_auth_session_hmac_secret(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
    )
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_SESSION_HMAC_SECRET", "weak-secret")

    with pytest.raises(ValidationError, match="at least 32 bytes"):
        _settings_without_env_file()


def test_production_settings_reject_repeated_auth_session_hmac_secret(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
    )
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", "production")
    monkeypatch.setenv("AUTH_SESSION_HMAC_SECRET", "A" * 32)

    with pytest.raises(ValidationError, match="must not be a repeated character"):
        _settings_without_env_file()


def test_settings_reject_public_auth_session_hmac_fixture(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
    )
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", "production")
    monkeypatch.setenv(
        "AUTH_SESSION_HMAC_SECRET",
        "naruon-session-hmac-token-32-byte-minimum",
    )

    with pytest.raises(ValidationError, match="public fixture value"):
        _settings_without_env_file()


def test_non_production_settings_reject_missing_auth_session_hmac_secret(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
    )
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", "local")
    monkeypatch.delenv("AUTH_SESSION_HMAC_SECRET", raising=False)

    with pytest.raises(ValidationError, match="AUTH_SESSION_HMAC_SECRET is required"):
        _settings_without_env_file()


def test_non_production_settings_reject_short_auth_session_hmac_secret(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
    )
    monkeypatch.setenv("RUNTIME_ENVIRONMENT", "local")
    monkeypatch.setenv("AUTH_SESSION_HMAC_SECRET", "weak-secret")

    with pytest.raises(ValidationError, match="at least 32 bytes"):
        _settings_without_env_file()


def test_settings_repr_redacts_auth_session_hmac_secret(monkeypatch):
    secret = TEST_AUTH_SESSION_HMAC_SECRET
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
    )
    monkeypatch.setenv("AUTH_SESSION_HMAC_SECRET", secret)

    loaded_settings = _settings_without_env_file()

    assert secret not in repr(loaded_settings)
    assert "**********" in repr(loaded_settings)


def test_openai_config():
    from core.config import settings

    assert hasattr(settings, "OPENAI_EMBEDDING_MODEL")
    assert hasattr(settings, "OPENAI_MODEL")


def test_oidc_settings_must_be_configured_together(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
    )
    monkeypatch.setenv("AUTH_SESSION_HMAC_SECRET", TEST_AUTH_SESSION_HMAC_SECRET)
    monkeypatch.setenv("OIDC_ISSUER_URL", "https://login.example.com/realms/naruon")
    monkeypatch.delenv("OIDC_CLIENT_ID", raising=False)
    monkeypatch.delenv("OIDC_JWKS_URL", raising=False)

    with pytest.raises(
        ValidationError,
        match="OIDC_ISSUER_URL, OIDC_CLIENT_ID, and OIDC_JWKS_URL",
    ):
        _settings_without_env_file()


def test_oidc_settings_accept_complete_configuration(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
    )
    monkeypatch.setenv("AUTH_SESSION_HMAC_SECRET", TEST_AUTH_SESSION_HMAC_SECRET)
    monkeypatch.setenv("OIDC_ISSUER_URL", "https://login.example.com/realms/naruon")
    monkeypatch.setenv("OIDC_CLIENT_ID", "naruon-api")
    monkeypatch.setenv("OIDC_JWKS_URL", "https://login.example.com/realms/naruon/jwks")

    loaded_settings = _settings_without_env_file()

    assert loaded_settings.OIDC_CLIENT_ID == "naruon-api"
