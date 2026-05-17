# Mobile Search Calendar API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the mobile search and calendar placeholder panels with API-backed loading, success, empty, and error states so mobile users see real workspace data instead of `준비 중` cards.

**Architecture:** Keep `Home` as the owner of mobile workspace routing, but extract the two API-backed panel bodies into focused client components in `frontend/src/components/mobile-workspace-panels.tsx`. Both panels reuse the existing `/api/search` endpoint through `apiClient.post`, avoiding a new backend API surface while still replacing hardcoded placeholder content with live data states.

**Tech Stack:** Next.js 16 app router, React 19 client components, existing `ApiClient`, Vitest/jsdom, Playwright route mocks.

---

## Source Gap

- `docs/plans/2026-05-16-branding-roadmap-next-gaps.md` lists **P1 — API-backed mobile search/calendar**: replace placeholder panels with real loading/empty/error/success states.
- `frontend/src/app/page.tsx` currently hardcodes `메일/첨부/일정/사람 결과 준비 중` in `#mobile-search` and static calendar titles in `#mobile-calendar`.
- `frontend/tests/e2e/dashboard-branding.spec.ts` currently asserts those placeholders, so tests must be converted to assert API-backed behavior.

## Files

- Create: `frontend/src/components/mobile-workspace-panels.tsx`
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/app/page.test.tsx`
- Modify: `frontend/tests/e2e/dashboard-branding.spec.ts`
- Modify: `frontend/tests/e2e/helpers.ts`
- Modify: `docs/plans/2026-05-16-branding-roadmap-next-gaps.md`

## Task 1: Prove the mobile panels must use API data

- [x] **Step 1: Write failing unit coverage**

  In `frontend/src/app/page.test.tsx`, mock `@/components/mobile-workspace-panels` with components that render `mock mobile search panel` and `mock mobile calendar panel`. Assert that the mobile hash routes `/#mobile-search` and `/#mobile-calendar` render those components instead of placeholder strings.

- [x] **Step 2: Verify RED**

  Run from `frontend/`:

  ```bash
  npm test -- src/app/page.test.tsx
  ```

  Expected: FAIL because `Home` still renders inline placeholder cards.

  Observed on 2026-05-17: FAIL because the active mobile panels still rendered `메일 결과 준비 중` and `디자인 리뷰 후속 조치` instead of API-backed loading states.

## Task 2: Implement reusable API-backed mobile panels

- [x] **Step 1: Create focused panel components**

  Create `frontend/src/components/mobile-workspace-panels.tsx` with:

  - `MobileSearchPanel` fetching `/api/search` with `{ query: '메일 첨부 일정 사람', limit: 4 }`.
  - `MobileCalendarPanel` fetching `/api/search` with `{ query: '회의 마감 후속 조치 일정', limit: 3 }`.
  - Shared rendering for loading (`검색 결과를 불러오는 중입니다.` / `일정 후보를 불러오는 중입니다.`), empty (`검색 결과가 없습니다.` / `일정 후보가 없습니다.`), error (`맥락 검색을 불러오지 못했습니다.` / `일정 후보를 불러오지 못했습니다.`), and success cards.

- [x] **Step 2: Wire panels into `Home`**

  In `frontend/src/app/page.tsx`, import the two panel components and replace the inline placeholder body of `#mobile-search` and `#mobile-calendar` with `<MobileSearchPanel active={effectiveMobileView === 'search'} />` and `<MobileCalendarPanel active={effectiveMobileView === 'calendar'} />`.

- [x] **Step 3: Verify GREEN**

  Run:

  ```bash
  npm test -- src/app/page.test.tsx
  ```

  Expected: PASS.

  Observed on 2026-05-17: PASS, 12 page tests. Added focused component coverage for API success, empty, and error states; `npm test -- src/components/mobile-workspace-panels.test.tsx src/app/page.test.tsx` passed 15 tests.

## Task 3: Convert Playwright evidence from placeholders to API-backed states

- [x] **Step 1: Update route mocks**

  In `frontend/tests/e2e/helpers.ts`, let `mockDashboardApi` return different `/api/search` results by query:

  - queries containing `회의` return a calendar candidate with subject `파트너 미팅 일정 확정`.
  - default search queries return search candidates with subject `Q2 출시 계획 및 우선순위 조정`.

- [x] **Step 2: Update E2E expectations**

  In `frontend/tests/e2e/dashboard-branding.spec.ts`, replace placeholder expectations:

  - `사람 결과 준비 중` becomes visible API result `Q2 출시 계획 및 우선순위 조정` under mobile search.
  - `디자인 리뷰 후속 조치` becomes visible API result `파트너 미팅 일정 확정` under mobile calendar.
  - Assert the old `준비 중` text is absent from the active panel.

- [x] **Step 3: Verify GREEN**

  Run with the dev server on `127.0.0.1:18081`:

  ```bash
  LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts
  ```

  Expected: PASS.

  Observed on 2026-05-17: PASS, 11 Playwright tests after fixing an effect cleanup bug where `status` in the dependency list cancelled the in-flight fetch immediately after switching to loading.

## Task 4: Final verification and delivery

- [x] Run from `frontend/`:

  ```bash
  npm run lint
  npm run typecheck
  npm test -- src/app/page.test.tsx src/app/layout.test.tsx src/components/EmailDetail.test.tsx src/components/DashboardLayout.test.tsx src/components/EmailList.test.tsx src/lib/workspace-preferences.test.ts
  LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts
  ```

- [x] Update `docs/plans/2026-05-16-branding-roadmap-next-gaps.md` so the P1 API-backed mobile search/calendar item reflects the implemented evidence.
- [ ] Commit intentional files only, push `feature/branding-mobile-action-workspace`, run PR continuity, request current-head CodeRabbit review, and keep PR #202 auto-merge enabled without stopping on pending checks.

Observed on 2026-05-17 from `frontend/`:

- `npm run lint` — PASS.
- `npm run typecheck` — PASS.
- `npm test -- src/app/page.test.tsx src/app/layout.test.tsx src/components/EmailDetail.test.tsx src/components/DashboardLayout.test.tsx src/components/EmailList.test.tsx src/components/mobile-workspace-panels.test.tsx src/lib/workspace-preferences.test.ts` — PASS, 30 tests.
- `LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts` — PASS, 11 tests.

Review follow-up: independent review found stale result display on panel reactivation, overly broad `/api/search` E2E mocks, and uncancelled requests during rapid mobile tab switching. Fixed by mounting API panels only while their mobile view is active, aborting in-flight fetches on unmount, adding a reactivation regression test, and branching Playwright `/api/search` mocks by query.
