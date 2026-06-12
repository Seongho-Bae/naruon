"""Regression tests for release governance artifacts.

These tests intentionally exercise repository-level release contracts from the
backend test suite so CI catches drift in versioning, changelog, and GitHub
workflow governance before a release branch can land.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"


def read_repo_text(relative_path: str) -> str:
    """Read a repository file with a clear assertion when it is missing."""
    path = REPO_ROOT / relative_path
    assert path.exists(), f"required governance artifact is missing: {relative_path}"
    return path.read_text(encoding="utf-8")


def test_root_version_exists_and_is_initial_semver_release() -> None:
    version = read_repo_text("VERSION").strip()

    assert re.fullmatch(
        r"\d+\.\d+\.\d+", version
    ), f"VERSION is not valid SemVer: {version!r}"


def test_changelog_follows_keep_a_changelog_for_initial_korean_release() -> None:
    changelog = read_repo_text("CHANGELOG.md")

    assert "Keep a Changelog" in changelog
    assert "https://keepachangelog.com/en/1.0.0/" in changelog
    assert "## [0.1.0] - 2026-05-09" in changelog
    assert "[0.0.0.1]" not in changelog
    assert "@seonghobae" in changelog
    assert "Seongho Bae (@seonghobae)" in changelog


def test_governed_workflows_do_not_use_unpinned_major_only_actions() -> None:
    assert (
        WORKFLOW_DIR.exists()
    ), "required governance artifact is missing: .github/workflows"
    governed_workflows = sorted(WORKFLOW_DIR.glob("*.yml")) + sorted(
        WORKFLOW_DIR.glob("*.yaml")
    )
    assert governed_workflows, "no governed GitHub workflows found"

    unpinned_major_refs: list[str] = []
    missing_version_comments: list[str] = []
    major_only_action = re.compile(
        r"uses:\s*['\"]?([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@v\d+['\"]?\s*$"
    )
    sha_without_version_comment = re.compile(
        r"uses:\s*['\"]?[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}['\"]?\s*$"
    )
    for workflow_path in governed_workflows:
        workflow_lines = workflow_path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(workflow_lines, 1):
            if major_only_action.search(line):
                unpinned_major_refs.append(
                    f"{workflow_path.relative_to(REPO_ROOT)}:{line_number}:{line.strip()}"
                )
            elif sha_without_version_comment.search(line):
                missing_version_comments.append(
                    f"{workflow_path.relative_to(REPO_ROOT)}:{line_number}:{line.strip()}"
                )

    assert unpinned_major_refs == []
    assert missing_version_comments == []


def test_bandit_security_scan_does_not_continue_on_error() -> None:
    workflow = read_repo_text(".github/workflows/bandit.yml")

    assert "continue-on-error: true" not in workflow


def test_app_ci_runs_backend_and_frontend_checks_without_duplicate_release_pushes() -> (
    None
):
    workflow = read_repo_text(".github/workflows/app-ci.yml")

    assert "pull_request:" in workflow
    assert "release/**" in workflow
    assert "python -m pytest" in workflow
    assert "PYTHONWARNINGS: error" in workflow
    assert 'DISABLE_BACKGROUND_WORKERS: "1"' in workflow
    assert "npm test" in workflow
    assert "npm run lint" in workflow
    assert "npm run build" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "concurrency:" in workflow
    assert "${{ github.event.pull_request.number || github.ref }}" in workflow
    assert "uses: actions/checkout@v" not in workflow
    assert "uses: actions/setup-python@v" not in workflow
    assert "uses: actions/setup-node@v" not in workflow

    push_block = workflow.split("push:", 1)[1].split("pull_request:", 1)[0]
    assert "master" in push_block
    assert "release/**" not in push_block


def test_docker_publish_validates_pr_images_and_publishes_semver_images_only_on_tags() -> (
    None
):
    workflow = read_repo_text(".github/workflows/docker-publish.yml")

    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true" in workflow
    assert (
        workflow.count(
            "docker/setup-qemu-action@ce360397dd3f832beb865e1373c09c0e9f86d70a # v4.0.0"
        )
        == 2
    )
    assert (
        workflow.count(
            "docker/setup-buildx-action@4d04d5d9486b7bd6fa91e7baf45bbb4f8b9deedd # v4.0.0"
        )
        == 2
    )
    assert (
        "docker/login-action@4907a6ddec9925e35a0a9e82d7399ccc52663121 # v4.1.0"
        in workflow
    )
    assert (
        "docker/metadata-action@030e881283bb7a6894de51c315a6bfe6a94e05cf # v6.0.0"
        in workflow
    )
    assert (
        workflow.count(
            "docker/build-push-action@bcafcacb16a39f128d818304e6c9c0c18556b85f # v7.1.0"
        )
        == 2
    )
    push_block = workflow.split("push:", 1)[1].split("pull_request:", 1)[0]
    assert "tags:" in push_block
    assert "branches:" not in push_block
    assert "ai_email_client-backend" in workflow
    assert "ai_email_client-frontend" in workflow
    assert "push: false" in workflow
    assert "push: true" in workflow
    assert "type=semver" in workflow
    assert "type=ref,event=branch" not in workflow


def test_frontend_dockerfile_builds_and_starts_production_artifact() -> None:
    dockerfile = read_repo_text("frontend/Dockerfile")

    assert dockerfile.index("ARG NEXT_PUBLIC_API_URL") < dockerfile.index(
        "RUN pnpm run build"
    )
    assert "pnpm run build" in dockerfile
    assert "ENV POSTCSS_WORKERS=1" in dockerfile
    assert "ENV DISABLE_POSTCSS_WORKERS=true" in dockerfile
    assert (
        'CMD ["./node_modules/.bin/next", "start", "--hostname", "0.0.0.0", "--port", "3000"]'
        in dockerfile
    )
    assert "pnpm run start" not in dockerfile
    assert "pnpm run dev" not in dockerfile


def test_backend_dockerfile_uses_modern_env_syntax() -> None:
    dockerfile = read_repo_text("Dockerfile")

    assert "FROM python:3.11-slim AS backend-runtime" in dockerfile
    assert "ENV PYTHONDONTWRITEBYTECODE=1" in dockerfile
    assert "ENV PYTHONUNBUFFERED=1" in dockerfile
    assert "pnpm install --frozen-lockfile" in dockerfile
    assert "pnpm run build" in dockerfile
    assert "FROM backend-runtime" in dockerfile
    assert "COPY --from=frontend-builder /usr/local/bin/node" in dockerfile
    assert "nodejs" not in dockerfile
    assert "ENV PYTHONDONTWRITEBYTECODE 1" not in dockerfile
    assert "ENV PYTHONUNBUFFERED 1" not in dockerfile
    assert "secrets.token_hex" not in dockerfile
    assert "ENV DATABASE_URL=" not in dockerfile
    assert '"/app/scripts/docker_entrypoint.sh"' in dockerfile
    assert "RUN chmod +x /app/scripts/docker_entrypoint.sh" in dockerfile
    assert "COPY scripts/start_combined.sh" not in dockerfile
    assert "RUN echo '#!/bin/bash" not in dockerfile
    assert "uvicorn" not in dockerfile.split("CMD", 1)[1]


def test_combined_image_start_script_preflights_env_and_logs_service_exit() -> None:
    start_script = read_repo_text("backend/scripts/docker_entrypoint.sh")

    assert "for var in DATABASE_URL AUTH_SESSION_HMAC_SECRET ENCRYPTION_KEY" in start_script
    assert "Fernet.generate_key()" in start_script
    assert "database bootstrap failed" in start_script
    assert "Backend and frontend will not start." in start_script
    assert "Starting backend (uvicorn :8000)" in start_script
    assert "Starting frontend (next start :3000)" in start_script
    assert 'wait -n "$backend_pid" "$frontend_pid"' in start_script
    assert "Backend (:8000) exited with code" in start_script
    assert "Frontend (:3000) exited with code" in start_script


def test_backend_compose_commands_use_startup_preflight() -> None:
    compose = read_repo_text("docker-compose.yml")
    live_e2e_compose = read_repo_text("docker-compose.live-e2e.yml")

    backend_block = compose.split("  backend:", 1)[1].split("  frontend:", 1)[0]
    assert "target: backend-runtime" in backend_block
    assert 'DEBUG: "false"' in backend_block
    assert 'DEBUG: "true"' not in backend_block
    assert "python scripts/bootstrap_db.py && python scripts/start_backend.py" in compose
    assert '"scripts/start_backend.py"' in live_e2e_compose
    assert "Dockerfile.ollama" in live_e2e_compose
    assert "DATABASE_URL: ${DATABASE_URL:?Set DATABASE_URL for live E2E}" in live_e2e_compose
    assert "postgresql+asyncpg://" not in live_e2e_compose
    assert '"127.0.0.1:18080:8080"' in live_e2e_compose
    assert 'OLLAMA_NO_CLOUD: "true"' in compose
    assert 'OLLAMA_NO_CLOUD: "true"' in live_e2e_compose
    assert "OPENAI_BASE_URL: http://ollama:11434/v1" in live_e2e_compose
    assert "OPENAI_MODEL: gemma4:e2b-it-qat" in live_e2e_compose
    assert "OPENAI_EMBEDDING_MODEL: embeddinggemma" in live_e2e_compose
    live_nginx = read_repo_text("tests/live/nginx.conf")
    assert "proxy_read_timeout 600s" in live_nginx
    assert 'add_header Referrer-Policy "strict-origin-when-cross-origin" always;' in live_nginx
    assert 'add_header X-Content-Type-Options "nosniff" always;' in live_nginx
    assert 'add_header X-Frame-Options "DENY" always;' in live_nginx


def test_compose_log_scanner_exists_for_warning_policy() -> None:
    scanner = read_repo_text("scripts/check_compose_logs.py")

    assert "warning|warn|deprecated|notice|fatal|denied|unable" in scanner
    assert "allowed_count" in scanner
    assert "unexpected_count" in scanner
    assert "Use --ui/--no-ui" in scanner
    assert "or deprecated --webui/--no-webui" in scanner


def test_strix_workflow_uses_github_models_default_and_narrow_warning_filter() -> (
    None
):
    workflow = read_repo_text(".github/workflows/strix.yml")
    gate_script = read_repo_text("scripts/ci/strix_quick_gate.sh")

    assert 'group: strix-${{ github.repository }}' in workflow
    assert "cancel-in-progress: false" in workflow
    assert "models: read" in workflow
    assert "provider_mode=github_models" in workflow
    assert "strix_llm:" in workflow
    assert "github.event.inputs.strix_llm || 'openai/gpt-5'" in workflow
    assert "secrets.STRIX_LLM ||" not in workflow
    assert "https://models.github.ai/inference" in workflow
    assert "LLM_API_BASE_FILE" in workflow
    assert "STRIX_GITHUB_MODELS_TOKEN is required for GitHub Models Strix scans" in workflow
    assert "secrets.STRIX_GITHUB_MODELS_TOKEN" in workflow
    assert "openai/gpt-5-mini* | openai/gpt-5-nano*" in workflow
    assert "vertex_ai/gemini-3.1-pro-preview-customtools" in workflow
    assert (
        "secrets.STRIX_LLM == 'vertex_ai/gemini-3.1-pro-preview-customtools' "
        "&& 'vertex_ai/gemini-2.5-flash'"
        not in workflow
    )
    assert 'STRIX_FAIL_ON_PROVIDER_SIGNAL: "1"' in workflow
    assert 'STRIX_VERTEX_FALLBACK_MODELS: ""' in workflow
    assert (
        "vertex_ai/gemini-3.1-pro-preview-customtools | vertex_ai/gemini-2.5-flash"
        in workflow
    )
    assert "vertex_ai/* | vertex_ai_beta/*" not in workflow
    assert "PYTHONWARNINGS:" not in workflow
    assert (
        'child_env["PYTHONWARNINGS"] = '
        '"ignore:Pydantic serializer warnings:UserWarning:pydantic.main"'
        in gate_script
    )
    assert "ignore::UserWarning" not in workflow


def test_pr_governance_uses_metadata_only_events_without_checkout_or_admin_merge() -> (
    None
):
    workflow = read_repo_text(".github/workflows/pr-governance.yml")
    gate_script = read_repo_text("scripts/ci/pr_governance_gate.sh")
    combined = f"{workflow}\n{gate_script}"

    assert "pull_request_target:" in workflow
    assert "workflow_run:" in workflow
    assert "check_run:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "Strix Security Scan" in workflow
    assert "- strix" not in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "trusted-governance" in workflow
    assert ".base.sha" in workflow
    assert "github.sha" not in workflow
    assert "tarball/${trusted_ref}" in workflow
    assert "gh_api_with_retry" in workflow
    assert "GitHub API request attempt" in workflow
    assert "Trusted governance ref must be a full commit SHA" in workflow
    assert "trusted_archive_candidate" in workflow
    assert "tar -tzf" in workflow
    assert "Trusted governance archive materialization attempt" in workflow
    assert "after 4 attempts" in workflow
    assert 'bash "$GOVERNANCE_GATE"' in workflow
    assert "CHECK_RUN_PR_NUMBER" in workflow
    assert "headRefOid" in gate_script
    assert "mergeStateStatus" in gate_script
    assert "gh pr checks" in gate_script and "--required" in gate_script
    assert "check-runs" in gate_script
    assert "Review skipped" in gate_script
    assert "CodeRabbit" in gate_script or "coderabbit" in gate_script
    assert "BEHIND" in gate_script
    assert "app.slug" in gate_script
    assert "coderabbitai" in gate_script
    assert "/issues/${PR_NUMBER}/comments" in gate_script
    assert "COMMENT_MARKER" in gate_script
    assert "Waiting for" in gate_script
    assert "reviewThreads" in gate_script
    assert "CHANGES_REQUESTED" in gate_script
    assert "gh pr merge" not in gate_script
    assert "--match-head-commit" not in gate_script
    assert "actions/checkout" not in combined
    assert "@coderabbitai ignore" not in combined
    assert "git clone" not in combined
    assert "--admin" not in combined
    assert "contents: write" not in combined
    assert "continue-on-error: true" not in combined
    assert "dismiss" not in combined.lower()


def test_coderabbit_approval_is_decoupled_from_github_checks() -> None:
    config = read_repo_text(".coderabbit.yaml")
    policy = read_repo_text("docs/development/merge-gate-policy.md")
    agents = read_repo_text("AGENTS.md")

    assert "request_changes_workflow: true" in config
    assert "github-checks:" in config
    assert "enabled: false" in config
    assert "GitHub Checks integration stays disabled" in policy
    assert "GitHub Checks integration disabled" in agents
