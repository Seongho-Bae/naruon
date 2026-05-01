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


def test_compose_requires_encryption_key_for_secret_fields():
    compose = (REPO_ROOT / "docker-compose.yml").read_text()

    assert "ENCRYPTION_KEY:" in compose
    assert "${ENCRYPTION_KEY:?Set ENCRYPTION_KEY" in compose


def test_readme_documents_encryption_key_generation():
    readme = (REPO_ROOT / "README.md").read_text()

    assert "ENCRYPTION_KEY" in readme
    assert "Fernet.generate_key" in readme


def test_readme_uses_cross_platform_browser_command():
    readme = (REPO_ROOT / "README.md").read_text()

    assert "open http://localhost:3000" not in readme
    assert (
        "python -m webbrowser http://localhost:3000" in readme
        or "python3 -m webbrowser http://localhost:3000" in readme
    )
