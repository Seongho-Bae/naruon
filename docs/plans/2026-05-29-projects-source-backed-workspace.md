# 2026-05-29 Projects Source-Backed Workspace

## Verified gap

- `frontend/branding/naruon-ux-mockup-5.png` specifies a dense project surface:
  project list, project detail, milestones, decision logs, linked mail,
  documents, and tasks.
- `docs/plans/2026-05-18-project-workspace-menu-roadmap.md` intentionally made
  `/projects` route-oriented and frontend-only. The current route therefore
  still used static project, milestone, and decision examples.
- Existing signed APIs already expose the minimum source evidence needed for a
  small implementation slice:
  - `/api/webdav/folders` for customer-owned project folder boundaries.
  - `/api/tasks` for source-linked ticket tasks and public task ids.
- No project provider write execution exists yet, so this slice must remain a
  read-only workspace view and label `provider_write_executed=false`.

## Implementation scope

1. Replace static `/projects` examples with signed API reads from
   `/api/webdav/folders` and `/api/tasks`.
2. Render project list entries from WebDAV project folders. If no folders exist,
   show a source-linked task backlog fallback instead of pretending seeded
   projects exist.
3. Derive milestone counts from ticket task statuses and keep task ids opaque;
   never expose sequential database ids.
4. Render the decision-log panel as source evidence: project folder boundary and
   ticket workflow evidence. Provider writes stay linked to Data/WebDAV intent
   flows.
5. Add unit and Playwright coverage for signed bearer headers, absence of public
   identity headers, desktop/mobile overflow, mobile scroll, and hamburger menu
   composition.

## Non-goals

- No new project tables or columns.
- No provider writeback execution.
- No browser-side WebDAV/CalDAV mutation.
- No fake decision-log persistence; durable decision objects are a future
  backend slice.

## Verification plan

- `npm test -- src/app/projects/page.test.tsx`
- `npm run typecheck`
- `npm run lint`
- `PLAYWRIGHT_PORT=<port> npm run test:e2e -- --project=desktop -g "source-backed Projects"`
- Inspect captured desktop, mobile scroll, and mobile menu screenshots before
  merge.
