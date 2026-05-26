# Branding Menu and Task Tracking Gap Closure Implementation Plan

<!-- markdownlint-disable MD013 -->

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the highest-risk gap between `docs/plans/`, `frontend/branding/`, and the current product by turning the branded shell into a durable Today/Inbox/Calendar/Task workspace with ticket-like tracking and safe PR automation.

**Architecture:** Keep Naruon as a web client/control plane, not a mail server. External IMAP/POP3/SMTP/OAuth, CalDAV/CardDAV, and WebDAV systems remain the source of truth; Naruon stores bounded metadata, AI extraction provenance, task state, and writeback intent. The first implementation slice persists email-derived tasks and upgrades the responsive shell/menu contract while leaving full connector/provider write execution for later connector slices.

**Tech Stack:** FastAPI, SQLAlchemy async models, Next.js app routes, Vitest/JSDOM, Playwright, GitHub Actions, CodeRabbit current-head review evidence.

---

## Audit evidence

| Area | Evidence | Status | First implementation action |
| --- | --- | --- | --- |
| Startup choice | `frontend/src/lib/workspace-preferences.ts` supports `dashboard \| email \| calendar` and first-run sessions open the dashboard. | Implemented | Preserve explicit user overrides and keep screenshot evidence current. |
| Branding menu IA | `frontend/branding/uiux/*.png` show full workspace IA; `DashboardLayout.tsx` exposes desktop and tablet/mobile destinations with live mail folder links. | Implemented | Keep desktop primary nav and tablet/mobile drawer destinations synchronized. |
| Ticket-like work tracking | `/tasks` reads `/api/tasks` and displays source-linked ticket status, priority, email, and thread provenance. | Implemented | Continue expanding persistence/writeback evidence in DB-affecting slices. |
| Sent-mail reply tracking | `/api/emails/pending-replies` uses the authenticated user's configured mail addresses, owner scope, reply-intent detection, and later external-reply checks. | Implemented | Provider-side sent-folder sync and durable notification scheduling remain connector slices. |
| CalDAV/WebDAV source of truth | `docs/plans/2026-05-18-calendar-writeback-sovereignty.md` and `ARCHITECTURE.md` require source records/ETag/writeback. | Partial | Keep writeback design documented here, but do not fake provider writes in this slice. |
| Private-network mail | `docs/plans/2026-05-18-self-hosted-connector-bootstrap.md` requires outbound connector design. | Partial | Document that GitHub self-hosted runner is CI smoke only; production connector remains outbound-only. |
| PR automation | `scripts/ci/pr_governance_gate.sh` treats missing CodeRabbit evidence as a blocker and `STARTUP_FAILURE` as waiting. | Partial | Treat missing robot evidence as wait-state and startup failure as terminal blocker. |
| Responsive evidence | `frontend/tests/e2e/dashboard-branding.spec.ts` covers desktop/tablet/mobile viewport, scroll, and hamburger capture evidence. | Implemented | Keep reviewing generated screenshots, not only pass/fail output. |

## 2026-05-26 verification update

- Startup selection is now treated as implemented: first-run sessions open the
  dashboard while explicit dashboard/email/calendar choices are preserved.
- Mail drawer items that were previously dead controls now link to `/mail`
  folder states, and Help/Profile route to Settings anchors.
- `/tasks` keeps the ticket-like board surface and reads `/api/tasks` so source
  email/thread provenance appears in the workspace.
- Sent-mail reply tracking is now calculated from customer-owned mailbox
  metadata: self-sent notes are excluded from pending replies, answered threads
  are excluded, and `/api/emails` exposes `requires_reply`/`is_self_sent` for
  the UI badges.
- POP3 credential onboarding now matches SMTP/IMAP shape in tenant config:
  nullable `pop3_username` and encrypted `pop3_password` are accepted, masked,
  and bootstrapped for existing databases.
- Self-sent knowledge capture now creates idempotent, source-linked ticket tasks
  only after proving a true self-to-self message from a tenant-owned address; it
  preserves email/thread provenance, stores plain-text titles, and skips raw
  payloads without a source email row.
- The remaining connector/writeback items stay as explicit future episodes:
  real CalDAV/WebDAV mutation, full POP3 message import/runtime sync, durable
  reply-tracking notifications, WebDAV/Notes materialization of self-sent
  knowledge, and source-id filtered sender DAG views.

## Task 1: Governance wait-state correction

**Files:**

- Modify: `scripts/ci/test_pr_governance_gate.sh`
- Modify: `scripts/ci/pr_governance_gate.sh`

- [ ] **Step 1: Write failing tests**

Add scenarios in the fake `gh` command:

```bash
missing_coderabbit)
  printf '{"check_runs":[]}'
  ;;
startup_failure)
  printf '[{"name":"Application CI","state":"STARTUP_FAILURE","link":"https://checks/app-ci"}]'
  ;;
```

