# Release, Deployment, Packaging, CI/CD Governance Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** `master` 기준의 release/deployment/packaging/CI/CD governance를 #118 meta issue와 Gitflow release 흐름에 맞게 증거 기반으로 복구한다.

**Architecture:** 기존 `origin/release/ci-cd-governance-20260509` branch의 검증된 산출물을 무비판적으로 merge하지 않고, current default branch에서 확인된 root cause와 GitHub alert evidence를 기준으로 필요한 조각을 TDD로 이식한다. GitHub Actions는 stable check name, fail-closed security gate, PR metadata-only governance, SemVer/GHCR image evidence, live Docker E2E evidence를 분리한다.

**Tech Stack:** GitHub Actions, FastAPI/Python/pytest, Next.js 16/npm/Vitest/Playwright, Docker/Compose/GHCR, Kubernetes manifests, OpenTelemetry/Prometheus/Grafana/Loki/Tempo documentation.

---

## Current evidence snapshot

- Worktree: `.worktrees/release-deployment-ci-governance-20260511`.
- Branch: `release/deployment-ci-governance-20260511` from `origin/master`.
- Default branch HEAD: `2779678a323f6b4e8fa0cc1b1fbd8e3618d27659`.
- Canonical meta issue: #118.
- New follow-up issues connected under #118: #135, #136, #137, #138, #139.
- Org ruleset blocker: `14316398` requires `required_approving_review_count=1` and `require_last_push_approval=true`.
- Repo ruleset target: `15586698` uses `required_approving_review_count=0`, `require_last_push_approval=false`, and keeps thread resolution.
- Open Code scanning alerts: unpinned `docker/login-action@v3`, `docker/metadata-action@v5`, `docker/build-push-action@v5` in `.github/workflows/docker-publish.yml`.
- Open Dependabot alerts: `ip-address`, `hono`, and `fast-uri` transitive dependency chain in `frontend/package-lock.json`.
- Secret scanning open alerts: 0.

## Implementation rules

- Use TDD for behavior/config changes: write or port a failing regression test first, watch it fail, then change workflow/code/docs.
- Do not remove features to make checks green. Trace the “why” first.
- Do not downgrade a library unless compatibility evidence is recorded.
- Do not use `@coderabbitai ignore`, review dismissal, bypass actors, or admin merge.
- Do not add a local CodeQL workflow unless GitHub default setup is explicitly disabled. Current duplicate Analyze evidence points to dynamic/default setup duplication, not missing workflow code.
- Live E2E must start from Docker image build and run real HTTP/browser paths, not in-process clients or fetch mocks.
- Warnings, deprecations, notices, fatal errors, denied logs, and scanner warnings are failures unless a third-party warning is narrowly documented.

---

### Task 1: Port release governance regression tests first

**Files:**
- Create/modify: `backend/tests/test_release_governance.py`
- Read reference: `origin/release/ci-cd-governance-20260509:backend/tests/test_release_governance.py`

**Step 1: Write or port the failing tests**

Include tests that assert:

- root `VERSION` exists and equals `0.1.0`.
- `CHANGELOG.md` follows Keep a Changelog and includes Korean `## [0.1.0] - 2026-05-09`.
- `[0.0.0.1]` never appears.
- `@seonghobae` and `Seongho Bae (@seonghobae)` attribution exist.
- Governed workflows have no unpinned `uses: owner/action@vN` references.
- Bandit has no `continue-on-error: true`.
- App CI runs backend and frontend checks without duplicate release-branch push triggers.
- Docker publish validates PR image builds and publishes backend/frontend SemVer images only on tags.
- PR governance uses metadata-only `pull_request_target`/`workflow_run` without checkout or admin merge.

**Step 2: Run the tests to verify RED**

Run:

```bash
cd backend && python3 -m pytest tests/test_release_governance.py -q
```

Expected initially: FAIL because `VERSION`, `CHANGELOG.md`, `app-ci.yml`, hardened workflow pins, and PR governance do not exist on this branch.

**Step 3: Commit?**

Do not commit after RED alone. Proceed to Task 2 implementation, then commit a logical green set.

---

### Task 2: Add SemVer release identity and Korean changelog source of truth

**Files:**
- Create: `VERSION`
- Create: `CHANGELOG.md`
- Modify if needed: `README.md`, `CONTRIBUTING.md`
- Reference: `origin/release/ci-cd-governance-20260509:VERSION`
- Reference: `origin/release/ci-cd-governance-20260509:CHANGELOG.md`

**Step 1: Add minimal implementation**

