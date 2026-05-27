# Branding Roadmap Next Gaps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Continue closing the `docs/plans/` + `frontend/branding/` gap by turning visible Naruon header primary actions into real accessible controls instead of inert status chips.

**Architecture:** Preserve the branded shell and mobile workspace work already in progress. Keep the header action labels and visual treatment, but render them as typed buttons that dispatch a lightweight browser event for downstream page-level handlers. This makes the UI affordance truthful while keeping the delivery slice small and testable.

**Tech Stack:** Next.js 16 app router, React 19 client components, Vitest/jsdom unit tests, Playwright acceptance tests, Tailwind utility classes.

---

## Source Gap

- `docs/plans/2026-05-11-frontend-brand-redesign-design.md` requires a top header with global search and right-side primary actions.
- `docs/plans/2026-05-11-frontend-brand-redesign-implementation.md` requires primary actions: `캘린더 반영`, `답장 초안`, and `할 일 만들기`.
- `frontend/branding/uiux/uiux3.png`, `frontend/branding/uiux/uiux4.png`, and `frontend/branding/brand_assets/4.png`/`5.png` show a decision/action-oriented workspace, but the current header renders those primary actions as non-interactive chips.

## Current Roadmap

1. **P0 — Mobile action workspace:** mostly implemented in `docs/plans/2026-05-16-branding-mobile-action-workspace.md`; remaining semantic cleanup is tracked by tests and review feedback.
2. **P0 — Header primary actions:** shell buttons implemented here; selected-email execution bridge implemented by `docs/plans/2026-05-17-branding-shell-action-bridge.md`.
3. **P0 — Desktop GNB + mobile central AI action:** implemented by `docs/plans/2026-05-17-branding-shell-gnb-mobile-ai.md` so the brand assets' global wayfinding and primary mobile action affordance are present in the shell.
4. **P1 — Dead sidebar route handling:** implemented by `docs/plans/2026-05-17-branding-shell-gnb-mobile-ai.md` with disabled/coming-soon controls for unavailable future routes.
5. **P1 — Tablet AI panel behavior:** implemented by `docs/plans/2026-05-17-tablet-ai-panel-collapse.md` with a 1024–1279px collapsed context panel and tablet header action coverage.
6. **P1 — API-backed mobile search/calendar:** implemented by `docs/plans/2026-05-17-mobile-search-calendar-api.md` with `/api/search`-backed loading, success, empty, and error states for mobile panels.
7. **P2 — InsightCard adoption:** implemented by making `EmailDetail` render `맥락 종합`, `실행 항목`, and `답장 실행` through reusable `InsightCard` wrappers with stable `article[data-insight-card]` landmarks, loading/error/empty state handling, and footer action/status preservation.

## P2 InsightCard adoption evidence

- RED: `npm test -- src/components/EmailDetail.test.tsx` failed because `EmailDetail` rendered zero `article[data-insight-card="true"]` landmarks for `맥락 종합`, `실행 항목`, and `답장 실행`.
- GREEN: `npm test -- src/components/EmailDetail.test.tsx` passed with 8 tests after refactoring summary/action/reply sections to `InsightCard`.
- Regression suite: `npm test -- src/components/EmailDetail.test.tsx src/components/DashboardLayout.test.tsx src/app/page.test.tsx src/app/ai-hub/page.test.tsx src/components/mobile-workspace-panels.test.tsx` passed with 33 tests.
- Static checks: `npm run typecheck` and `npm run lint` passed.
- Responsive/browser evidence: mocked localhost Playwright smoke confirmed insight cards `맥락 종합`, `실행 항목`, `답장 실행` render with no horizontal overflow; screenshot captured as `email-insight-cards-1280.png`.

## Files

- Modify: `frontend/src/components/DashboardLayout.test.tsx`
- Modify: `frontend/tests/e2e/dashboard-branding.spec.ts`
- Modify: `frontend/src/components/DashboardLayout.tsx`
- P2 completed with: `frontend/src/components/EmailDetail.test.tsx`
- P2 completed with: `frontend/src/components/EmailDetail.tsx`
- P2 completed with: `frontend/src/components/InsightCard.tsx`

## Task 1: Header primary actions are accessible buttons

- [ ] **Step 1: Write failing unit test**

Update `frontend/src/components/DashboardLayout.test.tsx` so the header actions are queried as buttons and clicking one emits `naruon:header-action`:

```tsx
const headerActionButtons = Array.from(
  banner?.querySelectorAll<HTMLButtonElement>('button[data-header-action]') ?? [],
).map((button) => button.textContent);
expect(headerActionButtons).toEqual(["캘린더 반영", "답장 초안", "할 일 만들기"]);

const headerEvents: string[] = [];
window.addEventListener("naruon:header-action", ((event: Event) => {
  headerEvents.push((event as CustomEvent<{ action: string }>).detail.action);
}) as EventListener);

act(() => {
  banner?.querySelector<HTMLButtonElement>('button[data-header-action="reply-draft"]')?.click();
});

expect(headerEvents).toContain("reply-draft");
```

- [ ] **Step 2: Verify RED**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx
```

Expected: FAIL because the header currently uses spans, not buttons.

- [ ] **Step 3: Implement minimal button behavior**

In `frontend/src/components/DashboardLayout.tsx`, give each header action an `action` id and render a `<button type="button" data-header-action="...">` that dispatches:

```tsx
window.dispatchEvent(new CustomEvent('naruon:header-action', { detail: { action } }));
```

- [ ] **Step 4: Verify GREEN**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx
npm run lint
npm run typecheck
```

Expected: PASS.

## Task 2: Branding E2E checks truthful header actions

- [ ] **Step 1: Write failing Playwright assertion**

Update `frontend/tests/e2e/dashboard-branding.spec.ts` to expect the three header actions as buttons instead of asserting they are not buttons:

```ts
await expect(header.getByRole('button', { name: '캘린더 반영' })).toBeVisible();
await expect(header.getByRole('button', { name: '답장 초안' })).toBeVisible();
await expect(header.getByRole('button', { name: '할 일 만들기' })).toBeVisible();
```

- [ ] **Step 2: Verify RED**

Run:

```bash
npm run test:e2e -- dashboard-branding.spec.ts
```

Expected: FAIL until the header chip implementation is replaced by real buttons.

- [ ] **Step 3: Verify GREEN after implementation**

Run:

```bash
npm run test:e2e -- dashboard-branding.spec.ts
```

Expected: PASS.