Add assertions:

```bash
assert_missing_coderabbit_waits_without_hard_comment
assert_startup_failure_creates_marker_comment
```

- [ ] **Step 2: Verify RED**

Run:

```bash
bash scripts/ci/test_pr_governance_gate.sh
```

Expected: missing CodeRabbit scenario posts a blocker and startup failure does not.

- [ ] **Step 3: Implement GREEN**

Change `pr_governance_gate.sh` so absent CodeRabbit check-runs call `add_waiting`, while `STARTUP_FAILURE` moves from waiting state to blocker state.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
bash scripts/ci/test_pr_governance_gate.sh
```

Expected: `test_pr_governance_gate: PASS`.

## Task 2: Ticket-like task persistence

**Files:**

- Modify: `backend/db/models.py`
- Create: `backend/api/tasks.py`
- Modify: `backend/main.py`
- Create: `backend/tests/test_tasks_api.py`
- Modify: `frontend/src/components/EmailDetail.tsx`
- Modify: `frontend/src/components/EmailDetail.test.tsx`

- [ ] **Step 1: Write failing backend tests**

Create tests proving that `/api/tasks/from-email` creates one task per execution item, scopes rows to the authenticated owner/organization, stores the source email FK internally, exposes source message/thread provenance, and exposes ticket fields: `status`, `priority`, `source_type`, `title`, `created_at`, `updated_at`.

- [ ] **Step 2: Verify RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 pytest tests/test_tasks_api.py -q
```

Expected: import/route/model errors because the task API does not exist yet.

- [ ] **Step 3: Implement backend GREEN**

Add `TicketTask` model and API. The request body is:

Use two-word `snake_case` database columns for the new table: `task_id`,
`task_uid`, `task_title`, `status_code`, `priority_code`, `source_type`,
`email_id`, `thread_id`, `created_at`, and `updated_at`. Keep `task_id` and
`email_id` private to the database; public API responses expose `task_uid` as
`id` and the source message id as `source_email_id`.

```json
{
  "source_email_id": "<message-14@example.com>",
  "thread_id": "thread-123",
  "items": ["담당자 확인", "일정 공유"]
}
```

The response is:

```json
{
  "created": 2,
  "tasks": [
    {"id": "9f2e2a1a4c7d4e8ab7b2d3c4f5a6b7c8", "title": "담당자 확인", "status": "open", "priority": "normal"}
  ]
}
```

Fail closed with 422 for empty items or HTML-like/script-like task titles at the
backend ingestion boundary. Invalid markup returns
`{"detail":"Execution items must be plain text"}`. Return 404 only when the
`source_email_id` does not belong to the authenticated owner.

- [ ] **Step 4: Write failing frontend test**

Update `EmailDetail.test.tsx` so “할 일 만들기” expects a POST to `/api/tasks/from-email` and displays the created ticket count from the server response.

- [ ] **Step 5: Implement frontend GREEN**

Call the new API from `handleCreateTask`. Keep the source email/thread link in the payload. Show error state if task creation fails.

- [ ] **Step 6: Verify task slice**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 pytest tests/test_tasks_api.py -q
npm test -- src/components/EmailDetail.test.tsx
```

Expected: both commands pass without `Timeout`, `Fatal`, `Warn`, or `Denied` output.

## Task 3: Branding IA and responsive route contract

**Files:**

- Modify: `frontend/src/components/DashboardLayout.tsx`
- Modify: `frontend/src/components/DashboardLayout.test.tsx`
- Modify: `frontend/src/lib/workspace-preferences.ts`
- Modify: `frontend/src/app/page.test.tsx`
- Create: `frontend/src/components/WorkspaceHome.tsx`
- Create: `frontend/src/app/mail/page.tsx`
- Create: `frontend/src/app/search/page.tsx`
- Create: `frontend/src/app/tasks/page.tsx`
- Create: `frontend/src/app/calendar/page.tsx`
- Create: `frontend/src/app/data/page.tsx`
- Create: `frontend/src/app/security/page.tsx`
- Modify: `frontend/playwright.config.ts`
- Modify: `frontend/tests/e2e/dashboard-branding.spec.ts`

- [ ] **Step 1: Write failing tests**

Add tests that require:

1. First-run default startup is dashboard.
2. Mobile/tablet hamburger is a drawer with an overlay, a visible close button, and links for Mail, Calendar, Tasks, Projects, Context Search, AI Hub, Data, Security, and Settings.
3. The mobile drawer closes with its close button and returns `aria-expanded=false`.
4. Playwright projects include mobile, tablet, and desktop.

- [ ] **Step 2: Verify RED**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx src/app/page.test.tsx
```