- Set `VERSION` to `0.1.0`.
- Bring in the Korean Keep a Changelog 0.1.0 entry from the release branch as the starting point.
- Keep the content meaningful and file/evidence based. Do not paste raw merge logs.
- Preserve attribution format: `Seongho Bae (@seonghobae)`.
- Include SWE/requester/operator context: `Seongho Bae (@seonghobae)의 SWE execution/operator context`.

**Step 2: Verify GREEN for release identity tests**

Run:

```bash
cd backend && python3 -m pytest tests/test_release_governance.py::test_version_and_changelog_follow_semver_and_keep_a_changelog_contracts -q
```

Expected: PASS.

---

### Task 3: Harden Bandit and GitHub Actions SHA pinning

**Files:**
- Modify: `.github/workflows/bandit.yml`
- Modify: `.github/workflows/docker-publish.yml`
- Later-created workflows must also use full SHA pins.
- Modify: `AGENTS.md` or create it if missing.
- Modify: `.agents/skills/fix-development-mistakes/SKILL.md`

**Step 1: Verify RED from Task 1 tests**

Run:

```bash
cd backend && python3 -m pytest tests/test_release_governance.py::test_bandit_security_scan_fails_on_findings_after_sarif_upload -q
cd backend && python3 -m pytest tests/test_release_governance.py::test_github_actions_are_pinned_to_full_commit_shas -q
```

Expected initially: FAIL due `continue-on-error: true` and `docker/*@v*` refs.

**Step 2: Implement minimal fix**

- Remove `continue-on-error: true` from Bandit scan.
- Pin Bandit install to `bandit[sarif]==1.8.6` unless a newer secure version is proven compatible.
- Keep SARIF upload with `if: always()` and pin `github/codeql-action/upload-sarif` to a full SHA.
- Pin `actions/checkout`, `actions/setup-python`, `docker/login-action`, `docker/metadata-action`, and `docker/build-push-action` to verified full SHAs with version comments.
- Record the recurrence-prevention rule in `AGENTS.md` and `.agents/skills/fix-development-mistakes/SKILL.md`.

**Step 3: Verify GREEN**

Run:

```bash
cd backend && python3 -m pytest tests/test_release_governance.py::test_bandit_security_scan_fails_on_findings_after_sarif_upload -q
cd backend && python3 -m pytest tests/test_release_governance.py::test_github_actions_are_pinned_to_full_commit_shas -q
```

Expected: PASS.

---

### Task 4: Add Application CI without duplicate push/PR check noise

**Files:**
- Create: `.github/workflows/app-ci.yml`
- Modify: `docs/development/merge-gate-policy.md`

**Step 1: Verify RED**

Run:

```bash
cd backend && python3 -m pytest tests/test_release_governance.py::test_application_ci_runs_backend_frontend_checks_and_avoids_duplicate_runs -q
```

Expected initially: FAIL because the workflow is missing.

**Step 2: Implement minimal workflow**

- Workflow name: `Application CI`.
- Triggers: `pull_request` to `master`/`release/**`, `push` to `master` only.
- Permissions: `contents: read`.
- Backend job: install Python dependencies and run `cd backend && PYTHONWARNINGS=error DISABLE_BACKGROUND_WORKERS=1 python -m pytest -q`.
- Frontend job: `cd frontend && npm ci && npm test && npm run lint && npm run build`.
- Keep job names stable: `backend`, `frontend`.

**Step 3: Verify GREEN**

Run the same test. Expected: PASS.

---

### Task 5: Replace Docker publish with PR validation and SemVer GHCR release path

**Files:**
- Modify: `.github/workflows/docker-publish.yml`
- Modify: `Dockerfile`
- Modify: `frontend/Dockerfile`
- Modify: `docker-compose.yml` only if needed for image/runtime parity.

**Step 1: Verify RED**

Run:

```bash
cd backend && python3 -m pytest tests/test_release_governance.py::test_docker_publish_validates_prs_and_publishes_versioned_backend_frontend_images -q
```

Expected initially: FAIL because current workflow builds one image and publishes on `master` pushes.

**Step 2: Implement minimal workflow**

- Workflow name: `Build and Publish Docker Images`.
- Matrix components: backend and frontend.
- PR behavior: build only, `push: false`, no registry writes.
- Tag behavior: only `v*`, validate `v$(cat VERSION)`, publish to GHCR.
- Image names:
  - `ghcr.io/${{ github.repository_owner }}/ai_email_client-backend`
  - `ghcr.io/${{ github.repository_owner }}/ai_email_client-frontend`
- Platforms: `linux/amd64,linux/arm64`.
- Enable `provenance: true` and `sbom: true` where supported.
- Record digest and component in `$GITHUB_STEP_SUMMARY`.
- Frontend Dockerfile must run production build/start, not `npm run dev`.

**Step 3: Verify GREEN**

Run the release governance Docker test.

