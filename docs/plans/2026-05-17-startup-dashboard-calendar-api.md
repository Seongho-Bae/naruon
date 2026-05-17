# Startup Dashboard and Calendar API Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace desktop startup dashboard and calendar fixed candidate copy with API-backed loading, success, empty, and error states.

**Architecture:** Reuse the existing `/api/search` contract used by mobile search/calendar panels so the desktop startup surfaces reflect live workspace data without introducing new backend endpoints. Keep the dashboard/email/calendar startup choice unchanged and preserve mobile hash override behavior.

**Tech Stack:** Next.js 16 app router, React 19 client components, Vitest/jsdom, Playwright localhost smoke.

---

## Source gap

- `docs/plans/2026-05-17-north-star-platform-roadmap.md` calls out the next slice after AI Hub: keep the startup dashboard/email/calendar choice, but make dashboard/calendar API-backed.
- Before this slice, `frontend/src/app/page.tsx` rendered fixed desktop dashboard counters (`12`, `3`, `8`) and fixed desktop calendar candidates (`Q2 출시 우선순위 회의`, `벤더 계약 검토`, `디자인 리뷰 후속 조치`).
- Mobile search/calendar were already API-backed through `/api/search`; desktop startup views lagged behind the same contract.

## Files

- Modify: `frontend/src/app/page.test.tsx`
- Modify: `frontend/src/app/page.tsx`
- Add: `docs/plans/2026-05-17-startup-dashboard-calendar-api.md`

## Task 1: Desktop dashboard uses live search results

- [x] Write a failing unit test that saves `naruon_startup_view=dashboard`, mocks `/api/search`, and expects live subjects such as `고객 계약 승인 대기` and `출시 리뷰 일정 조율` to replace the old fixed counter copy.
- [x] Verify RED with `npm test -- src/app/page.test.tsx`; expected failure: dashboard still showed `오늘 답장 또는 위임이 필요한 스레드` and no live subject.
- [x] Implement `useStartupSearch()` and `StartupResultList` in `frontend/src/app/page.tsx`, calling `/api/search` with `판단 대기 캘린더 반영 실행 항목` and safe React text-node normalization.
- [x] Verify GREEN with `npm test -- src/app/page.test.tsx`.

## Task 2: Desktop calendar uses live calendar candidates

- [x] Write a failing unit test that saves `naruon_startup_view=calendar`, mocks `/api/search`, and expects `엔터프라이즈 데모 일정` while removing static `디자인 리뷰 후속 조치`.
- [x] Verify RED with `npm test -- src/app/page.test.tsx`; expected failure: static desktop calendar candidates remained.
- [x] Reuse `useStartupSearch()` with `회의 마감 후속 조치 일정`, preserving loading/error/empty states.
- [x] Verify GREEN with `npm test -- src/app/page.test.tsx`.

## Evidence

- RED: `npm test -- src/app/page.test.tsx` failed with two expected startup API assertions after test helper correction.
- Follow-up RED: `npm test -- src/app/page.test.tsx` failed when a saved dashboard plus `#mobile-calendar` hash still mounted the dashboard once and issued the dashboard search query.
- GREEN: `npm test -- src/app/page.test.tsx` passed with 19 tests, including success, empty, error, and mobile hash override guards.
- Regression suite: `npm test -- src/app/page.test.tsx src/components/EmailDetail.test.tsx src/components/DashboardLayout.test.tsx src/app/ai-hub/page.test.tsx src/components/mobile-workspace-panels.test.tsx` passed with 38 tests.
- Static checks: `npm run typecheck` and `npm run lint` passed.
- Responsive/browser evidence: mocked localhost Playwright smoke confirmed dashboard and calendar startup views render API search results with no horizontal overflow; screenshot captured as `startup-calendar-api-1280.png`.
- E2E: `LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts` passed with 16 tests.