Expected: tests fail because default startup remains email and drawer links/close button are missing.

- [ ] **Step 3: Implement GREEN**

Centralize navigation data in `DashboardLayout.tsx`, remove fixed dead-space copy blocks that do not drive functionality, convert the mobile/tablet menu into a drawer pattern, extract the workspace home for route reuse, and add lightweight route pages with list/empty/error/action states for mail, context search, calendar, tasks, data, and security.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx src/app/page.test.tsx
npm test -- src/components/EmailDetail.test.tsx
```

Expected: all targeted frontend tests pass.

## Task 4: Documentation sync

**Files:**

- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `ARCHITECTURE.md`

- [ ] **Step 1: Update docs**

Record that Naruon starts as a user-selectable Today/Inbox/Calendar workspace, tasks are ticket-like and source-linked, PR governance treats pending robot evidence as a wait state, self-hosted runners are CI smoke only, and production private-network access is through an outbound connector to `naruon.net`.

- [ ] **Step 2: Verify docs**

Run:

```bash
npx -y markdownlint-cli2@0.17.2 README.md AGENTS.md ARCHITECTURE.md docs/plans/2026-05-19-branding-menu-task-tracking-gap-closure.md
```

Expected: `0 error(s)`.

## Task 5: Screenshot-backed responsive verification

**Files:**

- Modify: `frontend/tests/e2e/dashboard-branding.spec.ts`
- Generated evidence stays untracked unless intentionally documented.

- [ ] **Step 1: Run browser evidence**

Start the local frontend, then capture screenshots at 390x640, 768x1024, 1024x768, 1280x1024, and 1920x1080. Verify:

1. No horizontal overflow.
2. Scroll reaches bottom content above the mobile bottom nav.
3. Mobile drawer menu composition is valid and closes correctly.
4. Dashboard/Inbox/Calendar startup choices all work.

- [ ] **Step 2: Inspect screenshots**

Open the generated PNGs and visually confirm no clipped menu, hidden bottom actions, or excessive dead space. Do not claim success from tests alone.

## Fresh implementation evidence

- Real PostgreSQL smoke: a temporary `pgvector/pgvector:pg16` database bootstrapped with `PYTHONPATH=. python3 scripts/bootstrap_db.py` created `ticket_tasks` with `task_id,task_uid,user_id,organization_id,task_title,status_code,priority_code,source_type,email_id,thread_id,created_at,updated_at`; `/api/tasks/from-email` returned `SMOKE_POST_STATUS 200`, `SMOKE_CREATED 2`, `SMOKE_PUBLIC_ID_LENGTH 32`, and `SMOKE_SOURCE_EMAIL <task-smoke@example.com>`.
- Tenant provenance smoke: `GET /api/tasks` returned `SMOKE_GET_STATUS 200`, `SMOKE_GET_COUNT 3`, and a deliberately cross-tenant source row returned `SMOKE_CROSS_SOURCE None` plus `SMOKE_CROSS_THREAD None`.
- Workspace destination GREEN evidence: unit tests now require Calendar
  month/week/detail/coordination and CalDAV writeback queues, Tasks board/detail
  source links and reply tracking, Search integrated results/detail graph and
  timeline states, Projects decision logs, Data
  repository/ingestion/embedding/quality/WebDAV queues, and Security
  dashboard/access/audit/sharing/policy surfaces. The desktop primary
  nav and mobile drawer destination hrefs are asserted to stay synchronized for
  Home, Mail, Calendar, Tasks, Projects, Context Search, AI Hub, Data, Security,
  and Settings.
- Playwright route evidence: `LIVE_BASE_URL=http://127.0.0.1:18081 npx
  playwright test tests/e2e/dashboard-branding.spec.ts --project=desktop` passed
  29/29 checks covering desktop/tablet/mobile overflow, mobile drawer scrolling,
  route smoke for `/mail`, `/calendar`, `/tasks`, `/data`, `/search`,
  `/security`, `/projects`, `/ai-hub`, and `/settings`, and screenshot capture
  for startup desktop/tablet/mobile plus the mobile drawer.
- Calendar action follow-up: `EmailDetail` now requests
  `/api/calendar/writeback-intent` and no longer calls `/api/calendar/sync` from
  the browser action path. The user-facing status says a customer-owned source
  intent was requested, not that the provider calendar write has completed.

## North-star work deliberately deferred from this slice

- Real CalDAV/CardDAV/WebDAV provider clients and write execution.
- Real private-network connector artifact beyond runner manifest.
- Full Keycloak/Casdoor OIDC validation and Traefik production edge config.
- Source-scoped `MailboxAccount` migration for multi-account duplicate threading.
- Persistent WebDAV project folders and AI-organized file writeback.

These remain explicit roadmap items because pretending they are done would violate the source-of-truth and data-sovereignty contract.
