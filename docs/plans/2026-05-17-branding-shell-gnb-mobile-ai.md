# Branding Shell GNB and Mobile AI Action Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the next `docs/plans/` + `frontend/branding/` gap by matching the branded desktop global navigation and mobile central AI action affordance while preventing sidebar navigation from sending users to nonexistent routes.

**Architecture:** Keep the existing dashboard shell, sidebar, header action events, and mobile workspace hash contract. Add a desktop top GNB with valid route targets, notification/profile controls, and a mobile 5-slot bottom bar with a central AI action button that opens quick actions. Convert unavailable future sidebar destinations into disabled coming-soon controls so users do not hit 404 routes.

**Tech Stack:** Next.js 16 app router, React 19 client components, Vitest/jsdom unit tests, Playwright acceptance tests, Tailwind utility classes, local Naruon brand assets.

---

## Source Gap

- `frontend/branding/brand_assets/3.png`, `frontend/branding/uiux/uiux3.png`, and `frontend/branding/uiux/uiux4.png` show a desktop top global navigation with primary sections, search, right-side status/actions, notification, settings, and profile affordances.
- `frontend/branding/brand_assets/6.png` and `frontend/branding/uiux/uiux8.png` show a mobile bottom navigation pattern with a prominent central AI/action affordance.
- `docs/plans/2026-05-16-branding-roadmap-next-gaps.md` still tracks dead sidebar route handling as P1 because sidebar links currently point to routes that do not exist.

## Files

- Modify: `frontend/src/components/DashboardLayout.test.tsx`
- Modify: `frontend/tests/e2e/dashboard-branding.spec.ts`
- Modify: `frontend/src/components/DashboardLayout.tsx`

## Task 1: Desktop branded top GNB

- [x] **Step 1: Write failing unit test**

Add expectations in `frontend/src/components/DashboardLayout.test.tsx` for a `Primary workspace navigation` landmark with valid links to `홈`, `AI 허브`, `프롬프트`, and `설정`, plus accessible notification and profile buttons.

- [x] **Step 2: Verify RED**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx
```

Expected: FAIL because the header does not yet render primary GNB/profile controls.

- [x] **Step 3: Implement GNB**

In `frontend/src/components/DashboardLayout.tsx`, add desktop primary nav links for existing routes only and right-side notification/profile buttons with visible Korean labels or `aria-label`s.

- [x] **Step 4: Verify GREEN**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx
```

Expected: PASS.

## Task 2: Mobile central AI action

- [x] **Step 1: Write failing unit and E2E assertions**

Update tests so the mobile bottom navigation exposes a central `AI 빠른 실행` button that opens a quick-action sheet containing `답장 초안`, `할 일 만들기`, and `캘린더 반영`.

- [x] **Step 2: Verify RED**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx
```

Expected: FAIL because there is no central button or quick-action sheet.

- [x] **Step 3: Implement mobile action sheet**

Keep the existing mobile workspace hash links for inbox/search/calendar/more-style navigation and add a centered button that dispatches the same `naruon:header-action` events used by desktop header actions.

- [x] **Step 4: Verify GREEN**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx
npm run test:e2e -- dashboard-branding.spec.ts
```

Expected: PASS.

## Task 3: Sidebar future route safety

- [x] **Step 1: Write failing unit assertion**

Assert that future sidebar items such as `중요 메일`, `맥락 종합`, and `런칭 프로젝트` render as disabled coming-soon buttons instead of links to nonexistent routes.

- [x] **Step 2: Verify RED**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx
```

Expected: FAIL because these items currently render as `<a href="/starred">` etc.

- [x] **Step 3: Implement disabled coming-soon controls**

Extend the nav item model with `available: false` and render disabled buttons with `준비 중` copy for unavailable routes. Keep existing real routes (`/`, `/settings`, `/ai-hub`, `/prompt-studio`) as links.

- [x] **Step 4: Final verification and commit**

Run:

```bash
npm run lint
npm run typecheck
npm test -- src/components/DashboardLayout.test.tsx src/components/EmailList.test.tsx
LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts
```

Expected: PASS, then commit and push the branch for PR continuity.

Observed on 2026-05-17 from `frontend/`:

- `npm run lint` — PASS.
- `npm run typecheck` — PASS.
- `npm test -- src/components/DashboardLayout.test.tsx src/components/EmailList.test.tsx` — PASS.
- `LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts` — PASS.
