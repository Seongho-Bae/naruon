# DAV Source Selection and Conflict UI Phase

## Goal

Close the next verified `docs/plans` and `frontend/branding` gap without
changing Naruon's source-of-truth boundary: Naruon remains a signed web
workspace/control plane over customer-owned CalDAV/CardDAV/WebDAV providers.

## Verified Inputs

- `frontend/branding/naruon-ux-mockup-1.png` shows a dense operational home
  workspace with navigable decisions, tasks, calendar, and mail surfaces rather
  than static hero copy.
- `frontend/branding/naruon-ux-mockup-3.png` shows the Calendar workspace as a
  month/week/detail/coordination/candidate surface with provider-backed
  scheduling states.
- `docs/plans/2026-05-27-calendar-writeback-intent-ui.md` and
  `docs/plans/2026-05-27-data-webdav-writeback-intent-ui.md` already require
  signed source-registry reads, opaque target ids, ETag/If-Match visibility, and
  no direct browser provider writes.
- Subagent audits confirmed that Calendar and Data already call signed intent
  APIs, but Calendar auto-selected the first source and Data collapsed WebDAV
  `409` conflicts into a generic error.

## Implemented Slice

- Calendar source cards are selectable controls. The UI still initializes from
  the first eligible source, but the selected opaque `source_id`, protocol,
  capability list, ETag value, and writeback eligibility are visible before
  `POST /api/calendar/writeback-intent`.
- Data WebDAV source cards are selectable controls. `POST
  /api/webdav/writeback-intent` uses the selected opaque `source_id` and never
  exposes sequential account ids in the browser request.
- WebDAV `409` responses render as If-Match/ETag conflicts so the UI does not
  imply that Naruon overwrote a customer-owned file.
- The mobile hamburger drawer locks background body scroll while open and keeps
  the drawer itself scrollable, matching the branding requirement for usable
  mobile navigation across all primary destinations.
- README and AGENTS guardrails now record this bug pattern so future copied
  Calendar/WebDAV examples do not revert to implicit source selection or generic
  conflict errors.

## Still Future Work

- Real connector/provider write execution remains out of scope until the
  connector can enforce consent, capability, credential reference, remote href,
  and ETag/If-Match checks server-side.
- `CaldavAccount` still needs deeper credential/account registry consolidation
  with `calendar_writeback_sources`; this UI phase did not add provider
  execution.
- WebDAV project folder opaque ids and `/dav` fail-closed mutation behavior are
  handled in `2026-05-28-dav-registry-hardening.md`.

## Verification

```bash
npm test -- src/app/calendar/page.test.tsx src/app/data/page.test.tsx
npm run typecheck
npm run build
npx playwright test tests/e2e/dashboard-branding.spec.ts --project=desktop -g "calendar writeback|data WebDAV"
npx playwright test tests/e2e/mobile-hamburger.spec.ts --project=desktop
```

Screenshots to inspect:

- `calendar-writeback-intent-desktop.png`
- `calendar-writeback-intent-mobile.png`
- `calendar-writeback-intent-mobile-scroll.png`
- `data-webdav-writeback-intent-desktop.png`
- `data-webdav-writeback-intent-mobile.png`
- `data-webdav-writeback-intent-mobile-scroll.png`
- `mobile-hamburger-open.png`
