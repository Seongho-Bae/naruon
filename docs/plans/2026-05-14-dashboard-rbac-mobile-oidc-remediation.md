# Dashboard RBAC Mobile OIDC Remediation Plan

<!-- markdownlint-disable MD013 MD036 -->
<!-- Plan keeps copy/paste commands, long requirements, and step labels. -->

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the major gaps between the current Naruon app shell and the branding boards by restoring judgment/action surfaces, fixing scroll and mobile navigation regressions, tightening RBAC exposure, and defining the path to a built-in OIDC provider.

**Architecture:** Split the work into two tracks. First, repair the presentational shell and interaction model in the existing Next.js frontend without breaking current email/detail flows. Second, isolate RBAC/data-tenancy/OIDC-provider work as backend-backed epics, because several critical issues require schema changes and dedicated auth/session flows rather than UI-only patches.

**Tech Stack:** Next.js App Router, React 19, Tailwind CSS, FastAPI, SQLAlchemy, PyJWT/JWKS validation, Playwright/Vitest/pytest.

---

## Audit summary captured before implementation

### Remaining work defined

1. Restore branded dashboard composition:
   - top-level judgment/schedule/action summary row
   - right-side context/judgment/action execution rail
   - reduce dead copy blocks in sidebar/header
2. Fix shell and mobile scrolling:
   - long-form pages must scroll
   - mobile menu and bottom nav must not clip or wrap incorrectly
   - preserve sidebar scroll position across navigation
3. Restore missing route surfaces:
   - `/ai-hub/context`
   - `/ai-hub/decisions`
   - `/ai-hub/actions`
   - mobile-accessible equivalents
4. Add touch interactions:
   - swipe email rows left/right into an execution queue / completion flow
5. Reframe “오늘의 인사이트” around email-derived workload signals instead of fake time-tracking claims.
6. Fix frontend RBAC affordances:
   - hide/show the correct admin surfaces
   - surface blocked/allowed states intentionally
7. Plan backend RBAC/data scope hardening:
   - email/search/network tenancy
   - calendar auth
   - prompt sharing scope
8. Plan built-in OIDC provider path:
   - embedded Keycloak or Casdoor
   - internal login / callback / logout / session bootstrap
   - future SCIM/extensible provider federation

### Web gaps found against branding

- Missing dedicated `판단 포인트` surface
- Missing branded right rail composition; graph dominates the third pane
- Multiple dead links in nav
- Sidebar/header dead space dilutes task density
- Missing board-style KPI/action summary row

### Mobile gaps found

- Mobile bottom nav wraps because 5 items are rendered inside `grid-cols-4`
- Mobile AI/action workspace never appears (`showMobileActions = false`)
- No swipe/todo gesture path exists
- Long pages are clipped by hidden overflow in shell containers

### RBAC gaps found

- Critical backend exposure remains in email/search/network/calendar/prompt-sharing areas and requires follow-up backend scope work
- Group-admin capability is still unimplemented
- Built-in OIDC provider/self-login flow does not exist yet; only manual/local bearer-token plumbing exists

## Task 1: Repair the shell, dead-space, and scroll contracts

**Files:**

- Modify: `frontend/src/components/DashboardLayout.tsx`
- Modify: `frontend/src/app/page.tsx`
- Test: `frontend/src/components/DashboardLayout.test.tsx`

**Step 1: Write failing tests**

- Add/extend tests for:
  - sidebar scroll position persistence
  - mobile bottom-nav 5-column layout
  - removal/replacement of dead header/sidebar filler text in favor of actionable density

**Step 2: Run targeted tests to verify failure**
Run: `cd frontend && npx vitest run src/components/DashboardLayout.test.tsx`
Expected: FAIL.

**Step 3: Implement minimal shell fixes**

- Make the main content area scrollable for long pages.
- Preserve sidebar scroll offset on route change.
- Replace dead header chips and sidebar promo blocks with compact, useful state/action blocks.
- Fix bottom-nav geometry for 5 items.

**Step 4: Run tests/build/lint**
Run: `cd frontend && npx vitest run src/components/DashboardLayout.test.tsx && npm run build && npm run lint`
Expected: PASS.

## Task 2: Restore the branded dashboard composition

**Files:**

- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/components/EmailDetail.tsx`
- Create: `frontend/src/components/TodayInsightPanel.tsx`
- Create: `frontend/src/components/ExecutionRail.tsx`
- Test: `frontend/src/components/EmailDetail.test.tsx`

**Step 1: Write failing tests**

- Add tests for the presence of:
  - judgment surface (`판단 포인트`)
  - execution rail summary/actions beyond the graph
  - today-insight concept based on email-derived metrics

**Step 2: Run targeted tests to verify failure**
Run: `cd frontend && npx vitest run src/components/EmailDetail.test.tsx`
Expected: FAIL.

**Step 3: Implement minimal dashboard restoration**

- Add top KPI/action cards aligned with the board.
- Move summary/judgment/actions to a dedicated execution rail.
- Keep the graph as a secondary visual, not the only third-pane content.
- Rework copy so the product emphasizes context/judgment/action rather than “AI” as a primary actor.

**Step 4: Run tests/build/lint**
Run: `cd frontend && npx vitest run src/components/EmailDetail.test.tsx && npm run build && npm run lint`
Expected: PASS.

## Task 3: Restore missing AI hub subroutes and mobile IA

**Files:**

- Modify: `frontend/src/app/ai-hub/page.tsx`
- Create: `frontend/src/app/ai-hub/context/page.tsx`
- Create: `frontend/src/app/ai-hub/decisions/page.tsx`
- Create: `frontend/src/app/ai-hub/actions/page.tsx`
- Modify: `frontend/src/components/DashboardLayout.tsx`
- Test: `frontend/src/app/layout.test.tsx`

**Step 1: Write failing tests**

- Add route/nav assertions for real context/decisions/actions destinations.
- Add mobile-nav/menu assertions for accessible AI workspace paths.

**Step 2: Run targeted tests to verify failure**
Run: `cd frontend && npx vitest run src/app/layout.test.tsx src/components/DashboardLayout.test.tsx`
Expected: FAIL.

**Step 3: Implement minimal IA restoration**

- Back the existing nav links with real pages.
- Make mobile nav and menu expose the same IA without broken wrapping.

**Step 4: Run tests/build/lint**
Run: `cd frontend && npx vitest run src/app/layout.test.tsx src/components/DashboardLayout.test.tsx && npm run build && npm run lint`
Expected: PASS.

## Task 4: Add mobile swipe-to-execution interaction

**Files:**

- Modify: `frontend/src/components/EmailList.tsx`
- Create: `frontend/src/lib/execution-queue.ts`
- Create: `frontend/src/lib/execution-queue.test.ts`
- Create: `frontend/src/lib/email-list-gestures.test.tsx`

**Step 1: Write failing tests**

- Add tests for swipe-right → add to execution queue.
- Add tests for swipe-left → mark queue item done/remove from queue.

**Step 2: Run targeted tests to verify failure**
Run: `cd frontend && npx vitest run src/lib/execution-queue.test.ts src/lib/email-list-gestures.test.tsx`
Expected: FAIL.

**Step 3: Implement minimal gesture flow**

- Add local execution-queue persistence.
- Add pointer/touch gesture handling with visible affordances.
- Keep non-touch click behavior intact.

**Step 4: Run tests/build/lint**
Run: `cd frontend && npx vitest run src/lib/execution-queue.test.ts src/lib/email-list-gestures.test.tsx && npm run build && npm run lint`
Expected: PASS.

## Task 5: Harden frontend RBAC affordances around admin surfaces

**Files:**

- Modify: `frontend/src/app/settings/page.tsx`
- Modify: `frontend/src/lib/api-client.ts`
- Test: `frontend/src/app/settings/page.test.tsx`

**Step 1: Extend failing tests**

- Cover group-admin/member/platform-admin/organization-admin visibility and blocked states.

**Step 2: Run targeted tests to verify failure**
Run: `cd frontend && npx vitest run src/app/settings/page.test.tsx`
Expected: FAIL.

**Step 3: Implement minimal RBAC UI hardening**

- Surface clear “implemented vs unavailable” messaging by role.
- Avoid implying capabilities that the backend still cannot safely grant.

**Step 4: Run tests/build/lint**
Run: `cd frontend && npx vitest run src/app/settings/page.test.tsx && npm run build && npm run lint`
Expected: PASS.

## Task 6: Backend RBAC/data-scope hardening follow-up

**Files:**

- Modify: `backend/db/models.py`
- Modify: `backend/api/emails.py`
- Modify: `backend/api/search.py`
- Modify: `backend/api/network.py`
- Modify: `backend/api/calendar.py`
- Modify: `backend/api/prompts.py`
- Add/modify tests across affected suites

**Notes:**

- This is a separate schema-and-contract epic.
- Must not be mixed casually with frontend-only polish.
- Requires mailbox ownership columns, query filters, and likely migration scripts.

## Task 7: Built-in OIDC provider/self-login epic

**Candidate direction:** embedded Keycloak first, Casdoor as secondary evaluation path.

**Files likely involved:**

- `docker-compose.gateway.yml`
- new auth/login callback endpoints
- frontend login/callback/session bootstrap pages
- docs under `docs/operations/`

**Must cover:**

- built-in OIDC login even without an external provider
- future SCIM/federation extension path
- role/group mapping into `ScopedRoleAssignment`

**Notes:**

- This is larger than the current remediation slice.
- Delivery path should start with architecture/runbook + local stack integration, then real login flow.
