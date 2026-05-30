from __future__ import annotations

import secrets

from scripts import start_backend


def _clear_runtime_settings(monkeypatch) -> None:
    for setting_name in (
        "DATABASE_URL",
        "AUTH_SESSION_HMAC_SECRET",
        "OIDC_ISSUER_URL",
        "OIDC_CLIENT_ID",
        "OIDC_JWKS_URL",
        "ALLOWED_OIDC_HOSTS",
    ):
        monkeypatch.delenv(setting_name, raising=False)


def test_start_backend_reports_missing_database_url_without_import_traceback(
    monkeypatch, tmp_path, capsys
):
    _clear_runtime_settings(monkeypatch)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.chdir(tmp_path)

    exit_code = start_backend.main([])
    captured = capsys.readouterr()

    assert exit_code == 78
    assert "Missing required runtime settings: DATABASE_URL" in captured.err
    assert "AUTH_SESSION_HMAC_SECRET" in captured.err
    assert "Traceback" not in captured.err
    assert "pydantic" not in captured.err


def test_start_backend_accepts_operator_home_env_file(monkeypatch, tmp_path):
    _clear_runtime_settings(monkeypatch)
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    (home_dir / ".env").write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test_db",
                f"AUTH_SESSION_HMAC_SECRET={secrets.token_urlsafe(48)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.chdir(tmp_path)

    assert start_backend.validate_runtime_settings() == []


def test_start_backend_can_run_preflight_only_with_valid_settings(monkeypatch):
    _clear_runtime_settings(monkeypatch)
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
    )
    monkeypatch.setenv("AUTH_SESSION_HMAC_SECRET", secrets.token_urlsafe(48))
    monkeypatch.setenv("NARUON_STARTUP_PREFLIGHT_ONLY", "1")

    assert start_backend.main([]) == 0


def test_start_backend_rejects_partial_oidc_configuration(monkeypatch, tmp_path):
    _clear_runtime_settings(monkeypatch)
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
    )
    monkeypatch.setenv("AUTH_SESSION_HMAC_SECRET", secrets.token_urlsafe(48))
    monkeypatch.setenv("OIDC_ISSUER_URL", "https://login.example.test/realms/naruon")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.chdir(tmp_path)

    assert start_backend.validate_runtime_settings() == [
        "OIDC_ISSUER_URL, OIDC_CLIENT_ID, and OIDC_JWKS_URL must be set together"
    ]


def test_start_backend_rejects_oidc_without_allowed_hosts(monkeypatch, tmp_path):
    _clear_runtime_settings(monkeypatch)
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
    )
    monkeypatch.setenv("AUTH_SESSION_HMAC_SECRET", secrets.token_urlsafe(48))
    monkeypatch.setenv("OIDC_ISSUER_URL", "https://login.example.test/realms/naruon")
    monkeypatch.setenv("OIDC_CLIENT_ID", "naruon-api")
    monkeypatch.setenv("OIDC_JWKS_URL", "https://login.example.test/realms/naruon/jwks")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.chdir(tmp_path)

    assert start_backend.validate_runtime_settings() == [
        "ALLOWED_OIDC_HOSTS must list trusted OIDC issuer and JWKS hosts"
    ]


def test_start_backend_rejects_untrusted_oidc_jwks_host(monkeypatch, tmp_path):
    _clear_runtime_settings(monkeypatch)
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
    )
    monkeypatch.setenv("AUTH_SESSION_HMAC_SECRET", secrets.token_urlsafe(48))
    monkeypatch.setenv("OIDC_ISSUER_URL", "https://login.example.test/realms/naruon")
    monkeypatch.setenv("OIDC_CLIENT_ID", "naruon-api")
    monkeypatch.setenv("OIDC_JWKS_URL", "https://127.0.0.1/jwks")
    monkeypatch.setenv("ALLOWED_OIDC_HOSTS", "login.example.test")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.chdir(tmp_path)

    assert start_backend.validate_runtime_settings() == [
        "OIDC_JWKS_URL host must be listed in ALLOWED_OIDC_HOSTS"
    ]