**Step 4: Manual local build verification**

Run:

```bash
docker build --pull --progress=plain -t naruon-backend:local -f Dockerfile .
docker build --pull --progress=plain -t naruon-frontend:local -f frontend/Dockerfile --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 .
```

Expected: both build without warnings treated as failures where the tool supports it.

---

### Task 6: Add metadata-only PR governance automation

**Files:**
- Create: `.github/workflows/pr-governance.yml`
- Modify: `docs/development/merge-gate-policy.md`

**Step 1: Verify RED**

Run:

```bash
cd backend && python3 -m pytest tests/test_release_governance.py::test_pr_governance_automates_metadata_only_robot_review_gate -q
```

Expected initially: FAIL because the workflow is missing.

**Step 2: Implement minimal workflow**

- Use `pull_request_target`, `workflow_run`, and `workflow_dispatch`.
- Do not checkout PR head.
- Use GitHub API metadata only.
- Detect draft PR, BEHIND state, conflicts, unresolved threads, missing current-head CodeRabbit evidence, and failed required checks.
- Enable auto-merge only with `gh pr merge --auto --merge --match-head-commit "$HEAD_SHA"`.
- Never use `--admin`, review dismissal, bypass, or `@coderabbitai ignore`.

**Step 3: Verify GREEN**

Run the PR governance test. Expected: PASS.

---

### Task 7: Add live Docker E2E design and initial strict test harness

**Files:**
- Create: `docker-compose.live-e2e.yml`
- Create: `tests/live/nginx.conf`
- Create: `backend/tests/live/test_live_api_sequence.py`
- Create: `backend/tests/live/seed_live_data.py`
- Create: `frontend/playwright.config.ts`
- Create: `frontend/e2e/live-smoke.spec.ts`
- Modify: `frontend/package.json`
- Modify: `backend/pytest.ini`

**Step 1: Write failing tests/harness checks**

- Live API test must require `--live-base-url` or environment variable.
- Live tests must forbid `TestClient`, `ASGITransport`, `unittest.mock`, and frontend fetch mocks in live paths.
- Browser E2E must fail on console warning/error and page errors.

**Step 2: Verify RED**

Run:

```bash
cd backend && PYTHONWARNINGS=error python3 -m pytest -q tests/live/test_live_api_sequence.py --live-base-url=http://127.0.0.1:18080
```

Expected initially: FAIL because the live stack is not running. This is acceptable RED for the harness; the failure must be a connection/availability failure, not import/test syntax error.

**Step 3: Implement minimal live stack**

- Build backend/frontend images first.
- Compose live stack must use `image:` values from `BACKEND_IMAGE` and `FRONTEND_IMAGE`, not source build.
- Add nginx load-balancer service to avoid host port conflicts with `--scale backend=3`.
- Seed deterministic live data through backend container or a dedicated test helper.

**Step 4: Verify live path**

Run:

```bash
export POSTGRES_PASSWORD=live-e2e-local-only
export BACKEND_IMAGE=naruon-backend:local
export FRONTEND_IMAGE=naruon-frontend:local
docker build --pull --progress=plain -t "$FRONTEND_IMAGE" -f frontend/Dockerfile --build-arg NEXT_PUBLIC_API_URL=http://127.0.0.1:18080 .
docker compose -f docker-compose.live-e2e.yml up -d --scale backend=3
cd backend && PYTHONWARNINGS=error python3 -m pytest -q tests/live/test_live_api_sequence.py --live-base-url=http://127.0.0.1:18080
cd frontend && LIVE_BASE_URL=http://127.0.0.1:18080 NODE_OPTIONS="--throw-deprecation --trace-warnings" npx playwright test --project=chromium --reporter=line
docker compose -f docker-compose.live-e2e.yml logs --no-color
docker compose -f docker-compose.live-e2e.yml down -v
```

Expected: tests pass and logs have no warning/error/deprecation/fatal/denied strings after known non-error infrastructure noise is eliminated.

---

### Task 8: Add operations architecture docs and link them

**Files:**
- Create: `docs/operations/release-deployment-architecture.md`
- Create: `docs/operations/open-source-apm.md`
- Create: `docs/operations/email-relay-proxy-boundary.md`
- Create: `docs/operations/postgresql-physical-replication.md`
- Create: `docs/operations/auth-key-management.md`
- Create: `docs/operations/traefik-evaluation.md`
- Modify: `README.md`
- Modify: `ARCHITECTURE.md`
- Modify: `SECURITY.md`
- Modify: `docs/development/merge-gate-policy.md`

**Step 1: Add docs with Confirmed/Hypothesis labels**

