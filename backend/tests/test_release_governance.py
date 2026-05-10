import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def read_text(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_application_ci_runs_backend_frontend_checks_and_avoids_duplicate_runs():
    workflow = read_text(".github/workflows/app-ci.yml")

    assert "pull_request:" in workflow
    assert "branches: [master" in workflow or "branches:\n      - master" in workflow
    assert "release/**" in workflow
    assert (
        "push:\n    branches: [master]" in workflow
        or "push:\n    branches:\n      - master" in workflow
    )
    assert 'push:\n    branches: [master, "release/**"]' not in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "PYTHONWARNINGS: error" in workflow
    assert 'DISABLE_BACKGROUND_WORKERS: "1"' in workflow
    assert "concurrency:" in workflow
    assert "${{ github.event.pull_request.number || github.ref }}" in workflow
    assert "python -m pytest -q" in workflow
    assert "npm test" in workflow
    assert "npm run lint" in workflow
    assert "npm run build" in workflow
    assert "uses: actions/checkout@v" not in workflow
    assert "uses: actions/setup-python@v" not in workflow
    assert "uses: actions/setup-node@v" not in workflow


def test_bandit_security_scan_fails_on_findings_after_sarif_upload():
    workflow = read_text(".github/workflows/bandit.yml")

    assert (
        "push:\n    branches: [master]" in workflow
        or "push:\n    branches:\n      - master" in workflow
    )
    assert 'push:\n    branches: [ master, "release/**" ]' not in workflow
    assert "continue-on-error: true" not in workflow
    assert "requirements-bandit-ci.txt" not in workflow
    assert "bandit[sarif]==1.8.6" in workflow
    assert "uses: actions/checkout@v" not in workflow
    assert "uses: actions/setup-python@v" not in workflow
    assert "uses: github/codeql-action/upload-sarif@v" not in workflow
    assert "if: ${{ always()" in workflow
    assert "bandit-results.sarif" in workflow


def test_docker_publish_validates_prs_and_publishes_versioned_backend_frontend_images():
    workflow = read_text(".github/workflows/docker-publish.yml")
    push_block = workflow.split("push:", 1)[1].split("pull_request:", 1)[0]

    assert "pull_request:" in workflow
    assert "release/**" in workflow
    assert "tags:" in push_block
    assert "branches:" not in push_block
    assert "linux/amd64" in workflow
    assert "linux/arm64" in workflow
    assert "ai_email_client-backend" in workflow
    assert "ai_email_client-frontend" in workflow
    assert "push: false" in workflow
    assert "push: true" in workflow
    assert "type=semver" in workflow
    assert "type=ref,event=branch" not in workflow
    assert "Read release version" in workflow
    assert "type=raw,value=${{ steps.version.outputs.version }}" in workflow
    assert "id: build" in workflow
    assert "steps.build.outputs.digest" in workflow
    assert "GITHUB_STEP_SUMMARY" in workflow
    assert "NEXT_PUBLIC_API_URL" in workflow
    assert (
        "packages: write" not in workflow.split("pull_request_image_validation:", 1)[0]
    )
    assert "publish_images:" in workflow
    assert "uses: actions/checkout@v" not in workflow
    assert "uses: docker/" not in "\n".join(
        line for line in workflow.splitlines() if re.search(r"uses: docker/.+@v", line)
    )


def test_pr_governance_automates_metadata_only_robot_review_gate():
    workflow = read_text(".github/workflows/pr-governance.yml")

    assert "pull_request_target:" in workflow
    assert "workflow_run:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "actions/checkout" not in workflow
    assert "@coderabbitai ignore" not in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "headRefOid" in workflow
    assert "mergeStateStatus" in workflow
    assert "gh pr checks" in workflow and "--required" in workflow
    assert "check-runs" in workflow
    assert "CodeRabbit" in workflow or "coderabbit" in workflow
    assert "BEHIND" in workflow
    assert "app.slug" in workflow
    assert "coderabbitai" in workflow
    assert "/issues/${PR_NUMBER}/comments" in workflow
    assert "reviewThreads" in workflow
    assert "--match-head-commit" in workflow
    assert "--admin" not in workflow
    assert "dismiss" not in workflow.lower()
    assert 'echo "::notice::' not in workflow


def test_strix_enabled_scan_fails_closed_when_report_artifact_is_missing():
    workflow = read_text(".github/workflows/strix.yml")

    assert "if-no-files-found: error" in workflow
    assert "if-no-files-found: warn" not in workflow


def test_mail_smoke_uses_self_hosted_runner_without_turning_naruon_into_mail_server():
    workflow = read_text(".github/workflows/mail-smoke.yml")

    assert "workflow_dispatch:" in workflow
    assert "self-hosted" in workflow
    assert "mail-egress" in workflow
    assert "environment: mail-egress" in workflow
    assert "MAIL_SMOKE_IMAP_HOST" in workflow
    assert "MAIL_SMOKE_SMTP_HOST" in workflow
    assert "pull_request" not in workflow
    assert "listen" not in workflow.lower()
    assert "MX" not in workflow
    assert "MAIL_SMOKE_ALLOWED_HOSTS" in workflow
    assert "ipaddress" in workflow
    assert "MAIL_SMOKE_ALLOWED_HOSTS must not be empty" in workflow
    assert "verified_hosts = validate_target" in workflow
    assert "socket.create_connection((verified_hosts[0], port)" in workflow
    assert "server_hostname=host" in workflow
    assert workflow.index("validate_target") < workflow.index(
        "socket.create_connection"
    )


def test_frontend_dockerfile_builds_production_artifact():
    dockerfile = read_text("frontend/Dockerfile")

    assert dockerfile.index("ARG NEXT_PUBLIC_API_URL") < dockerfile.index(
        "RUN npm run build"
    )
    assert dockerfile.index("ARG NEXT_PUBLIC_API_AUTH_TOKEN") < dockerfile.index(
        "RUN npm run build"
    )
    assert "ENV NEXT_PUBLIC_API_AUTH_TOKEN" in dockerfile
    assert "npm run build" in dockerfile
    assert "npm run start" in dockerfile
    assert "npm run dev" not in dockerfile


def test_local_compose_wires_single_mailbox_bearer_auth():
    compose = read_text("docker-compose.yml")
    config = read_text("backend/core/config.py")

    assert "API_AUTH_TOKEN" in config
    assert "AUTH_SINGLE_USER_ID" in config
    assert "API_AUTH_TOKEN: ${API_AUTH_TOKEN:-change-me-local-only}" in compose
    assert "AUTH_SINGLE_USER_ID: ${AUTH_SINGLE_USER_ID:-default}" in compose
    assert "NEXT_PUBLIC_API_AUTH_TOKEN" in compose


def test_backend_dockerfile_keeps_dependency_install_output_visible_for_warning_scans():
    dockerfile = read_text("Dockerfile")

    assert "pip install --no-cache-dir -r requirements.txt" in dockerfile
    assert "--quiet -r requirements.txt" not in dockerfile


def test_observability_and_release_operations_are_documented_and_composable():
    compose = read_text("docker-compose.yml")
    observability = read_text("docs/operations/observability.md")
    mail_runner = read_text("docs/operations/mail-runner.md")
    postgres_ops = read_text("docs/operations/postgres-replication.md")

    assert "otel-collector" in compose
    assert "prometheus" in compose
    assert "grafana" in compose
    assert "loki" in compose
    assert "tempo" in compose
    assert "backend-worker" in compose
    assert "OpenTelemetry" in observability
    assert "Prometheus" in observability
    assert "Grafana" in observability
    assert "Naruon은 이메일 서버가 아닙니다" in mail_runner
    assert "self-hosted runner" in mail_runner
    assert "물리 복제" in postgres_ops
    assert "pg_is_in_recovery" in postgres_ops


def test_backend_tracing_exports_to_otel_collector_instead_of_only_documenting_apm():
    requirements = read_text("backend/requirements.txt")
    config = read_text("backend/core/config.py")
    main = read_text("backend/main.py")
    compose = read_text("docker-compose.yml")
    observability_path = REPO_ROOT / "backend/core/observability.py"

    assert observability_path.exists()
    observability_module = observability_path.read_text(encoding="utf-8")
    assert "opentelemetry-sdk==" in requirements
    assert "opentelemetry-exporter-otlp-proto-grpc==" in requirements
    assert "opentelemetry-instrumentation-fastapi==" in requirements
    assert "OTEL_EXPORTER_OTLP_ENDPOINT" in config
    assert re.search(r"configure_tracing\(\s*app\s*,", main)
    assert "OTLPSpanExporter" in observability_module
    assert "FastAPIInstrumentor.instrument_app" in observability_module
    assert 'excluded_urls="/healthz,/readyz,/metrics"' in observability_module
    assert "OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4317" in compose


def test_edge_auth_and_gateway_follow_up_is_documented():
    architecture = read_text("ARCHITECTURE.md")
    edge_auth = read_text("docs/operations/edge-auth.md")
    acceptance = read_text("docs/development/release-governance-acceptance.md")

    assert "Keycloak" in architecture
    assert "Casdoor" in architecture
    assert "Traefik" in architecture
    assert "Keycloak" in edge_auth
    assert "Casdoor" in edge_auth
    assert "Traefik" in edge_auth
    assert "OIDC" in edge_auth
    assert "auth_request" in edge_auth
    assert "인증/게이트웨이" in acceptance


def test_postgres_replication_docs_cover_routing_pooling_and_nul_text_policy():
    postgres_ops = read_text("docs/operations/postgres-replication.md")
    architecture = read_text("ARCHITECTURE.md")

    assert "PgBouncer" in postgres_ops
    assert "PgCat" in postgres_ops
    assert "DATABASE_URL_READ_ONLY" in postgres_ops
    assert "primary-only" in postgres_ops
    assert "NUL" in postgres_ops
    assert "\\u0000" in postgres_ops
    assert "\\x00" in postgres_ops
    assert "NUL" in architecture


def test_python_dependencies_do_not_pin_yanked_email_validator_release():
    requirements = read_text("backend/requirements.txt")

    assert "email-validator==2.1.0" not in requirements
    assert "email-validator==2.3.0" in requirements


def test_frontend_direct_dependencies_are_audit_clean_floor_versions():
    package_json = json.loads(read_text("frontend/package.json"))

    assert "shadcn" not in package_json["dependencies"]
    assert package_json["overrides"]["hono"] == "^4.12.18"
    assert package_json["overrides"]["fast-uri"] == "^3.1.2"
    assert package_json["overrides"]["ip-address"] == "^10.1.1"


def test_version_and_changelog_follow_semver_and_keep_a_changelog_contracts():
    version = read_text("VERSION").strip()
    changelog = read_text("CHANGELOG.md")

    assert re.fullmatch(r"0\.1\.0", version)
    assert "https://keepachangelog.com/en/1.0.0/" in changelog
    assert "## [0.1.0] - 2026-05-09" in changelog
    assert "[0.0.0.1]" not in changelog
    assert "@seonghobae" in changelog
    assert "Seongho Bae (@seonghobae)" in changelog
    assert "Keep a Changelog" in changelog
    assert len(changelog.splitlines()) >= 2000
