# Startup View, Responsive Scroll, and Mobile Menu Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users choose whether Naruon opens to dashboard, email, or calendar while proving the branded shell works across desktop/tablet/mobile resolutions, scroll states, and the mobile hamburger menu.

**Architecture:** Add a small client-side workspace preference store backed by `localStorage`, keep URL hash overrides for mobile deep links, and surface the preference in the mobile hamburger menu. Extend unit and Playwright coverage before implementation so startup routing, short-height scroll, and hamburger composition are verified against the branding plans.

**Tech Stack:** Next.js 16 app router, React 19 client components, TypeScript, Vitest/jsdom, Playwright, local Naruon brand assets.

---

## Source Gap

- `docs/plans/2026-05-11-frontend-brand-redesign-design.md` requires desktop, tablet, and mobile browser assertions, no hover-only mobile controls, and obvious paths between inbox, detail, and execution actions.
- `docs/plans/2026-05-16-branding-roadmap-next-gaps.md` still tracks tablet and mobile calendar/search behavior gaps.
- Current `frontend/src/app/page.tsx` always opens the email workspace on desktop and defaults mobile to inbox unless the hash says otherwise.
- Current `frontend/src/components/DashboardLayout.tsx` hamburger only lists mail sections, so mobile users cannot reach dashboard, settings, calendar, or help/profile affordances from the menu.

## Files

- Create: `frontend/src/lib/workspace-preferences.ts`
- Modify: `frontend/src/lib/mobile-workspace.ts`
- Modify: `frontend/src/app/page.test.tsx`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/components/DashboardLayout.test.tsx`
- Modify: `frontend/src/components/DashboardLayout.tsx`
- Scope note: a settings-page startup selector was initially considered but deliberately left out of this PR so pre-existing sensitive settings API code is not pulled into the changed-file security scan scope.
- Modify: `frontend/tests/e2e/dashboard-branding.spec.ts`

## Task 1: Startup view preference store and page behavior

- [x] **Step 1: Write failing unit tests**

Update `frontend/src/app/page.test.tsx` with tests that seed `localStorage.setItem('naruon_startup_view', 'calendar')` and expect the mobile calendar region to be the active startup panel, seed `dashboard` and expect a dashboard overview region, and verify the default remains the email workspace.

- [x] **Step 2: Verify RED**

Run from `frontend/`:

```bash
npm test -- src/app/page.test.tsx
```

Expected: FAIL because no startup preference store exists and no dashboard overview startup panel is rendered.

Observed on 2026-05-17: FAIL in `src/app/page.test.tsx` because `오늘의 실행 대시보드` was not rendered from a saved startup preference.

- [x] **Step 3: Implement minimal preference behavior**

Create `workspace-preferences.ts` with `WorkspaceStartupView = 'dashboard' | 'email' | 'calendar'`, `getWorkspaceStartupView()`, `setWorkspaceStartupView(view)`, `subscribeWorkspaceStartupView(listener)`, and `useWorkspaceStartupView()`. In `page.tsx`, use the preference to select the initial desktop/mobile content while preserving `#mobile-*` hash overrides.

- [x] **Step 4: Verify GREEN**

Run:

```bash
npm test -- src/app/page.test.tsx
```

Expected: PASS.

Observed on 2026-05-17: PASS in focused `src/app/page.test.tsx` coverage.

## Task 2: User-facing startup selector

- [x] **Step 1: Write failing UI tests**

Update `DashboardLayout.test.tsx` or a focused settings test to assert a `시작 화면` control exposes options `대시보드`, `이메일`, and `일정`, and selecting `일정` persists `naruon_startup_view=calendar`.

- [x] **Step 2: Verify RED**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx src/app/page.test.tsx
```

Expected: FAIL until a selector is wired.

Observed on 2026-05-17: FAIL in `src/components/DashboardLayout.test.tsx` because the hamburger menu did not expose `시작 화면` controls.

- [x] **Step 3: Implement selector**

Add a compact `시작 화면` selector to the mobile hamburger menu. Keep Korean labels explicit: `대시보드`, `이메일`, `일정`. Dispatch `naruon:startup-view-change` so mounted pages update without refresh.

- [x] **Step 4: Verify GREEN**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx src/app/page.test.tsx
```

