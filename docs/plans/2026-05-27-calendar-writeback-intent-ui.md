# Calendar Writeback Intent UI Slice

## Goal

Wire the Calendar workspace to Naruon's customer-owned writeback-intent
contract so users can verify CalDAV/CardDAV/WebDAV source selection, conflict
requirements, provenance, and audit event state without pretending that Naruon
is the calendar server or directly writing provider data from the browser.

## Contract

- Naruon remains a web client/control plane.
- Customer CalDAV/CardDAV/WebDAV accounts remain the source of truth.
- Calendar actions create server-authoritative intent through
  `POST /api/calendar/writeback-intent`.
- The Calendar workspace first loads server-owned source registry rows through
  `GET /api/calendar/writeback-sources`; the browser may pass only the opaque
  `target_source_id`, never owner or capability claims.
- The UI must show `writeback_mode`, `protocol`, `target_source_id`,
  `if_match`, and `audit_event` when the intent is accepted.
- `422` means no customer-owned source is available.
- `409` means ETag/If-Match conflict protection stopped an overwrite.
- Browser requests use the stored `naruon_session_token` as
  `Authorization: Bearer`; public identity headers are not part of this flow.

## Implemented Slice

- `/calendar` now exposes a CalDAV/CardDAV/WebDAV intent check panel.
- The intent panel lists signed-session CalDAV registry sources, initializes an
  eligible write-capable customer source, and lets the user deliberately select
  the opaque target source before posting intent.
- Source cards show provider, protocol, capabilities, persisted ETag state, and
  writeback eligibility so source selection is visible before any intent POST.
- The monthly, weekly, detail, coordination, and candidate calendar tabs all
  render concrete surfaces instead of an inert "under implementation" state.
- Mobile layout keeps the header and monthly grid bounded, and adds bottom safe
  area padding so the fixed workspace navigation does not cover final content.
- Playwright captures desktop, mobile, and mobile-scroll screenshots for the
  writeback intent surface.

## Verification

```bash
npm test -- src/app/calendar/page.test.tsx src/components/EmailDetail.test.tsx src/lib/api-client.test.ts
PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests/test_calendar_api.py -q
npm test -- src/components/mobile-workspace-panels.test.tsx
npm run typecheck
npm run build
LIVE_BASE_URL=http://127.0.0.1:18130 npx playwright test tests/e2e/dashboard-branding.spec.ts --project=desktop -g "calendar writeback"
LIVE_BASE_URL=http://127.0.0.1:18130 npx playwright test tests/e2e/dashboard-flows.spec.ts --project=desktop -g "connects inbox"
```
