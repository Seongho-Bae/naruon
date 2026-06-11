from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_dockerignore_excludes_nested_environment_files_but_keeps_examples():
    dockerignore = (REPO_ROOT / ".dockerignore").read_text()

    assert ".env*" in dockerignore
    assert "**/.env*" in dockerignore
    assert "!.env.example" in dockerignore
    assert "!**/.env.example" in dockerignore


def test_backend_dockerfile_suppresses_pip_root_warning():
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()

    assert "PIP_ROOT_USER_ACTION=ignore" in dockerfile
    assert "PIP_DISABLE_PIP_VERSION_CHECK=1" in dockerfile


def test_backend_requirements_do_not_pin_yanked_email_validator():
    requirements = (REPO_ROOT / "backend" / "requirements.txt").read_text()

    assert "email-validator==2.1.0" not in requirements
    assert "email-validator==2.3.0" in requirements


def test_compose_externalizes_postgres_credentials():
    compose = (REPO_ROOT / "docker-compose.yml").read_text()

    assert "POSTGRES_PASSWORD: postgres" not in compose
    assert "postgres:postgres@" not in compose
    assert "${POSTGRES_DB" in compose
    assert "${POSTGRES_USER" in compose
    assert "${POSTGRES_PASSWORD" in compose
    assert "AUTH_SESSION_HMAC_SECRET" in compose
    assert "${AUTH_SESSION_HMAC_SECRET:?" in compose
    assert "ENCRYPTION_KEY" in compose
    assert "${ENCRYPTION_KEY:?" in compose


def test_compose_wrapper_uses_operator_env_file_without_bulk_secret_injection():
    wrapper = (REPO_ROOT / "scripts" / "naruon_compose.sh").read_text()
    gateway_compose = (REPO_ROOT / "docker-compose.gateway.yml").read_text()
    local_compose = (REPO_ROOT / "docker-compose.yml").read_text()

    assert "NARUON_ENV_FILE" in wrapper
    assert "${HOME}/.env" in wrapper
    assert 'docker compose --env-file "${env_file}" "$@"' in wrapper
    assert "env_file:" not in gateway_compose
    assert "env_file:" not in local_compose


def test_postgres_ha_compose_requires_external_postgres_password():
    compose = (REPO_ROOT / "docker-compose.postgres-ha.yml").read_text()

    assert "POSTGRES_PASSWORD:-postgres" not in compose
    assert "${POSTGRES_PASSWORD:?" in compose


def test_kubernetes_backend_database_url_comes_from_secret():
    manifest = (REPO_ROOT / "k8s" / "backend-deployment.yaml").read_text()

    assert "postgres:postgres@" not in manifest
    assert "secretKeyRef" in manifest
    assert "DATABASE_URL" in manifest
    assert "AUTH_SESSION_HMAC_SECRET" in manifest
    assert "auth-session-hmac-secret" in manifest


def test_kubernetes_postgres_password_comes_from_secret():
    manifest = (REPO_ROOT / "k8s" / "db-statefulset.yaml").read_text()

    assert "name: POSTGRES_PASSWORD\n          value: postgres" not in manifest
    assert "secretKeyRef" in manifest
    assert "POSTGRES_PASSWORD" in manifest


def test_env_example_documents_required_postgres_password():
    env_example = (REPO_ROOT / ".env.example").read_text()

    assert "POSTGRES_PASSWORD=change-me-local-only" in env_example
    assert "AUTH_SESSION_HMAC_SECRET=" in env_example
    assert "postgres:postgres@" not in env_example
    assert "postgres:change-me-local-only@" in env_example


def test_readme_uses_cross_platform_browser_command():
    readme = (REPO_ROOT / "README.md").read_text()

    assert "open http://localhost:3000" not in readme
    assert (
        "python -m webbrowser http://localhost:3000" in readme
        or "python3 -m webbrowser http://localhost:3000" in readme
    )
