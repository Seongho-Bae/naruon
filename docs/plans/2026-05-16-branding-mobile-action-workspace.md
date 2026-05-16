# Branding Mobile Action Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the mobile inbox match the `frontend/branding/uiux` action-workspace direction by exposing inbox, search/context, AI execution, and schedule actions without hover-only controls.

**Architecture:** Keep the desktop layout unchanged. Convert the mobile bottom navigation in `DashboardLayout` into explicit buttons that dispatch a typed browser event, then let `app/page.tsx` switch between the inbox, detail, AI execution graph, search/context placeholder, and schedule placeholder.

**Tech Stack:** Next.js 16 app router, React 19 client components, Vitest/jsdom unit tests, Playwright acceptance tests, Tailwind utility classes.

---

## Source Gap

- `frontend/branding/uiux/uiux2.png` and `frontend/branding/uiux/uiux8.png` define a mobile-first workspace with direct bottom affordances for inbox, context search, relationship/context, schedule, and more/actions.
- `docs/plans/2026-05-11-frontend-brand-redesign-implementation.md` requires Playwright coverage for desktop/mobile shell, local brand assets, and dashboard flows.
- Current `frontend/src/app/page.tsx` has `showMobileActions = false`, so the mobile AI execution section can never be reached.
- Current `frontend/src/components/DashboardLayout.tsx` renders mobile bottom navigation from mail folders as links, while `frontend/tests/e2e/dashboard-branding.spec.ts` already expects visible mobile buttons for `받은편지함` and `AI 실행`.

## Files

- Modify: `frontend/src/components/DashboardLayout.test.tsx`
- Modify: `frontend/tests/e2e/dashboard-branding.spec.ts`
- Modify: `frontend/src/components/DashboardLayout.tsx`
- Modify: `frontend/src/app/page.tsx`

## Task 1: Mobile action navigation emits workspace events

- [ ] **Step 1: Write failing unit test**

Update `frontend/src/components/DashboardLayout.test.tsx` so the mobile nav assertion expects action buttons and verifies the custom event:

```tsx
const mobileNavButtons = Array.from(mobileNav?.querySelectorAll('button') ?? []).map(
  (button) => button.textContent,
);
expect(mobileNavButtons).toEqual(["받은편지함", "맥락 검색", "AI 실행", "일정"]);

const events: string[] = [];
window.addEventListener("naruon:mobile-workspace", ((event: Event) => {
  events.push((event as CustomEvent<{ view: string }>).detail.view);
}) as EventListener);

act(() => {
  mobileNav?.querySelector<HTMLButtonElement>('button[data-mobile-view="actions"]')?.click();
});

expect(events).toContain("actions");
```

- [ ] **Step 2: Verify RED**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx
```

Expected: FAIL because the component still renders mail-folder links instead of action buttons.

- [ ] **Step 3: Implement minimal event-emitting nav**

In `frontend/src/components/DashboardLayout.tsx`, replace the mobile bottom nav source with action items:

```tsx
const mobileWorkspaceItems = [
  { label: '받은편지함', icon: Inbox, view: 'inbox' as const },
  { label: '맥락 검색', icon: Search, view: 'search' as const },
  { label: 'AI 실행', icon: Sparkles, view: 'actions' as const },
  { label: '일정', icon: CalendarDays, view: 'calendar' as const },
];
```

Render each item as a `button` and dispatch:

```tsx
window.dispatchEvent(new CustomEvent('naruon:mobile-workspace', { detail: { view } }));
```

- [ ] **Step 4: Verify GREEN**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx
```

Expected: PASS.

## Task 2: Mobile page exposes AI execution, search, and schedule panels

- [ ] **Step 1: Write failing Playwright acceptance**

Extend `frontend/tests/e2e/dashboard-branding.spec.ts`:

```ts
await page.getByRole('button', { name: 'AI 실행' }).click();
await expect(page.getByRole('region', { name: '모바일 AI 실행' })).toBeVisible();
await expect(page.getByText('관계 맥락')).toBeVisible();

await page.getByRole('button', { name: '맥락 검색' }).click();
await expect(page.getByRole('region', { name: '모바일 맥락 검색' })).toBeVisible();
await expect(page.getByText('메일, 첨부, 일정, 사람을 한 번에 검색합니다.')).toBeVisible();

await page.getByRole('button', { name: '일정' }).click();
await expect(page.getByRole('region', { name: '모바일 일정 연결' })).toBeVisible();
await expect(page.getByText('캘린더 반영 대기')).toBeVisible();
```

- [ ] **Step 2: Verify RED**

Run:

```bash
npm run test:e2e -- dashboard-branding.spec.ts
```

Expected: FAIL because mobile action buttons are not wired to visible page sections yet.

- [ ] **Step 3: Implement mobile panels**

In `frontend/src/app/page.tsx`, replace `showMobileActions` with `mobileView` state. Listen for `naruon:mobile-workspace` events and render panels for `actions`, `search`, and `calendar`.

- [ ] **Step 4: Verify GREEN**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx
npm run test:e2e -- dashboard-branding.spec.ts
```

Expected: PASS.

## Task 3: Final verification

- [ ] Run:

```bash
npm run lint
npm run typecheck
npm test -- src/components/DashboardLayout.test.tsx
```

- [ ] Commit:

```bash
git add docs/plans/2026-05-16-branding-mobile-action-workspace.md frontend/src/components/DashboardLayout.tsx frontend/src/components/DashboardLayout.test.tsx frontend/src/app/page.tsx frontend/tests/e2e/dashboard-branding.spec.ts
git commit -m "feat: expose mobile AI action workspace"
```
