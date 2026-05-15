# Naruon Foundation Remediation Implementation Plan

<!-- markdownlint-disable MD013 MD036 -->
<!-- Plan keeps copy/paste commands, long requirements, and step labels. -->

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the immediate UI, mobile scroll, route discoverability, and RBAC leakage gaps found while preserving the larger OIDC/synthetic-mailbox roadmap as staged epics.

**Architecture:** Keep this slice small and safety-first. Frontend changes repair the existing Next.js shell and mobile affordances without inventing unavailable product data. Backend changes enforce authenticated user/org scoping on calendar, network, and prompt/provider paths before UI polish claims those surfaces are safe.

**Tech Stack:** Next.js App Router, React 19, Tailwind CSS, Vitest, Playwright, FastAPI, SQLAlchemy, pytest, PyJWT/JWKS auth context.

---

## Task 1: Restore route discoverability and header search honesty

**Files:**

- Modify: `frontend/src/components/DashboardLayout.tsx`
- Modify: `frontend/src/components/DashboardLayout.test.tsx`
- Modify: `frontend/tests/e2e/dashboard-branding.spec.ts`

**Step 1: Write failing tests**

Add assertions that desktop navigation exposes `설정` and `프롬프트 스튜디오`, mobile drawer exposes compose/starred/sent/drafts/all/projects/labels/settings, mobile settings uses a settings icon label, and header search submit navigates to `/ai-hub/context?q=<term>`.

**Step 2: Run test to verify failure**

Run: `cd frontend && npx vitest run src/components/DashboardLayout.test.tsx`
Expected: FAIL because the links and search submit are not wired yet.

**Step 3: Implement minimal code**

- Add `Settings` icon import.
- Add desktop navigation entries for settings and prompt studio.
- Add an expanded mobile drawer route map while keeping the five-item bottom nav compact.
- Replace the mobile settings icon with `Settings`.
- Wrap header search in a form and route to `/ai-hub/context?q=...`.

**Step 4: Run tests**

Run: `cd frontend && npx vitest run src/components/DashboardLayout.test.tsx`
Expected: PASS.

## Task 2: Fix mobile scroll and non-swipe execution affordances

**Files:**

- Modify: `frontend/src/components/DashboardLayout.tsx`
- Modify: `frontend/src/components/EmailList.tsx`
- Modify: `frontend/src/components/EmailDetail.tsx`
- Modify: `frontend/src/components/EmailList.test.tsx`
- Modify: `frontend/tests/e2e/dashboard-branding.spec.ts`

**Step 1: Write failing tests**

Add tests for visible row fallback buttons: “실행 목록에 추가” and “완료 처리”. Add Playwright checks that mobile last interactive content is above the fixed bottom nav after scrolling.

**Step 2: Run test to verify failure**

Run: `cd frontend && npx vitest run src/components/EmailList.test.tsx`
Expected: FAIL because swipe-only actions have no tap fallback.

**Step 3: Implement minimal code**

- Add `min-h-0` to `ScrollArea` callers.
- Add safe-area-aware bottom padding to the main scroll section and bottom nav.
- Add tap fallback buttons per email row for queue and completion.

**Step 4: Run tests**

Run: `cd frontend && npx vitest run src/components/EmailList.test.tsx && npm run build && npm run lint`
Expected: PASS with zero warnings.

## Task 3: Enforce RBAC on calendar/network/prompt paths

**Files:**

- Modify: `backend/api/calendar.py`
- Modify: `backend/api/network.py`
- Modify: `backend/api/prompts.py`
- Modify: `backend/tests/test_calendar_api.py`
- Modify: `backend/tests/test_network_api.py`
- Modify: `backend/tests/test_prompts_api.py`

**Step 1: Write failing tests**

Add tests that unauthenticated calendar sync is rejected, network graph excludes another user's emails, and prompt test selects only providers scoped to the caller organization.

**Step 2: Run tests to verify failure**

Run: `cd backend && DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_calendar_api.py tests/test_network_api.py tests/test_prompts_api.py -q`
Expected: FAIL on the new negative cases.

**Step 3: Implement minimal code**

- Add `AuthContext` dependency to calendar sync and remove body-token trust.
- Keep calendar sync fail-closed with 503 until server-side per-user Google
  credentials exist; do not translate `AuthContext` claims into Google OAuth
  credentials.
- Filter network graph query by authenticated `Email.user_id`.
- Scope prompt provider lookup by `auth_context.organization_id` and fail closed when no org-scoped provider exists.

**Step 4: Run tests**

Run: same pytest command.
Expected: PASS with zero warnings.

## Task 4: Sync roadmap docs with actual gap inventory

**Files:**

- Modify: `ARCHITECTURE.md`
- Modify: `docs/plans/2026-05-14-synthetic-mailbox-platform-program.md`
- Modify: `docs/plans/2026-05-14-dashboard-rbac-mobile-oidc-remediation.md`

**Step 1: Update docs**

Record the new design/implementation plan, remaining route/screen gaps vs branding, mobile scroll/RBAC findings, and the exact deferred platform epics.
Include the ownerless-email bootstrap guard and the calendar credential-store
gap so docs do not imply legacy data or calendar sync silently keep working.

**Step 2: Verify docs and code together**

Run targeted backend/frontend tests, then full feasible gates:

- `cd backend && DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest -q`
- `cd frontend && npm test && npm run build && npm run lint`
- `cd frontend && npm run test:e2e -- tests/e2e/dashboard-branding.spec.ts`

Expected: PASS with zero warnings or a documented exact blocker.
