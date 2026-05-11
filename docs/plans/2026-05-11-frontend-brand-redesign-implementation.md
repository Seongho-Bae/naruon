# Frontend Brand Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship the #132 Naruon frontend redesign with local brand assets, guide-aligned shell/inbox/detail/graph surfaces, 40/44px controls, and Vitest plus Playwright evidence.

**Architecture:** Keep the current Next.js App Router and FastAPI contracts. Refactor the frontend into a board-driven execution workspace using local assets in `public/brand`, semantic CSS tokens in `globals.css`, existing React components, and deterministic mocked browser tests.

**Tech Stack:** Next.js 16, React 19, Tailwind CSS v4 CSS-first tokens, Base UI primitives, Vitest/jsdom, Playwright, TypeScript.

---

## Prerequisites

- Worktree: `/home/seongho/ai_email_client/.worktrees/frontend-brand-redesign-20260511`
- Design source: `docs/plans/2026-05-11-frontend-brand-redesign-design.md`
- If PR #133 is still unmerged, repeat its dependency cleanup in this branch before adding Playwright so `npm audit --package-lock-only --omit=dev --audit-level=moderate` can pass.

## Task 1: Dependency and test foundation

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Create: `frontend/src/test/setup.ts`
- Modify: `frontend/vitest.config.ts`
- Create: `frontend/src/test/types.ts`
- Create: `frontend/src/app/shadcn-tailwind.css` if #133 is not merged
- Modify: `frontend/src/app/globals.css` if #133 is not merged

**Step 1: Write failing setup/typecheck test contract**

Add `frontend/src/test/setup.ts` with only the React act environment assignment:

```ts
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
```

Add `frontend/src/test/types.ts`:

```ts
export {};

declare global {
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}
```

Update one existing test, such as `DashboardLayout.test.tsx`, to remove its local `globalThis.IS_REACT_ACT_ENVIRONMENT = true;` assignment. This should fail until Vitest loads setup globally.

**Step 2: Verify RED**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx
```

Expected: fails or emits setup-related act warnings until `vitest.config.ts` includes the setup file and globals type.

**Step 3: Implement foundation**

Update `frontend/vitest.config.ts` to include:

```ts
test: {
  setupFiles: ["./src/test/setup.ts"],
},
```

Remove local `globalThis.IS_REACT_ACT_ENVIRONMENT = true;` assignments from all frontend tests.

If #133 is still unmerged, remove `shadcn` from production dependencies and switch `globals.css` from `@import "shadcn/tailwind.css";` to a local `@import "./shadcn-tailwind.css";` copy that preserves the Base UI accordion height fallback.

Install Playwright as a dev dependency only:

```bash
npm install --save-dev @playwright/test
```

Add scripts:

```json
"typecheck": "tsc --noEmit",
"test:e2e": "playwright test"
```

**Step 4: Verify GREEN**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx
npm run typecheck
npm audit --package-lock-only --omit=dev --audit-level=moderate
```

Expected: test passes, typecheck passes, production audit passes with no moderate+ vulnerabilities.

**Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vitest.config.ts frontend/src/test frontend/src/app/globals.css frontend/src/app/shadcn-tailwind.css
git commit -m "test: prepare frontend redesign verification"
```

## Task 2: Local brand assets and metadata

**Files:**
- Create: `frontend/public/brand/naruon-symbol.svg`
- Create: `frontend/public/brand/naruon-logo.svg`
- Create: `frontend/public/brand/naruon-app-icon.svg`
- Modify: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/layout.test.tsx`

**Step 1: Write failing tests**

Create `frontend/src/app/layout.test.tsx`:

```tsx
import { describe, expect, it } from "vitest";
import { metadata } from "./layout";

describe("root layout metadata", () => {
  it("describes the Korean-first Naruon workspace and local icons", () => {
    expect(metadata.title).toBe("Naruon | AI Email Workspace");
    expect(metadata.description).toContain("이메일");
    expect(metadata.icons).toMatchObject({ icon: "/brand/naruon-app-icon.svg" });
  });
});
```

**Step 2: Verify RED**

Run:

```bash
npm test -- src/app/layout.test.tsx
```

Expected: fails because metadata is missing icons or Korean description.

**Step 3: Implement local assets and metadata**

Create deterministic SVG assets based on the visible Naruon mark: blue/purple upward flow, blue star, green star, and wordmark.

Update `metadata` in `layout.tsx`:

```ts
export const metadata: Metadata = {
  title: "Naruon | AI Email Workspace",
  description: "Naruon은 이메일, 일정, 관계, 판단 포인트를 하나의 맥락으로 연결하는 AI 이메일 워크스페이스입니다.",
  icons: { icon: "/brand/naruon-app-icon.svg" },
};
```

**Step 4: Verify GREEN**

Run:

```bash
npm test -- src/app/layout.test.tsx
npm run typecheck
```

Expected: both pass.

**Step 5: Commit**

