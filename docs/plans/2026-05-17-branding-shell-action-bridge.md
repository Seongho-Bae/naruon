# Branding Shell Action Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make desktop header actions and the mobile AI quick-action sheet execute against the selected email instead of only opening informational popovers.

**Architecture:** Keep `DashboardLayout` as the shell event source using `naruon:header-action`. Add a page-level bridge in `frontend/src/app/page.tsx` that validates selected-email context, forwards commands to `EmailDetail`, and shows Korean guidance when no email is selected. Extend `EmailDetail` with a small action-command prop that reuses the existing draft, calendar sync, and action-item UI paths.

**Tech Stack:** Next.js 16 app router, React 19 client components, Vitest/jsdom unit tests, Playwright E2E, existing API client endpoints.

---

## Source Gap

- `docs/plans/2026-05-16-branding-roadmap-next-gaps.md` marked header primary actions as implemented visually, but the runtime only dispatched `naruon:header-action` events.
- `frontend/src/components/DashboardLayout.tsx` emitted `reply-draft`, `calendar-sync`, and `create-task` events from desktop and mobile controls.
- No runtime listener consumed those events, so users could press real-looking action buttons without any selected-email behavior.

## Files

- Modify: `frontend/src/app/page.test.tsx`
- Modify: `frontend/src/components/EmailDetail.test.tsx`
- Modify: `frontend/tests/e2e/dashboard-branding.spec.ts`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/components/EmailDetail.tsx`
- Modify: `docs/plans/2026-05-16-branding-roadmap-next-gaps.md`

## Task 1: Page-level shell action bridge

- [x] **Step 1: Write failing unit tests**

Create `frontend/src/app/page.test.tsx` to assert that dispatching `naruon:header-action` without a selected email shows `먼저 메일을 선택하세요.` and dispatching after email selection forwards the action to `EmailDetail`.

- [x] **Step 2: Verify RED**

Run:

```bash
npm test -- src/app/page.test.tsx src/components/EmailDetail.test.tsx
```

Expected and observed before implementation: FAIL because no page-level listener forwarded shell actions or showed selected-email guidance.

- [x] **Step 3: Implement bridge**

Add `workspaceActionNotice` and `detailActionCommand` state in `frontend/src/app/page.tsx`, listen for `naruon:header-action`, require a selected email, and pass `{ id, action }` to every rendered `EmailDetail` instance.

- [x] **Step 4: Verify GREEN**

Run:

```bash
npm test -- src/app/page.test.tsx src/components/EmailDetail.test.tsx
```

Expected and observed after implementation: PASS.

## Task 2: EmailDetail command execution

- [x] **Step 1: Write failing unit test**

Add an `EmailDetail` test that renders a selected email with `actionCommand={{ id: 1, action: "reply-draft" }}` and expects `/api/llm/draft` to run and the `답장 초안` textarea to receive the draft.

- [x] **Step 2: Verify RED**

Run:

```bash
npm test -- src/components/EmailDetail.test.tsx
```

Expected and observed before implementation: FAIL because `EmailDetail` did not accept or execute external commands.

- [x] **Step 3: Implement command execution**

Extend `EmailDetail` with an optional `actionCommand` prop, reuse the existing reply draft and calendar sync handlers, consume each command id only once, and add truthful task-creation status copy for `create-task`.

- [x] **Step 4: Verify GREEN**

Run:

```bash
npm test -- src/app/page.test.tsx src/components/EmailDetail.test.tsx
```

Expected and observed after implementation: PASS.

## Task 3: Shell acceptance proof

- [x] **Step 1: Add acceptance assertions**

Keep `frontend/tests/e2e/dashboard-branding.spec.ts` focused on branded shell/nav acceptance and use the new `frontend/src/app/page.test.tsx` and `frontend/src/components/EmailDetail.test.tsx` coverage for selected-email command execution, duplicate-pane suppression, and stale mobile command replay prevention.

- [x] **Step 2: Final verification**

Run:

```bash
npm run lint
npm run typecheck
npm test -- src/app/page.test.tsx src/components/EmailDetail.test.tsx src/components/DashboardLayout.test.tsx src/components/EmailList.test.tsx
LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts
```

Expected: PASS, then commit and push this bridge as the next PR #202 update.

Observed on 2026-05-17 from `frontend/`:

- `npm run lint` — PASS after moving command-triggered state changes out of the synchronous effect body.
- `npm run typecheck` — PASS.
- `npm test -- src/app/page.test.tsx src/components/EmailDetail.test.tsx src/components/DashboardLayout.test.tsx src/components/EmailList.test.tsx` — PASS.
- `LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts` — PASS for shell/nav acceptance; selected-email command execution is covered by the new unit tests because the existing live E2E harness does not currently hydrate/fetch the inbox list reliably enough to select an email.

Review follow-up: the page bridge now separates desktop and mobile command state so one shell click cannot execute in both mounted detail panes, clears stale mobile commands when returning to the inbox or selecting a new email, and `EmailDetail` tracks the last consumed command id per selected email to prevent replay when callback dependencies change. Command reset, same-email reselect, empty-todo feedback, todo-data waits, and late async draft/calendar responses are covered by regression tests.
