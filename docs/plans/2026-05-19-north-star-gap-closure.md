# North-star Gap Closure Slice

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the highest-signal gaps discovered after comparing
`docs/plans/`, `frontend/branding/`, current frontend implementation, and PR
automation behavior.

**Architecture:** Keep Naruon's visible IA honest while preserving the platform
contracts: Naruon is a relay/proxy web client and AI workspace, customer systems
remain source-of-truth, private-network access is outbound-only through a
connector, and PR governance is metadata-only.

## Completed tasks

- [x] Desktop startup chooser: `DashboardLayout` now exposes a desktop/tablet
  `시작 화면` control for `대시보드`, `이메일`, and `일정` in addition to the
  mobile hamburger selector.
- [x] Detail action parity: `EmailDetail` now provides a visible `할 일 만들기`
  action in the `실행 항목` card instead of requiring only shell commands.
- [x] Responsive/mobile safety: mobile quick actions are viewport-bounded and
  scrollable; inbox/detail/search/calendar/action panels have safe bottom padding
  so the fixed bottom nav does not cover final content.
- [x] Playwright evidence: mobile selected-email detail now proves subject,
  summary, execution heading, and task creation status after selecting a real
  inbox item.
- [x] Brittle copy reduction: branding checks assert structural brand surfaces and
  local assets rather than a fixed slogan string.
- [x] Destination detail surfaces: Calendar, Tasks, Search, Data, Security,
  Projects, AI Hub, and Settings now have route-smoke coverage and the new
  pages expose actionable work states instead of inert placeholder copy.
- [x] PR governance hardening: `.github/workflows/pr-governance.yml` listens for
  the exact `Strix Security Scan` workflow, runs a trusted-base governance script,
  separates pending/waiting states from failures, and updates an idempotent marker
  comment instead of posting duplicates.
- [x] Strix GPT-5 hardening: the workflow keeps GPT-5.4-or-newer as the model
  requirement and uses only an explicitly named `STRIX_OPENAI_API_KEY` OpenAI
  Platform credential. It fails closed instead of routing scanner traffic
  through GitHub Models, `github.token`, Gemini, GPT-4o, or GPT-4.1.

## Verification evidence

- RED unit tests failed before implementation for missing desktop startup controls
  and missing visible detail task action.
- GREEN unit evidence:

  ```bash
  npm test -- \
    src/components/DashboardLayout.test.tsx \
    src/components/EmailDetail.test.tsx \
    src/app/page.test.tsx \
    src/components/EmailList.test.tsx
  ```

- PR governance RED: `bash scripts/ci/test_pr_governance_gate.sh` failed while
  `scripts/ci/pr_governance_gate.sh` was absent.
- PR governance GREEN:

  ```bash
  python3 -m pytest backend/tests/test_release_governance.py -q
  bash scripts/ci/test_pr_governance_gate.sh
  ```

- Responsive GREEN:

  ```bash
  LIVE_BASE_URL=http://127.0.0.1:18081 \
    npm run test:e2e -- dashboard-branding.spec.ts dashboard-flows.spec.ts
  ```

- Destination detail GREEN:

  ```bash
  npm test -- \
    src/app/calendar/page.test.tsx \
    src/app/tasks/page.test.tsx \
    src/app/search/page.test.tsx \
    src/app/projects/page.test.tsx \
    src/app/data/page.test.tsx \
    src/app/security/page.test.tsx \
    src/components/DashboardLayout.test.tsx
  LIVE_BASE_URL=http://127.0.0.1:18081 \
    npx playwright test tests/e2e/dashboard-branding.spec.ts --project=desktop
  ```

## Remaining north-star work

- Implement production connector bootstrap artifacts beyond the manifest.
- Replace the HMAC bridge with a verified OIDC provider integration while keeping
  signed, server-verifiable session claims.
- Implement provider writes for CalDAV/CardDAV/WebDAV with ETag/If-Match conflict
  handling and source-level audit trails.
- Add OpenTelemetry instrumentation and dashboards for connector heartbeat, sync
  lag, provider throttling, writeback conflicts, and AI action audit events.

## Follow-up slice evidence

- `EmailDetail` calendar actions now request `/api/calendar/writeback-intent` for
  extracted execution items instead of the legacy `/api/calendar/sync` path, and
  the UI reports the selected customer-owned source provenance as an intent
  request rather than claiming provider write completion.
- Frontend unit and E2E mocks assert that the mail-detail calendar action does
  not call `/api/calendar/sync`, keeping the source-of-truth/writeback boundary
  from regressing through copied fixtures.
