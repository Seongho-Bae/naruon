from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_dockerignore_excludes_nested_environment_files_but_keeps_examples():
    dockerignore = (REPO_ROOT / ".dockerignore").read_text()

    assert ".env*" in dockerignore
    assert "**/.env*" in dockerignore
    assert "!.env.example" in dockerignore
    assert "!**/.env.example" in dockerignore


def test_compose_externalizes_postgres_credentials():
    compose = (REPO_ROOT / "docker-compose.yml").read_text()

    assert "POSTGRES_PASSWORD: postgres" not in compose
    assert "postgres:postgres@" not in compose
    assert "${POSTGRES_DB" in compose
    assert "${POSTGRES_USER" in compose
    assert "${POSTGRES_PASSWORD" in compose


def test_env_example_documents_required_postgres_password():
    env_example = (REPO_ROOT / ".env.example").read_text()

    assert "POSTGRES_PASSWORD=change-me-local-only" in env_example
    assert "postgres:postgres@" not in env_example
    assert "postgres:change-me-local-only@" in env_example


def test_local_compose_defaults_to_fail_closed_auth_for_dev_only_stacks():
    compose = (REPO_ROOT / "docker-compose.yml").read_text()
    live_e2e_compose = (REPO_ROOT / "docker-compose.live-e2e.yml").read_text()

    assert "AUTH_MODE: ${AUTH_MODE:-hybrid}" in compose
    assert "TRUST_DEV_HEADERS: ${TRUST_DEV_HEADERS:-false}" in compose
    assert "AUTH_MODE: ${AUTH_MODE:-header}" not in compose
    assert "TRUST_DEV_HEADERS: ${TRUST_DEV_HEADERS:-true}" not in compose

    assert "AUTH_MODE: ${AUTH_MODE:-hybrid}" in live_e2e_compose
    assert "TRUST_DEV_HEADERS: ${TRUST_DEV_HEADERS:-false}" in live_e2e_compose
    assert "AUTH_MODE: ${AUTH_MODE:-header}" not in live_e2e_compose
    assert "TRUST_DEV_HEADERS: ${TRUST_DEV_HEADERS:-true}" not in live_e2e_compose
    assert "127.0.0.1:8000:8000" in compose
    assert "127.0.0.1:3000:3000" in compose
    assert "127.0.0.1:18080:8080" in live_e2e_compose


def test_env_example_defaults_to_fail_closed_auth_mode():
    env_example = (REPO_ROOT / ".env.example").read_text()

    assert "AUTH_MODE=hybrid" in env_example
    assert "TRUST_DEV_HEADERS=false" in env_example
    assert "LEGACY_EMAIL_OWNER_USER_ID=" in env_example
    assert "LEGACY_EMAIL_OWNER_USER_ID=testuser" not in env_example


def test_readme_uses_cross_platform_browser_command():
    readme = (REPO_ROOT / "README.md").read_text()

    assert "open http://localhost:3000" not in readme
    assert (
        "python -m webbrowser http://localhost:3000" in readme
        or "python3 -m webbrowser http://localhost:3000" in readme
    )
