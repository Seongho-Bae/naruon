# AI Hub Functional Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `/ai-hub` from a thin prompt summary page into the branded AI workspace promised by the shell: context synthesis, decision points, and action items.

**Architecture:** Keep the slice frontend-only and reuse existing `/api/prompts` data as the current available signal. Render three functional sections with loading, error, empty, and success states; every empty/error state includes an action so the page does not become dead space.

**Tech Stack:** Next.js 16 app router, React 19 client component, existing `ApiClient`, Vitest/jsdom, Playwright responsive checks.

---

## Source gap

- `frontend/src/components/DashboardLayout.tsx` makes `AI 허브` a primary route.
- `frontend/src/app/ai-hub/page.tsx` currently renders `AI Hub`, `최근 AI 요약`, and `설명 없음`, which does not match the brand roadmap's `맥락 종합 / 판단 포인트 / 실행 항목` promise.
- `docs/plans/2026-05-17-north-star-platform-roadmap.md` selects `/ai-hub` as the first slice because it removes visible dead space without adding a new backend endpoint.

## Files

- Create: `frontend/src/app/ai-hub/page.test.tsx`
- Modify: `frontend/src/app/ai-hub/page.tsx`
- Modify: `frontend/tests/e2e/dashboard-branding.spec.ts`
- Modify: `docs/plans/2026-05-17-north-star-platform-roadmap.md` if implementation changes the chosen first slice.

## Task 1: Prove `/ai-hub` needs real workspace sections

- [x] **Step 1: Write failing unit tests**

  Create `frontend/src/app/ai-hub/page.test.tsx` with tests that assert:

  - Successful prompt data renders `맥락 종합`, `판단 포인트`, `실행 항목`.
  - Generic copy `최근 AI 요약`, `AI Hub`, and `설명 없음` is absent.
  - A pending API request renders `role="status"` with `AI 허브를 불러오는 중입니다.`.
  - A failed API request renders `role="alert"` and a `다시 시도` button.

- [x] **Step 2: Verify RED**

  Run from `frontend/`:

  ```bash
  npm test -- src/app/ai-hub/page.test.tsx
  ```

  Expected: FAIL because the current page has only one summary card and no semantic loading/error roles.

  Observed on 2026-05-17: FAIL because the page still rendered `AI Hub`, had no `맥락 종합 / 판단 포인트 / 실행 항목`, and exposed no `role="status"` or `role="alert"` states.

## Task 2: Implement the functional AI hub surface

- [x] **Step 1: Replace generic AI hub content**

  In `frontend/src/app/ai-hub/page.tsx`:

  - Use title `AI 허브`.
  - Add actions linking to `/`, `/#mobile-search`, and `/prompt-studio`.
  - Render three sections/cards: `맥락 종합`, `판단 포인트`, `실행 항목`.
  - Loading uses `role="status"` and `aria-live="polite"`.
  - Error uses `role="alert"` and a retry button.
  - Empty states include action links, not only text.
  - Success states map existing prompt data into the three sections without showing `설명 없음`.

- [x] **Step 2: Verify GREEN**

  Run:

  ```bash
  npm test -- src/app/ai-hub/page.test.tsx
  ```

  Expected: PASS.

  Observed on 2026-05-17: PASS, 3 AI hub unit tests.

## Task 3: Add responsive/brand E2E coverage

- [x] **Step 1: Extend Playwright branding test**

  In `frontend/tests/e2e/dashboard-branding.spec.ts`, click or navigate to `/ai-hub` and assert the three sections are visible at desktop and mobile widths without horizontal overflow.

- [x] **Step 2: Verify GREEN**

  Run with a fresh local dev server:

  ```bash
  LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts
  ```

  Expected: PASS.

  Observed on 2026-05-17: PASS, 13 Playwright branding tests including mobile and desktop AI hub overflow checks.

## Task 4: Final verification and delivery

- [x] Run from `frontend/`:

  ```bash
  npm run lint
  npm run typecheck
  npm test -- src/app/ai-hub/page.test.tsx src/app/page.test.tsx src/components/DashboardLayout.test.tsx src/components/mobile-workspace-panels.test.tsx
  LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts
  ```

  Observed on 2026-05-17:

  - `npm run lint`: PASS.
  - `npm run typecheck`: PASS.
  - Focused Vitest command: PASS, 21 tests.
  - Playwright branding command: PASS, 13 tests.

- [x] Review with a subagent.

  Observed on 2026-05-17: first review found nested `main` inside `DashboardLayout` landmark; fixed by changing the AI Hub wrapper to `section`. Re-review PASS with no blocking findings.

- [ ] Commit intentional files only, push `feature/branding-mobile-action-workspace`, run PR continuity, request current-head CodeRabbit review, and keep PR #202 auto-merge enabled without stopping on pending checks.
