# AI Hub Sidebar Deep Links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the remaining AI Hub sidebar dead space by making the `맥락 종합`, `판단 포인트`, and `실행 항목` menu items link to the real AI Hub sections.

**Architecture:** Keep the existing `/ai-hub` route as the single workspace and use hash anchors for its three visible regions. The desktop sidebar links to `/ai-hub#context`, `/ai-hub#decisions`, and `/ai-hub#actions`; the page exposes matching section IDs without introducing new backend endpoints.

**Tech Stack:** Next.js 16 App Router, React, Vitest/jsdom, Playwright.

---

## File map

- Modify `frontend/src/components/DashboardLayout.tsx`: replace disabled AI Hub child items with available hash links.
- Modify `frontend/src/components/DashboardLayout.test.tsx`: assert AI Hub child items are links, not `준비 중` disabled controls.
- Modify `frontend/src/app/ai-hub/page.tsx`: add stable IDs to each AI Hub section.
- Modify `frontend/src/app/ai-hub/page.test.tsx`: assert section IDs and labels match the sidebar link targets.
- Modify `frontend/tests/e2e/dashboard-branding.spec.ts`: assert desktop AI Hub sidebar links target the real route hashes and deep-linked sections render without overflow.

## Acceptance criteria

- [x] `맥락 종합`, `판단 포인트`, and `실행 항목` are desktop sidebar links, not `data-coming-soon` controls.
- [x] The three links point to `/ai-hub#context`, `/ai-hub#decisions`, and `/ai-hub#actions`.
- [x] `/ai-hub` renders sections with IDs `context`, `decisions`, and `actions`.
- [x] Desktop Playwright coverage proves the sidebar links exist and hash deep links land on visible AI Hub sections.
- [x] Existing mobile hamburger and startup-view behavior stays unchanged.

## TDD tasks

### Task 1: RED tests for truthful AI Hub sidebar links

- [x] Update `DashboardLayout.test.tsx` to expect the three AI Hub sidebar labels as anchors with `/ai-hub#...` hrefs and to expect they are absent from `data-coming-soon` controls.
- [x] Update `ai-hub/page.test.tsx` to expect each AI Hub region to have the matching `id`.
- [x] Run `npm test -- src/components/DashboardLayout.test.tsx src/app/ai-hub/page.test.tsx` from `frontend/` and confirm the new assertions fail because the current sidebar items are disabled and the page sections have no IDs.

### Task 2: GREEN implementation

- [x] Change `aiHubItems` in `DashboardLayout.tsx` to `href: '/ai-hub#context'`, `href: '/ai-hub#decisions'`, `href: '/ai-hub#actions'`, and `available: true`.
- [x] Add an `id` field to each AI Hub section definition in `page.tsx` and pass it to `HubCard` so each `<section>` receives the stable anchor ID.
- [x] Re-run the focused Vitest command and confirm it passes.

### Task 3: E2E proof and review-ready verification

- [x] Extend `dashboard-branding.spec.ts` to inspect the desktop AI Hub subnav link hrefs.
- [x] Extend the AI Hub responsive test to navigate to `/ai-hub#context`, `/ai-hub#decisions`, and `/ai-hub#actions` on desktop and verify the matching region is visible with no horizontal overflow.
- [x] Run focused Playwright, lint, and typecheck before commit.

## Evidence log

- RED: `npm test -- src/components/DashboardLayout.test.tsx src/app/ai-hub/page.test.tsx` failed before implementation because AI Hub child items were still disabled and AI Hub sections had no stable IDs.
- GREEN: `npm test -- src/components/DashboardLayout.test.tsx src/app/ai-hub/page.test.tsx` passed after adding sidebar hash links and section IDs.
- Verification: `npm run typecheck` passed.
- Verification: `npm run lint` passed.
- Verification: `LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- dashboard-branding.spec.ts` passed 16/16 against a current local Next dev server. The default `http://127.0.0.1:18080` server was stale and served an older bundle, so it was not used as acceptance evidence.
- Review follow-up: hash section links now set `aria-current="location"` after sidebar navigation, and Playwright clicks each sidebar item from `/` before asserting URL hash, visible section, and no horizontal overflow.
- Screenshot: `ai-hub-deep-links-1280.png` captured `/ai-hub#decisions` for desktop visual inspection.
