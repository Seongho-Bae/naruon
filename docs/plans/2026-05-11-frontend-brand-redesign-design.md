# Frontend Brand Redesign Design

**Issue:** #132, `브랜딩 가이드 이미지 기준 Frontend 디자인 재정렬`

**Goal:** Realign the Naruon frontend with the supplied brand and UI guide assets so the product reads as an AI email workspace for context, judgment, and execution instead of a lightly themed email client.

**Status:** Design recorded before implementation. This document is the source of truth for the #132 implementation plan.

## Evidence used

- Branding board: `frontend/branding/naruon_branding.png`
- Foundation assets: `frontend/branding/brand_assets/1.png`
- Form/input assets: `frontend/branding/brand_assets/2.png`
- Navigation assets: `frontend/branding/uiux/uiux2.png`
- High-fidelity product direction: `frontend/branding/uiux/uiux3.png`
- Navigation and dashboard patterns: `frontend/branding/uiux/uiux7.png`
- Current frontend shell: `frontend/src/components/DashboardLayout.tsx`
- Current workspace composition: `frontend/src/app/page.tsx`
- Current inbox/detail/graph components: `EmailList.tsx`, `EmailDetail.tsx`, `NetworkGraph.tsx`
- Next.js static asset guidance: public assets are served from `/...`, and local images should use explicit dimensions when rendered with `next/image`.

## Constraints

- No external font endpoint. Use local/static fonts only if bundled; otherwise use system fallback stacks already present in `globals.css`.
- Logo/favicon/social assets must be project-local, not copied from external URLs.
- Playwright coverage is required for changed user-facing functional points.
- Keep current backend API contracts. This redesign changes presentation and interaction states only.
- Keep existing accessibility landmarks and improve them where the row/list interaction needs stronger semantics.
- Current package state on `master` still includes vulnerable `shadcn` production dependency. #133 removes it. The #132 implementation should either build on the #133 dependency state or repeat the same removal if #133 has not landed before #132 needs verification.
- `npx tsc --noEmit` currently reports pre-existing test type issues around `globalThis.IS_REACT_ACT_ENVIRONMENT` and `vis-network` test data access. The implementation plan must either fix these or explicitly gate typecheck separately from the redesign if out of scope.

## Approaches considered

### Approach A: Token-only polish

Update CSS variables, button/input sizing, and some copy while keeping the current resizable three-panel shell.

- Pros: smallest diff, low risk to current component structure.
- Cons: leaves the product feeling like a generic email client, does not address mobile IA, and does not use the guide's navigation or dense inbox patterns.

### Approach B: Board-driven execution workspace, chosen

Implement the UI as a brand-board-aligned execution workspace: persistent navigation, dense inbox/thread list, detail workspace, and AI/context action panel.

- Pros: matches the Naruon brand promise, uses the provided UIUX boards directly, gives desktop and mobile a clear information architecture, and creates strong Playwright acceptance points.
- Cons: larger component diff and requires careful tests around async states.

### Approach C: Separate marketing/login redesign first

Start with the login/marketing style from `uiux3.png`, then later redesign the app shell.

- Pros: visually impressive and close to brand hero boards.
- Cons: current repo entry point is the dashboard; this delays the actual #132 acceptance criteria around shell, inbox, detail, controls, and Playwright coverage.

## Chosen design

Use Approach B. The app shell should communicate this progression in the first scan:

1. **맥락 종합:** email, people, files, and schedules are connected.
2. **판단 포인트:** the system surfaces the decision points.
3. **실행 항목:** the user can create follow-up actions, calendar entries, or replies.

The redesign should preserve the existing functional surfaces but reorder visual priority so AI context and next actions are not hidden below the email body.

## Brand system decisions

### Assets

- Add project-local logo and symbol assets under `frontend/public/brand/`.
- Use a clean SVG for the primary logo and symbol rather than the current inline approximation in `DashboardLayout.tsx`.
- Add a favicon/app icon asset under the same local brand directory or Next app icon convention.
- Keep all asset references root-relative, such as `/brand/naruon-logo.svg`.

### Colors

Expose semantic tokens in `globals.css` and map Tailwind theme values to them:

| Token | Value | Use |
| --- | --- | --- |
| `--naruon-ink` | `#0B1220` | Primary text, dark logo text |
| `--naruon-primary` | `#2563FF` | Primary actions, selection, active nav |
| `--naruon-indigo` | `#4F46E5` | Secondary brand emphasis |
| `--naruon-purple` | `#7C3AED` | 판단 포인트, insight states |
| `--naruon-green` | `#22C55E` | 실행 항목, success states |
| `--naruon-sky` | `#38BDF8` | Informational accents |
| `--naruon-slate` | `#64748B` | Secondary copy |
| `--naruon-border` | `#E5E7EB` | Default borders |
| `--naruon-bg` | `#F8FAFC` | App background |
| `--naruon-surface` | `#FFFFFF` | Cards and panels |

### Typography

- Korean-first UI stack: `Pretendard, "Apple SD Gothic Neo", "Malgun Gothic", "Segoe UI", ui-sans-serif, system-ui, sans-serif`.
- English/numeric fallback may use Inter only if bundled locally; otherwise keep system fonts.
- Use board scale: 40px H1 for major app page title, 20px section headings, 16px body, 14px labels/buttons, 12px captions/meta.