```bash
git add frontend/public/brand frontend/src/app/layout.tsx frontend/src/app/layout.test.tsx
git commit -m "feat: add local Naruon brand assets"
```

## Task 3: Brand tokens and control sizing

**Files:**
- Modify: `frontend/src/app/globals.css`
- Modify: `frontend/src/components/ui/button.tsx`
- Modify: `frontend/src/components/ui/input.tsx`
- Modify: `frontend/src/components/ui/textarea.tsx`
- Create: `frontend/src/components/ui/control-sizing.test.tsx`

**Step 1: Write failing sizing tests**

Create `control-sizing.test.tsx` that renders `Button`, `Input`, and `Textarea` and asserts class strings include 40px/default and 44px/large control contracts:

```tsx
/* @vitest-environment jsdom */
import React from "react";
import { createRoot } from "react-dom/client";
import { act } from "react";
import { describe, expect, it } from "vitest";
import { Button } from "./button";
import { Input } from "./input";
import { Textarea } from "./textarea";

describe("brand control sizing", () => {
  it("uses guide-aligned default control heights and radii", () => {
    const container = document.createElement("div");
    const root = createRoot(container);
    act(() => root.render(<><Button>버튼</Button><Input /><Textarea /></>));
    expect(container.querySelector("button")?.className).toContain("h-10");
    expect(container.querySelector("input")?.className).toContain("h-10");
    expect(container.querySelector("textarea")?.className).toContain("min-h-24");
    act(() => root.unmount());
  });
});
```

**Step 2: Verify RED**

Run:

```bash
npm test -- src/components/ui/control-sizing.test.tsx
```

Expected: fails because current defaults are `h-8`, `h-7`, and `min-h-16`.

**Step 3: Implement tokens and sizing**

Add `--naruon-*` CSS variables from the design doc and map existing app variables to them.

Update primitives:

- Button default: `h-10`, `rounded-xl`, `px-4`
- Button small: `h-8`
- Button large: `h-11`
- Icon: `size-10`
- Input default: `h-10`, `rounded-xl`, `px-3`
- Textarea: `min-h-24`, `rounded-2xl`, `px-3`

**Step 4: Verify GREEN**

Run:

```bash
npm test -- src/components/ui/control-sizing.test.tsx
npm run lint
npm run typecheck
```

Expected: all pass without warnings.

**Step 5: Commit**

```bash
git add frontend/src/app/globals.css frontend/src/components/ui frontend/src/components/ui/control-sizing.test.tsx
git commit -m "feat: align frontend controls with brand guide"
```

## Task 4: Dashboard shell redesign

**Files:**
- Modify: `frontend/src/components/DashboardLayout.tsx`
- Modify: `frontend/src/components/DashboardLayout.test.tsx`

**Step 1: Write failing shell tests**

Extend `DashboardLayout.test.tsx` to assert:

- logo uses `/brand/naruon-logo.svg` or `/brand/naruon-symbol.svg`;
- mobile bottom navigation exists;
- sidebar includes mail nav and AI workspace nav groups;
- primary actions include `캘린더 반영`, `답장 초안`, and `할 일 만들기`.

