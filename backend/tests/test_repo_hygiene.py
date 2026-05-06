from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
UNSAFE_DEFAULT_DATABASE_CREDENTIAL = "postgres:" + "postgres@"
LEGACY_ENCRYPTION_FALLBACK_NAME = "FALLBACK" + "_KEY"
STATIC_BEARER_AUTH_NAME = "API_AUTH_" + "BEARER_TOKEN"


def test_dockerignore_excludes_nested_environment_files_but_keeps_examples():
    dockerignore = (REPO_ROOT / ".dockerignore").read_text()

    assert ".env*" in dockerignore
    assert "**/.env*" in dockerignore
    assert "!.env.example" in dockerignore
    assert "!**/.env.example" in dockerignore


def test_compose_externalizes_postgres_credentials():
    compose = (REPO_ROOT / "docker-compose.yml").read_text()

    assert "POSTGRES_PASSWORD: postgres" not in compose
    assert UNSAFE_DEFAULT_DATABASE_CREDENTIAL not in compose
    assert "${POSTGRES_DB" in compose
    assert "${POSTGRES_USER" in compose
    assert "${POSTGRES_PASSWORD" in compose
    assert "ENCRYPTION_KEY:" in compose
    assert "${ENCRYPTION_KEY:?" in compose


def test_kubernetes_backend_uses_secret_refs_for_database_and_encryption():
    deployment = (REPO_ROOT / "k8s/backend-deployment.yaml").read_text()

    assert UNSAFE_DEFAULT_DATABASE_CREDENTIAL not in deployment
    assert "DATABASE_URL" in deployment
    assert "ENCRYPTION_KEY" in deployment
    assert "secretKeyRef" in deployment


def test_env_example_documents_required_postgres_password():
    env_example = (REPO_ROOT / ".env.example").read_text()

    assert "POSTGRES_PASSWORD=change-me-local-only" in env_example
    assert UNSAFE_DEFAULT_DATABASE_CREDENTIAL not in env_example
    assert "postgres:change-me-local-only@" in env_example


def test_env_example_documents_signed_auth_token_inputs():
    env_example = (REPO_ROOT / ".env.example").read_text()

    assert STATIC_BEARER_AUTH_NAME not in env_example
    assert "API_AUTH_SIGNING_SECRET=" in env_example
    assert "NEXT_PUBLIC_API_AUTH_TOKEN=" in env_example


def test_backend_config_has_no_hardcoded_database_credentials():
    config = (REPO_ROOT / "backend/core/config.py").read_text()
    backend_readme = (REPO_ROOT / "backend/README.md").read_text()

    assert UNSAFE_DEFAULT_DATABASE_CREDENTIAL not in config
    assert "localhost:5432/ai_email" not in config
    assert UNSAFE_DEFAULT_DATABASE_CREDENTIAL not in backend_readme


def test_encrypted_string_has_no_hardcoded_fallback_key():
    models = (REPO_ROOT / "backend/db/models.py").read_text()

    assert LEGACY_ENCRYPTION_FALLBACK_NAME not in models


def test_backend_auth_uses_signed_subject_tokens_instead_of_static_shared_token():
    checked_paths = [
        REPO_ROOT / "backend/core/config.py",
        REPO_ROOT / "backend/api/auth.py",
        REPO_ROOT / "docker-compose.yml",
        REPO_ROOT / "k8s/backend-deployment.yaml",
    ]

    for path in checked_paths:
        content = path.read_text()
        assert STATIC_BEARER_AUTH_NAME not in content
        assert "API_AUTH_SIGNING_SECRET" in content


def test_readme_uses_cross_platform_browser_command():
    readme = (REPO_ROOT / "README.md").read_text()

    assert "open http://localhost:3000" not in readme
    assert (
        "python -m webbrowser http://localhost:3000" in readme
        or "python3 -m webbrowser http://localhost:3000" in readme
    )