### Control sizing

- Default button and input height: 40px.
- Large/mobile-primary button height: 44px.
- Small buttons: 32px.
- Icon buttons: 40px square.
- Touch targets must not drop below 44px on mobile.

## Layout decisions

### Desktop

- Persistent left sidebar, 240px target width, with logo, primary mail nav, AI workspace nav, and assistant/status card.
- Top header, 64px target height, with global search and right-side actions.
- Main workspace uses three zones at wide widths:
  - Inbox/thread list, dense and scannable.
  - Email detail/thread workspace.
  - AI context/action panel for summary, 판단 포인트, 실행 항목, related entities, and graph fallback.
- Existing resizable panels can stay if they do not fight the design, but the default composition must look intentional without user resizing.

### Tablet

- Collapse the right AI panel into detail tabs or a drawer around 1024 to 1279px.
- Keep search visible and preserve primary actions.

### Mobile

- Use a compact app bar and bottom navigation.
- Show one primary task at a time: inbox, detail, or AI/actions.
- Provide an obvious path from inbox to thread detail to execution actions.
- Do not rely on hover-only controls.

## Component decisions

### `DashboardLayout`

- Replace inline logo approximation with local brand asset.
- Keep `aside`, `header`, `nav`, `main`, and skip link landmarks.
- Add a mobile navigation affordance and bottom nav surface if feasible in the implementation slice.
- Active navigation must include text, icon, and `aria-current="page"`.

### `EmailList`

- Change tall card rows into denser thread rows inspired by the board.
- Each row should show sender, subject, snippet, date, unread/new status, thread count, and priority/status when available.
- Selected state should use a left rail plus pale blue background.
- Empty, error, loading, and search-empty states must be localized Korean-first and action-oriented.

### `EmailDetail`

- Keep no-selection, loading, error, thread, LLM summary, action-item, calendar sync, and reply flows.
- Reorder the detail so the header and AI/action cards are easier to scan.
- Normalize mixed English/Korean labels, such as `AI Generated`, `Tasks`, and `Loading details...`, to Korean-first labels.
- Preserve draft text on send failure.

### `NetworkGraph`

- Keep existing XSS-safe tooltip behavior.
- Add a textual fallback or companion summary because canvas graphs are not sufficient for screen readers.
- Localize loading, error, and empty copy.

### UI primitives

- Update `button.tsx`, `input.tsx`, and `textarea.tsx` to match 40/44px sizing and board radii.
- Keep focus-visible rings strong. Do not remove outlines for aesthetics.

## State and edge-case decisions

- Loading should use stable skeleton or status regions, not layout-jumping single text where practical.
- Empty states should explain what happened and offer a next action.
- Error states should be localized, preserve user work, and include retry where recovery is possible.
- Long Korean/English mixed subjects, 47+ character sender names, no subject, many participants, many thread messages, many todos, and failed AI/calendar/reply calls are acceptance-relevant states.
- Priority/status must not be color-only; include visible labels.

## Verification design

### Vitest

- Add or extend tests for `DashboardLayout`, `EmailList`, `EmailDetail`, `NetworkGraph`, and page composition.
- Add a small test setup file if needed to type `globalThis.IS_REACT_ACT_ENVIRONMENT` cleanly.
- Keep the existing `NetworkGraph` tooltip sanitization regression.

### Playwright

- Add `@playwright/test`, `playwright.config.ts`, and E2E tests under `frontend/tests/e2e/`.
- Mock backend routes for deterministic browser assertions.
- Cover desktop and mobile viewport acceptance points:
  - local brand logo renders;
  - desktop sidebar/header/main workspace render;
  - inbox loading, empty, error, populated, search, selected-row states;
  - detail no-selection, loaded, AI failure, calendar sync, draft/send states;
  - graph empty/error/populated states and text fallback;
  - no external font endpoint is requested.

## Acceptance-relevant functional points

Track these during implementation and verification:

1. Brand logo and local assets appear in app shell.
2. Desktop shell has sidebar, header, main workspace, and active navigation.
3. Mobile shell has compact navigation and no hover-only required controls.
4. Inbox can fetch, search, show loading/error/empty/populated states, and select a message.
5. Selected inbox row is visibly and semantically selected.
6. Detail view keeps no-selection, loading, error, loaded, thread, summary, action, calendar, draft, and send states.
7. Graph remains safe against HTML tooltip injection and has accessible text fallback.
8. Buttons, inputs, and textarea match 40/44px control targets.
9. External font endpoints are not used.
10. Playwright browser assertions cover the redesigned user-facing paths.

## Dependency decision

If #133 has merged before implementation, rebase #132 on the merged dependency state. If #133 is still blocked when #132 implementation starts, repeat the same local dependency cleanup in #132 rather than introducing Playwright on top of known vulnerable production dependencies. Do not downgrade libraries to hide alerts.

## Open risks

- The branding files are raster boards, not clean exported production assets. Implementation should create deterministic local SVG assets from the visible mark rather than referencing board screenshots directly.
- Current branch-level merges remain blocked by org ruleset #128, so delivery may stop at PR-ready evidence until the external ruleset is aligned.
- Playwright installation may add significant dev dependencies. Keep it dev-only and document browser install requirements.
