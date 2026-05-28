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


def test_settings_load_repo_root_env_when_started_from_backend_directory(
    monkeypatch, tmp_path
):
    backend_dir = tmp_path / "backend"
    backend_dir.mkdir()
    repo_env = tmp_path / ".env"
    database_url = "postgresql+asyncpg://root:root@localhost:5432/root_db"
    repo_env.write_text(
        "\n".join(
            [
                f"DATABASE_URL={database_url}",
                f"AUTH_SESSION_HMAC_SECRET={TEST_AUTH_SESSION_HMAC_SECRET}",
            ]
        )
        + "\n"
    )
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("AUTH_SESSION_HMAC_SECRET", raising=False)
    monkeypatch.chdir(backend_dir)

    loaded_settings = Settings()

    assert loaded_settings.DATABASE_URL == database_url


def test_settings_load_operator_home_env_when_project_env_is_absent(
    monkeypatch, tmp_path
):
    project_dir = tmp_path / "project" / "backend"
    home_dir = tmp_path / "home"
    project_dir.mkdir(parents=True)
    home_dir.mkdir()
    database_url = "postgresql+asyncpg://home:home@localhost:5432/home_db"
    (home_dir / ".env").write_text(
        "\n".join(
            [
                f"DATABASE_URL={database_url}",
                f"AUTH_SESSION_HMAC_SECRET={TEST_AUTH_SESSION_HMAC_SECRET}",
            ]
        )
        + "\n"
    )
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("AUTH_SESSION_HMAC_SECRET", raising=False)
    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.chdir(project_dir)

    loaded_settings = Settings()

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