- Confirmed sections must cite current repo files.
- Hypothesis sections must not claim production readiness.
- Explicitly state Naruon is not an email server. It is a web client server and can relay/proxy member-configured email servers.
- APM must default to OpenTelemetry, Prometheus, Grafana, Loki, Tempo/Jaeger.
- PostgreSQL physical replication must include WAL/archive/restore drills and state current single-primary limitation.
- Auth/key management must evaluate Keycloak and Casdoor without premature adoption.
- Traefik must be evaluated against current NGINX ingress assumption.

**Step 2: Verify docs link and content**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
required = [
    'docs/operations/release-deployment-architecture.md',
    'docs/operations/open-source-apm.md',
    'docs/operations/email-relay-proxy-boundary.md',
    'docs/operations/postgresql-physical-replication.md',
    'docs/operations/auth-key-management.md',
    'docs/operations/traefik-evaluation.md',
]
for path in required:
    text = Path(path).read_text()
    assert 'Confirmed' in text or '확인된 사실' in text
    assert 'Hypothesis' in text or '가설' in text
print('operation docs verified')
PY
```

Expected: PASS.

---

### Task 9: Fix frontend dependency alerts without downgrade

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Modify/add tests if dependency removal affects behavior.

**Step 1: Reproduce dependency tree evidence**

Run:

```bash
cd frontend && npm ls ip-address hono fast-uri || true
cd frontend && npm audit --package-lock-only --omit=dev --audit-level=moderate
```

Expected initially: evidence of vulnerable transitive chain or current PR #133 removal path.

**Step 2: Implement minimal fix**

- Prefer removing unused vulnerable CLI dependency if confirmed, as in PR #133.
- If not removable, upgrade parent dependency so transitive packages resolve to patched versions.
- Do not downgrade without compatibility proof.

**Step 3: Verify GREEN**

Run:

```bash
cd frontend && npm ci
cd frontend && npm audit --package-lock-only --omit=dev --audit-level=moderate
cd frontend && npm test && npm run lint && npm run build
```

Expected: 0 vulnerabilities at moderate+, tests/lint/build pass.

---

### Task 10: Full local verification and review

**Files:**
- All changed files.

**Step 1: Run backend verification**

Run:

```bash
cd backend && DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python -m pytest -q
```

Expected: PASS, no warnings.

**Step 2: Run frontend verification**

Run:

```bash
cd frontend && NODE_OPTIONS="--throw-deprecation --trace-warnings" npm test && NODE_OPTIONS="--throw-deprecation --trace-warnings" npm run lint && NODE_OPTIONS="--throw-deprecation --trace-warnings" npm run build
```

Expected: PASS, no warnings.

**Step 3: Run security/workflow checks**

Run:

```bash
cd backend && python -m pytest tests/test_release_governance.py -q
python3 scripts/check_compose_logs.py --help
git diff --check
```

Expected: PASS.

**Step 4: Subagent reviews**

- Spec reviewer: verify every #118/#135~#139 acceptance-relevant point is covered or explicitly deferred with blocker evidence.
- Code-quality reviewer: verify workflow security, action pinning, no PR-head execution in privileged workflows, no duplicate check regressions, no library downgrade.

---

### Task 11: Commit, push, Draft PR, evidence, and gates

**Files:**
- All intentional changes.

**Step 1: Inspect diff before commit**

Run:

```bash
git status --short --branch
git diff --stat
git diff --check
```

**Step 2: Commit**

Use a Korean/English conventional summary, e.g.:

```bash
git add <intentional files only>
git commit -m "feat: establish release governance gates"
```

**Step 3: Push and PR continuity**

Run:

```bash
git push -u origin release/deployment-ci-governance-20260511
```

Create or update Draft PR in Korean. The body must include:

- #118, #135, #136, #137, #138, #139 references.
- current head SHA.
- local verification evidence.
- security alerts before/after evidence.
- GHCR release behavior and deferred tag evidence.
- external blocker if org ruleset still requires human approval.

**Step 4: PR gates**

Run:

```bash
gh pr checks <new-pr>
gh pr view <new-pr> --json mergeStateStatus,mergeable,isDraft,reviewDecision,statusCheckRollup
gh api /repos/Seongho-Bae/naruon/code-scanning/alerts?state=open
gh api /repos/Seongho-Bae/naruon/dependabot/alerts?state=open
```

**Step 5: Merge/deploy follow-through**

- Do not merge without current-head required checks and CodeRabbit/robot-review evidence.
- If `mergeStateStatus=BEHIND`, run `gh pr update-branch`, then re-run gates.
- If only org ruleset `14316398` human-review requirement blocks merge, record it as #128 external policy blocker and do not wait for a human review by default.
- After merge/tag, verify release/GHCR/tag/deploy evidence and update #129/#130.
