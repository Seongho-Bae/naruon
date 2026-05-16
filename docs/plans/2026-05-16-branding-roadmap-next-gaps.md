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
2. **P0 — Header primary actions:** implement in this plan so visible action affordances are real buttons.
3. **P1 — Dead sidebar route handling:** replace 404-prone future navigation with disabled/coming-soon states or add route stubs.
4. **P1 — Tablet AI panel behavior:** add a 1024–1279px detail-tab/drawer layout for the right context panel.
5. **P1 — API-backed mobile search/calendar:** replace placeholder panels with real loading/empty/error/success states.
6. **P2 — InsightCard adoption:** refactor `EmailDetail` AI cards to use `InsightCard` consistently.

## Files

- Modify: `frontend/src/components/DashboardLayout.test.tsx`
- Modify: `frontend/tests/e2e/dashboard-branding.spec.ts`
- Modify: `frontend/src/components/DashboardLayout.tsx`

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
