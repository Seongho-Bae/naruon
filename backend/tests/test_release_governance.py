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

    assert version == "0.1.0"


def test_changelog_follows_keep_a_changelog_for_initial_korean_release() -> None:
    changelog = read_repo_text("CHANGELOG.md")

    assert "Keep a Changelog" in changelog
    assert "https://keepachangelog.com/en/1.0.0/" in changelog
    assert "## [0.1.0] - 2026-05-09" in changelog
    assert "[0.0.0.1]" not in changelog
    assert "@seonghobae" in changelog
    assert "Seongho Bae (@seonghobae)" in changelog


def test_governed_workflows_do_not_use_unpinned_major_only_actions() -> None:
    assert WORKFLOW_DIR.exists(), "required governance artifact is missing: .github/workflows"
    governed_workflows = sorted(WORKFLOW_DIR.glob("*.yml")) + sorted(
        WORKFLOW_DIR.glob("*.yaml")
    )
    assert governed_workflows, "no governed GitHub workflows found"

    unpinned_major_refs: list[str] = []
    major_only_action = re.compile(
        r"uses:\s*['\"]?([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@v\d+['\"]?\s*$"
    )
    for workflow_path in governed_workflows:
        workflow_lines = workflow_path.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(workflow_lines, 1):
            if major_only_action.search(line):
                unpinned_major_refs.append(
                    f"{workflow_path.relative_to(REPO_ROOT)}:{line_number}:{line.strip()}"
                )

    assert unpinned_major_refs == []


def test_bandit_security_scan_does_not_continue_on_error() -> None:
    workflow = read_repo_text(".github/workflows/bandit.yml")

    assert "continue-on-error: true" not in workflow


def test_app_ci_runs_backend_and_frontend_checks_without_duplicate_release_pushes() -> None:
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


def test_docker_publish_validates_pr_images_and_publishes_semver_images_only_on_tags() -> None:
    workflow = read_repo_text(".github/workflows/docker-publish.yml")

    assert "pull_request:" in workflow
    assert "push:" in workflow
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
        "RUN npm run build"
    )
    assert "npm run build" in dockerfile
    assert 'CMD ["npm", "run", "start"' in dockerfile or "npm run start" in dockerfile
    assert "npm run dev" not in dockerfile


def test_compose_log_scanner_exists_for_warning_policy() -> None:
    scanner = read_repo_text("scripts/check_compose_logs.py")

    assert "warning|warn|deprecated|notice|fatal|denied|unable" in scanner
    assert "allowed_count" in scanner
    assert "unexpected_count" in scanner


def test_pr_governance_uses_metadata_only_events_without_checkout_or_admin_merge() -> None:
    workflow = read_repo_text(".github/workflows/pr-governance.yml")

    assert "pull_request_target:" in workflow
    assert "workflow_run:" in workflow
    assert "workflow_dispatch:" in workflow
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
    assert "actions/checkout" not in workflow
    assert "@coderabbitai ignore" not in workflow
    assert "git clone" not in workflow
    assert "--admin" not in workflow
    assert "contents: write" not in workflow
    assert "dismiss" not in workflow.lower()