Expected: PASS.

Observed on 2026-05-17: PASS after adding the hamburger startup selector. The settings-page selector was scope-cut before landing to keep unrelated settings API code out of this PR's security-scan diff.

## Task 3: Hamburger menu composition and close behavior

- [x] **Step 1: Write failing hamburger assertions**

Update `DashboardLayout.test.tsx` to open `Open workspace menu` and assert the menu contains grouped sections for `시작 화면`, `메일`, `워크스페이스`, and `도움`, includes real links to `/settings`, `#mobile-inbox`, `#mobile-calendar`, and disabled future routes with `준비 중`, then closes when a real menu action is selected.

- [x] **Step 2: Verify RED**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx
```

Expected: FAIL because the hamburger currently renders only mail items.

Observed on 2026-05-17: FAIL because the hamburger menu only contained mail sections.

- [x] **Step 3: Implement composition**

Expand the hamburger menu model so mobile users can reach mail, calendar, settings, help/profile placeholders, and startup view choices without relying on the bottom nav. Keep unavailable routes disabled rather than 404 links.

- [x] **Step 4: Verify GREEN**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx
```

Expected: PASS.

Observed on 2026-05-17: PASS in `src/components/DashboardLayout.test.tsx`.

## Task 4: Responsive and scroll Playwright acceptance

- [x] **Step 1: Write failing E2E assertions**

Update `frontend/tests/e2e/dashboard-branding.spec.ts` to cover viewport matrix `390x844`, `390x640`, `768x1024`, `1024x768`, `1280x1024`, and `1920x1080`; assert `document.documentElement.scrollWidth <= document.documentElement.clientWidth`; assert mobile calendar/search/actions panels can scroll to their last card without bottom nav covering it; assert hamburger menu composition is visible and closes on selection.

- [x] **Step 2: Verify RED**

Run with the existing local server harness:

```bash
LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts
```

Expected: FAIL until scroll regions and hamburger composition are fixed.

Observed on 2026-05-17: FAIL first on hamburger/menu assertions and scroll/menu composition checks before fixes.

- [x] **Step 3: Implement scroll fixes**

Make mobile non-inbox panels use `min-h-0 overflow-y-auto pb-28`, keep desktop/sidebar scroll independent, and ensure bottom navigation does not obscure final content on short screens.

- [x] **Step 4: Final verification**

Run:

```bash
npm run lint
npm run typecheck
npm test -- src/app/page.test.tsx src/components/DashboardLayout.test.tsx src/components/EmailDetail.test.tsx src/components/EmailList.test.tsx
LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts
```

Expected: PASS, then review, commit, push, and run PR continuity for PR #202.

Observed on 2026-05-17 from `frontend/`:

- `npm run lint` — PASS.
- `npm run typecheck` — PASS.
- `npm test -- src/app/page.test.tsx src/app/layout.test.tsx src/components/EmailDetail.test.tsx src/components/DashboardLayout.test.tsx src/components/EmailList.test.tsx` — PASS, 19 tests, including saved-dashboard plus `#mobile-calendar` hash override.
- `LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts` — PASS, 11 tests across desktop/tablet/mobile/short-mobile viewports with search and calendar scroll coverage.

## Acceptance Criteria

- Users can choose `대시보드`, `이메일`, or `일정` as the startup surface.
- Preference survives reload through local storage and updates mounted UI through a browser event.
- Mobile hash links continue to override startup preference for deep links.
- Hamburger menu has a defensible composition: startup selector, mail routes, workspace views, settings/help/profile affordances, and disabled future routes.
- Playwright covers desktop, tablet, normal mobile, and short mobile heights with horizontal-overflow and scroll assertions.
