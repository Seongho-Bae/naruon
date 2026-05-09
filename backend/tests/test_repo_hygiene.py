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


def test_compose_keeps_postgres_internal_and_uses_password_auth_for_initdb():
    compose = (REPO_ROOT / "docker-compose.yml").read_text()

    assert "${POSTGRES_HOST_PORT" not in compose
    assert "internal: true" in compose
    assert "POSTGRES_INITDB_ARGS" in compose
    assert "--auth-local=scram-sha-256" in compose
    assert "--auth-host=scram-sha-256" in compose
    assert "PGPASSWORD=" in compose
    assert "pg_isready -h 127.0.0.1" in compose


def test_compose_host_facing_service_ports_are_overridable():
    compose = (REPO_ROOT / "docker-compose.yml").read_text()

    assert "127.0.0.1:${BACKEND_HOST_PORT:-8000}:8000" in compose
    assert "127.0.0.1:${FRONTEND_HOST_PORT:-3000}:3000" in compose
    assert "127.0.0.1:${OTEL_GRPC_HOST_PORT:-4317}:4317" in compose
    assert "127.0.0.1:${OTEL_HTTP_HOST_PORT:-4318}:4318" in compose
    assert "127.0.0.1:${PROMETHEUS_HOST_PORT:-9090}:9090" in compose
    assert "127.0.0.1:${GRAFANA_HOST_PORT:-3001}:3000" in compose
    assert "127.0.0.1:${LOKI_HOST_PORT:-3100}:3100" in compose
    assert "127.0.0.1:${TEMPO_HOST_PORT:-3200}:3200" in compose


def test_observability_configs_avoid_startup_warning_defaults():
    otel = (REPO_ROOT / "observability" / "otel-collector.yml").read_text()
    prometheus = (REPO_ROOT / "observability" / "prometheus.yml").read_text()
    tempo = (REPO_ROOT / "observability" / "tempo.yml").read_text()
    compose = (REPO_ROOT / "docker-compose.yml").read_text()
    alloy = (REPO_ROOT / "observability" / "config.alloy").read_text()

    assert "0.0.0.0" not in otel
    assert "endpoint: otel-collector:4317" in otel
    assert "endpoint: otel-collector:4318" in otel
    assert "endpoint: otel-collector:8889" in otel
    assert "otlp/tempo" in otel
    assert "endpoint: tempo:4317" in otel
    assert "insecure: true" in otel
    assert 'targets: ["otel-collector:8889"]' in prometheus
    assert "metrics_generator:" in tempo
    assert "frontend_address: 127.0.0.1:9095" in tempo
    assert "endpoint: tempo:4317" in tempo
    assert "endpoint: tempo:4318" in tempo
    assert "promtail" not in compose.lower()
    assert "grafana/alloy" in compose
    assert "config.alloy" in compose
    assert "-log.level=error" not in compose
    assert "GF_LOG_LEVEL" not in compose
    assert "http://tempo:3200/ready" in compose
    assert "condition: service_healthy" in compose
    assert "loki.source.docker" in alloy
    assert "loki.write" in alloy


def test_compose_log_policy_uses_exact_allowlist_instead_of_blanket_suppression():
    checker = (REPO_ROOT / "scripts" / "check_compose_logs.py").read_text()
    observability = (REPO_ROOT / "docs" / "operations" / "observability.md").read_text()

    assert "GF_LOG_LEVEL" not in checker
    assert "-log.level=error" not in checker
    assert "Skipping migration: Already executed" in checker
    assert "unowned file entry ignored during wal replay" in checker
    assert "exact allowlist" in observability


def test_alloy_collects_only_opted_in_compose_containers_to_avoid_stale_host_logs():
    compose = (REPO_ROOT / "docker-compose.yml").read_text()
    alloy = (REPO_ROOT / "observability" / "config.alloy").read_text()

    assert 'naruon.logging: "enabled"' in compose
    assert "__meta_docker_container_label_naruon_logging" in alloy
    assert 'regex         = "enabled"' in alloy
    assert 'action        = "keep"' in alloy


def test_env_example_documents_required_postgres_password():
    env_example = (REPO_ROOT / ".env.example").read_text()

    assert "POSTGRES_PASSWORD=change-me-local-only" in env_example
    assert "postgres:postgres@" not in env_example
    assert "postgres:change-me-local-only@" in env_example


def test_readme_uses_cross_platform_browser_command():
    readme = (REPO_ROOT / "README.md").read_text()

    assert "open http://localhost:3000" not in readme
    assert (
        "python -m webbrowser http://localhost:3000" in readme
        or "python3 -m webbrowser http://localhost:3000" in readme
    )


def test_kubernetes_manifests_do_not_ship_plaintext_db_credentials_or_latest_images():
    k8s_text = "\n".join(
        path.read_text() for path in sorted((REPO_ROOT / "k8s").glob("*.yaml"))
    )

    assert "postgres:postgres" not in k8s_text
    assert "POSTGRES_PASSWORD\n          value: postgres" not in k8s_text
    assert "secretKeyRef" in k8s_text
    assert ":latest" not in k8s_text
    assert "ai_email_client-backend:0.1.0" in k8s_text
    assert "ai_email_client-frontend:0.1.0" in k8s_text


def test_postgres_statefulset_declares_storage_and_health_contracts():
    db_statefulset = (REPO_ROOT / "k8s/db-statefulset.yaml").read_text()

    assert "volumeClaimTemplates" in db_statefulset
    assert "readinessProbe" in db_statefulset
    assert "livenessProbe" in db_statefulset
    assert "resources:" in db_statefulset
    assert "pgvector/pgvector:pg16" not in db_statefulset


def test_local_scanner_outputs_are_ignored():
    gitignore = (REPO_ROOT / ".gitignore").read_text()

    assert "bandit-results.sarif" in gitignore
    assert "strix_runs/" in gitignore
