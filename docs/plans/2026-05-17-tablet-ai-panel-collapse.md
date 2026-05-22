# Tablet AI Panel Collapse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the remaining P1 branding roadmap gap by collapsing the right AI/context panel into a tablet-friendly drawer/tab surface at 1024–1279px while preserving search, primary actions, scrolling, and mobile hamburger guarantees.

**Architecture:** Keep the existing three-panel desktop workspace for `xl` and wider screens. Add a dedicated `lg:max-xl` tablet workspace that renders the inbox and detail side-by-side, with the graph/context surface inside a collapsible `details` disclosure labelled `태블릿 맥락 패널`; keep mobile below 1024px unchanged.

**Tech Stack:** Next.js 16 app router, React 19 client components, Tailwind CSS responsive utilities, Vitest/jsdom, Playwright.

---

## Source Gap

- `docs/plans/2026-05-11-frontend-brand-redesign-design.md` requires tablet behavior around 1024–1279px where the right AI panel collapses into detail tabs or a drawer while search and primary actions remain usable.
- `docs/plans/2026-05-16-branding-roadmap-next-gaps.md` still lists **P1 — Tablet AI panel behavior** as unimplemented.
- `frontend/src/app/page.tsx` currently switches from mobile directly to the three-panel desktop layout at `lg`/1024px, so tablet landscape gets the cramped right graph panel instead of a collapsed context surface.

## Files

- Modify: `frontend/tests/e2e/dashboard-branding.spec.ts`
- Modify: `frontend/src/app/page.test.tsx`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/components/DashboardLayout.test.tsx`
- Modify: `frontend/src/components/DashboardLayout.tsx`

## Task 1: Prove tablet uses collapsed context instead of desktop right rail

- [x] **Step 1: Write failing Playwright assertions**

  In `frontend/tests/e2e/dashboard-branding.spec.ts`, add a `1024x768` assertion that `태블릿 메일 작업공간` is visible, `태블릿 맥락 패널` is visible, and the desktop three-panel region is hidden. Also assert the header action buttons remain visible at tablet width.

- [x] **Step 2: Verify RED**

  Run from `frontend/`:

  ```bash
  LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts
  ```

  Expected: FAIL because 1024px currently renders `데스크톱 메일 작업공간` and hides header action buttons until `xl`.

  Observed on 2026-05-17: FAIL because `태블릿 메일 작업공간` was not found at `1024x768`.

- [x] **Step 3: Add unit composition coverage**

  In `frontend/src/app/page.test.tsx`, assert the home composition contains both `태블릿 메일 작업공간` and the `태블릿 맥락 패널` disclosure, so the responsive surface has regression coverage even without layout evaluation in jsdom.

- [x] **Step 4: Verify RED**

  Run:

  ```bash
  npm test -- src/app/page.test.tsx
  ```

  Expected: FAIL because the tablet region does not exist.

  Observed on 2026-05-17: FAIL because `[aria-label="태블릿 메일 작업공간"]` was not rendered and the header action group was still `xl`-scoped.

## Task 2: Implement the tablet workspace and header action preservation

- [x] **Step 1: Add tablet workspace markup**

  In `frontend/src/app/page.tsx`, keep the existing desktop `ResizablePanelGroup` but change it to `xl:flex`. Add a sibling tablet region with `aria-label="태블릿 메일 작업공간"` and classes `hidden lg:flex xl:hidden`. Render `EmailList`, `EmailDetail`, and a collapsed `<details>` context panel with `summary` text `태블릿 맥락 패널` and the existing `NetworkGraph` inside.

- [x] **Step 2: Preserve primary actions at tablet width**

  In `frontend/src/components/DashboardLayout.tsx`, render header action buttons from `lg` upward instead of waiting for `xl`. Use wrapping/flex constraints so the buttons remain reachable without horizontal overflow at 1024px.

- [x] **Step 3: Verify GREEN**

  Run:

  ```bash
  npm test -- src/app/page.test.tsx src/components/DashboardLayout.test.tsx
  LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts
  ```

  Expected: PASS, including tablet overflow checks and visible tablet header action buttons.

  Observed on 2026-05-17: PASS for focused unit tests and focused tablet E2E. A first GREEN attempt exposed that `ResizablePanelGroup`'s base `flex` class overrode `hidden`; the desktop region now uses an outer responsive wrapper so it is actually hidden on tablet.

## Task 3: Final verification and delivery

- [x] Run from `frontend/`:

  ```bash
  npm run lint
  npm run typecheck
  npm test -- src/app/page.test.tsx src/app/layout.test.tsx src/components/EmailDetail.test.tsx src/components/DashboardLayout.test.tsx src/components/EmailList.test.tsx src/lib/workspace-preferences.test.ts
  LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts
  ```

- [x] Capture tablet/mobile screenshots and inspect them before claiming visual readiness.
- [ ] Commit intentional files only, push `feature/branding-mobile-action-workspace`, run PR continuity, request current-head CodeRabbit review, and keep PR #202 auto-merge enabled without stopping on pending checks.

Observed on 2026-05-17 from `frontend/`:

- `npm run lint` — PASS.
- `npm run typecheck` — PASS.
- `npm test -- src/app/page.test.tsx src/app/layout.test.tsx src/components/EmailDetail.test.tsx src/components/DashboardLayout.test.tsx src/components/EmailList.test.tsx src/lib/workspace-preferences.test.ts` — PASS, 25 tests.
- `LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts` — PASS, 11 tests.
- Screenshot inspection: `tablet-1024-branding-fixed.png` shows the `태블릿 메일 작업공간` two-column layout with a collapsed context panel instead of a cramped right rail. `mobile-390-menu-fixed.png` shows the hamburger menu spans the mobile viewport width after fixing the popover width regression found during screenshot review.
- Dev-server screenshot console noise was limited to Next HMR WebSocket handshake retries in the manual Playwright session; test runs passed without app-level failures.

Review follow-up: independent review found command replay and hidden-detail duplicate fetch risks across desktop, tablet, and mobile viewport transitions. Fixed by tagging shell commands with layout target plus viewport mode version, making viewport state hydration-stable with a mounted readiness gate, conditionally mounting only the active `EmailDetail`, and adding desktop/tablet/mobile replay plus hidden mobile-detail remount regression tests. Final subagent review returned PASS with no critical/important findings.
