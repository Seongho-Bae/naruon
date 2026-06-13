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


def test_frontend_dockerfile_runs_as_non_root_user():
    dockerfile = (REPO_ROOT / "frontend" / "Dockerfile").read_text()

    assert "RUN chown -R node:node /app" in dockerfile
    assert "USER node" in dockerfile
    assert dockerfile.rfind("USER node") > dockerfile.rfind("RUN pnpm run build")


def test_ollama_dockerfile_keeps_pulled_models_available_to_runtime_user():
    dockerfile = (REPO_ROOT / "Dockerfile.ollama").read_text()

    assert "ENV OLLAMA_MODELS=/usr/share/ollama/.ollama/models" in dockerfile
    assert "useradd --system --create-home --home-dir /home/ollama" in dockerfile
    assert "curl " not in dockerfile
    assert "for attempt in $(seq 1 60)" in dockerfile
    assert "if ollama list > /dev/null 2>&1" in dockerfile
    assert "cat /tmp/ollama-build.log; exit 1" in dockerfile
    assert "ollama pull gemma4:e2b-it-qat" in dockerfile
    assert "ollama pull embeddinggemma" in dockerfile
    assert dockerfile.count("RUN set -eux;") >= 2
    assert dockerfile.find("ollama pull gemma4:e2b-it-qat") < dockerfile.find(
        "ollama pull embeddinggemma"
    )
    assert "ollama list | grep -E '^gemma4:e2b-it-qat[[:space:]]'" in dockerfile
    assert (
        "ollama list | grep -E '^embeddinggemma(:|[[:space:]])'" in dockerfile
    )
    assert "chown -R ollama:ollama /usr/share/ollama/.ollama" in dockerfile
    assert dockerfile.rfind("USER ollama") > dockerfile.rfind(
        "chown -R ollama:ollama /usr/share/ollama/.ollama"
    )


def test_backend_requirements_do_not_pin_yanked_email_validator():
    requirements = (REPO_ROOT / "backend" / "requirements.txt").read_text()

    assert "email-validator==2.1.0" not in requirements
    assert "email-validator==2.3.0" in requirements


def test_backend_requirements_pin_ruff_for_deterministic_ci():
    requirements = (REPO_ROOT / "backend" / "requirements.txt").read_text()

    assert "\nruff\n" not in f"\n{requirements}\n"
    assert "ruff==0.15.16" in requirements


def test_traefik_compose_services_disable_privilege_escalation():
    expected_next_service = {
        "docker-compose.infra.yml": "  prometheus:",
        "docker-compose.gateway.yml": "  keycloak:",
    }

    for compose_name, next_service in expected_next_service.items():
        compose = (REPO_ROOT / compose_name).read_text()
        traefik_block = compose.split("  traefik:", 1)[1].split(next_service, 1)[0]

        assert "security_opt:" in traefik_block
        assert "- no-new-privileges:true" in traefik_block


def test_compose_externalizes_postgres_credentials():
    compose = (REPO_ROOT / "docker-compose.yml").read_text()
    compose_without_runtime_preflights = (
        compose.replace(
            '$${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env before running Docker Compose}',
            "",
        )
        .replace(
            '$${AUTH_SESSION_HMAC_SECRET:?Set AUTH_SESSION_HMAC_SECRET in .env before running Docker Compose}',
            "",
        )
        .replace(
            '$${ENCRYPTION_KEY:?Set ENCRYPTION_KEY in .env before running Docker Compose}',
            "",
        )
    )

    assert "POSTGRES_PASSWORD: postgres" not in compose
    assert "postgres:postgres@" not in compose
    assert "POSTGRES_DB: ai_email" in compose
    assert "POSTGRES_USER: postgres" in compose
    assert "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}" in compose
    assert "- POSTGRES_PASSWORD" not in compose
    assert "POSTGRES_PASSWORD:-postgres" not in compose
    assert "${POSTGRES_PASSWORD" in compose
    assert "${POSTGRES_PASSWORD:?" not in compose_without_runtime_preflights
    assert '$${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env before running Docker Compose}' in compose
    assert "127.0.0.1:15432:5432" in compose
    assert "AUTH_SESSION_HMAC_SECRET" in compose
    assert "AUTH_SESSION_HMAC_SECRET: ${AUTH_SESSION_HMAC_SECRET}" in compose
    assert "- AUTH_SESSION_HMAC_SECRET" not in compose
    assert "${AUTH_SESSION_HMAC_SECRET:?" not in compose_without_runtime_preflights
    assert '$${AUTH_SESSION_HMAC_SECRET:?Set AUTH_SESSION_HMAC_SECRET in .env before running Docker Compose}' in compose
    assert "ENCRYPTION_KEY" in compose
    assert "ENCRYPTION_KEY: ${ENCRYPTION_KEY}" in compose
    assert "- ENCRYPTION_KEY" not in compose
    assert "${ENCRYPTION_KEY:?" not in compose_without_runtime_preflights
    assert '$${ENCRYPTION_KEY:?Set ENCRYPTION_KEY in .env before running Docker Compose}' in compose


def test_compose_allows_only_the_local_ollama_provider_host():
    local_compose = (REPO_ROOT / "docker-compose.yml").read_text()
    live_compose = (REPO_ROOT / "docker-compose.live-e2e.yml").read_text()

    def has_exact_compose_line(compose: str, *expected_lines: str) -> bool:
        normalized_lines = {
            line.strip().removeprefix("- ").strip() for line in compose.splitlines()
        }
        return any(expected_line in normalized_lines for expected_line in expected_lines)

    assert not has_exact_compose_line(
        "ALLOWED_LLM_BASE_URL_HOSTS=ollama,evil.example",
        "ALLOWED_LLM_BASE_URL_HOSTS=ollama",
    )

    for compose in (local_compose, live_compose):
        assert has_exact_compose_line(
            compose,
            'ALLOW_LOCAL_LLM_PROVIDERS: "true"',
            "ALLOW_LOCAL_LLM_PROVIDERS=true",
        )
        assert has_exact_compose_line(
            compose,
            'ALLOWED_LLM_BASE_URL_HOSTS: "ollama"',
            "ALLOWED_LLM_BASE_URL_HOSTS: ollama",
            "ALLOWED_LLM_BASE_URL_HOSTS=ollama",
        )
        assert has_exact_compose_line(
            compose,
            "OPENAI_BASE_URL: http://ollama:11434/v1",
            "OPENAI_BASE_URL=http://ollama:11434/v1",
        )
        assert has_exact_compose_line(
            compose,
            "OPENAI_MODEL: gemma4:e2b-it-qat",
            "OPENAI_MODEL=gemma4:e2b-it-qat",
        )


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


def test_env_example_does_not_ship_runtime_secret_defaults():
    env_example = (REPO_ROOT / ".env.example").read_text()

    assert "POSTGRES_DB=" not in env_example
    assert "POSTGRES_USER=" not in env_example
    assert "POSTGRES_PASSWORD=" not in env_example
    assert "DATABASE_URL=" not in env_example
    assert "AUTH_SESSION_HMAC_SECRET=" not in env_example
    assert "ENCRYPTION_KEY=" not in env_example
    assert "postgres:postgres@" not in env_example
    assert "change-me-local-only" not in env_example


def test_readme_uses_cross_platform_browser_command():
    readme = (REPO_ROOT / "README.md").read_text()

    assert "open http://localhost:3000" not in readme
    assert (
        "python -m webbrowser http://localhost:3000" in readme
        or "python3 -m webbrowser http://localhost:3000" in readme
    )
