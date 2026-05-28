import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "start_backend.py"


def _load_start_backend_module():
    spec = importlib.util.spec_from_file_location("start_backend", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_database_url_fails_before_uvicorn_import(
    monkeypatch, tmp_path, capsys
):
    module = _load_start_backend_module()
    home_dir = tmp_path / "home"
    app_dir = tmp_path / "app"
    home_dir.mkdir()
    app_dir.mkdir()
    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("AUTH_SESSION_HMAC_SECRET", raising=False)
    monkeypatch.delenv("NARUON_ENV_FILE", raising=False)
    monkeypatch.delenv("NARUON_BACKEND_ENV_FILE", raising=False)
    monkeypatch.chdir(app_dir)

    exit_code = module.main()

    captured = capsys.readouterr()
    assert exit_code == module.CONFIG_ERROR_EXIT_CODE
    assert "Missing required backend runtime env: DATABASE_URL" in captured.err
    assert "AUTH_SESSION_HMAC_SECRET" in captured.err
    assert "Traceback" not in captured.err


def test_operator_env_file_passes_startup_preflight(monkeypatch, tmp_path):
    module = _load_start_backend_module()
    env_file = tmp_path / "backend.env"
    env_file.write_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test_db",
                "AUTH_SESSION_HMAC_SECRET=local-runtime-session-key-0123456789",
            ]
        )
        + "\n"
    )
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("AUTH_SESSION_HMAC_SECRET", raising=False)
    monkeypatch.setenv("NARUON_ENV_FILE", str(env_file))
    monkeypatch.setenv("NARUON_STARTUP_CHECK_ONLY", "1")

    assert module.main() == 0