**Step 2: Verify RED**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx
```

Expected: fails because current shell uses inline SVG and lacks mobile bottom nav and full action set.

**Step 3: Implement shell**

Replace `NaruonMark` inline SVG with a reusable local asset rendering path. Build left sidebar, top header, mobile app bar, and bottom nav using existing icons and accessible labels.

**Step 4: Verify GREEN**

Run:

```bash
npm test -- src/components/DashboardLayout.test.tsx
npm run lint
npm run typecheck
```

Expected: all pass.

**Step 5: Commit**

```bash
git add frontend/src/components/DashboardLayout.tsx frontend/src/components/DashboardLayout.test.tsx
git commit -m "feat: redesign Naruon workspace shell"
```

## Task 5: Inbox thread list redesign

**Files:**
- Modify: `frontend/src/components/EmailList.tsx`
- Create: `frontend/src/components/EmailList.test.tsx`

**Step 1: Write failing inbox tests**

Create `EmailList.test.tsx` with mocked `fetch` that verifies:

- initial `GET /api/emails`;
- search `POST /api/search` body;
- localized loading, error, and empty states;
- `받은편지함`, `맥락 종합`, and `실행 항목` copy;
- selected row has `aria-current="true"` or `aria-selected="true"` and visible selected label/rail class;
- no subject, unread, and thread-count badges render.

**Step 2: Verify RED**

Run:

```bash
npm test -- src/components/EmailList.test.tsx
```

Expected: fails because tests target localized/redesigned states.

**Step 3: Implement inbox**

Convert tall cards into dense, scannable rows with board-aligned selection, status labels, and Korean-first microcopy.

**Step 4: Verify GREEN**

Run:

```bash
npm test -- src/components/EmailList.test.tsx
npm run lint
npm run typecheck
```

Expected: all pass.

**Step 5: Commit**

```bash
git add frontend/src/components/EmailList.tsx frontend/src/components/EmailList.test.tsx
git commit -m "feat: redesign inbox thread list"
```

## Task 6: Detail and action workspace redesign

**Files:**
- Modify: `frontend/src/components/EmailDetail.tsx`
- Modify: `frontend/src/components/EmailDetail.test.tsx`

**Step 1: Write failing detail tests**

Extend tests to verify Korean-first labels and state preservation:

- `AI 생성` instead of `AI Generated`;
- `요약을 생성하는 중입니다` instead of `Generating summary...`;
- `실행 항목` count label;
- calendar sync success/error roles;
- send failure keeps draft text;
- no-selection view uses Naruon context/judgment/execution copy.

**Step 2: Verify RED**

Run:

```bash
npm test -- src/components/EmailDetail.test.tsx
```

Expected: fails on old English labels and current layout contracts.

**Step 3: Implement detail redesign**

Rework detail header, AI summary card, action card, conversation card, and reply card. Keep API calls unchanged and preserve failure semantics.

**Step 4: Verify GREEN**

Run:

```bash
npm test -- src/components/EmailDetail.test.tsx
npm run lint
npm run typecheck
```

Expected: all pass.

**Step 5: Commit**

```bash
git add frontend/src/components/EmailDetail.tsx frontend/src/components/EmailDetail.test.tsx
git commit -m "feat: redesign email detail actions"
```

## Task 7: Graph accessibility and page composition

**Files:**
- Modify: `frontend/src/components/NetworkGraph.tsx`
- Modify: `frontend/src/components/NetworkGraph.test.tsx`
- Modify: `frontend/src/app/page.tsx`
- Create: `frontend/src/app/page.test.tsx`

**Step 1: Write failing tests**

Add tests that verify:

- graph loading/error/empty copy is Korean;
- populated graph renders an accessible text summary of nodes and relationships;
- tooltip sanitization still passes;
- `page.tsx` composes shell, inbox, detail, and graph/action panel and propagates selected email ID.

**Step 2: Verify RED**

Run:

```bash
npm test -- src/components/NetworkGraph.test.tsx src/app/page.test.tsx
```

Expected: fails because text fallback and page composition tests are new.

**Step 3: Implement graph/page**

Add text fallback/summary and board-aligned graph panel. Keep `vis-network` sanitization. Adjust `page.tsx` default panel proportions and responsive classes.

**Step 4: Verify GREEN**

Run:

```bash
npm test -- src/components/NetworkGraph.test.tsx src/app/page.test.tsx
npm run lint
npm run typecheck
```

Expected: all pass.

**Step 5: Commit**

```bash
git add frontend/src/components/NetworkGraph.tsx frontend/src/components/NetworkGraph.test.tsx frontend/src/app/page.tsx frontend/src/app/page.test.tsx
git commit -m "feat: add accessible graph workspace"
```

## Task 8: Playwright browser acceptance

**Files:**
- Create: `frontend/playwright.config.ts`
- Create: `frontend/tests/e2e/dashboard-branding.spec.ts`
- Create: `frontend/tests/e2e/dashboard-flows.spec.ts`

**Step 1: Write failing Playwright tests**

Create `dashboard-branding.spec.ts` to assert desktop/mobile shell, local brand logo, no external font requests, and keyboard skip-link behavior.

Create `dashboard-flows.spec.ts` to mock `/api/emails`, `/api/search`, `/api/emails/:id`, `/api/llm/summarize`, `/api/llm/draft`, `/api/emails/send`, `/api/calendar/sync`, and `/api/network/graph` and assert select/search/detail/calendar/reply/graph paths.

**Step 2: Verify RED**

Run:

```bash
npm run test:e2e
```

Expected: fails until config and mocks are complete.

**Step 3: Implement Playwright config and mocks**

Use `webServer` with `npm run dev`, `reuseExistingServer: !process.env.CI`, and deterministic mocked routes in each spec. Avoid screenshot baselines unless the environment has stable browser fonts; prefer locator and computed-style assertions.

**Step 4: Verify GREEN**

Run:

```bash
npm run test:e2e
npm test
npm run lint
npm run typecheck
npm run build
npm audit --package-lock-only --omit=dev --audit-level=moderate
```

Expected: all pass, no warnings or moderate+ production vulnerabilities.

**Step 5: Commit**

```bash
git add frontend/playwright.config.ts frontend/tests/e2e frontend/package.json frontend/package-lock.json
git commit -m "test: cover Naruon redesign in Playwright"
```

## Final verification and delivery

Run from `frontend/`:

```bash
npm test
npm run test:e2e
npm run lint
npm run typecheck
npm run build
npm audit --package-lock-only --omit=dev --audit-level=moderate
```

Run from repo root:

```bash
git diff --check
```

Then push the branch, create or update the #132 PR, post verification evidence to issue #132, and follow current-head robot-review gate policy. If GitHub still blocks merge for org human-review ruleset #128, record exact blocker evidence and keep auto-merge enabled where possible.
