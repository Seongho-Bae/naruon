# Data WebDAV Writeback Intent UI

## Goal

Wire the Data workspace to Naruon's customer-owned WebDAV writeback-intent
contract so users can inspect source selection and conflict requirements before
AI-organized files or attachments are written back to their own storage.

## Architecture

- Naruon is not a WebDAV storage provider or long-term source of truth.
- Customer WebDAV accounts remain the writeback target.
- The browser calls `POST /api/webdav/writeback-intent` through the signed
  `apiClient` session path.
- The browser chooses optional targets with opaque `target_source_id`; legacy
  sequential `target_account_id` payloads fail closed.
- The UI shows intent, source id, server URL, If-Match requirement, and
  provenance only. It does not claim provider write execution.
- Public identity headers must not be emitted by browser write requests.

## Implementation

- `/data` now exposes a WebDAV writeback intent approval panel.
- The intent panel uses the first connected customer WebDAV account as the
  target source through `webdav_accounts.source_uid` and fails closed when no
  source or signed session is available.
- Data repository cards now use responsive grid tracks so mobile verification
  does not depend on desktop-only three-column layouts.
- Unit and Playwright tests assert signed `Authorization: Bearer` handling and
  absence of public identity headers for `/api/webdav/writeback-intent`.

## Verification

```bash
npm test -- src/app/data/page.test.tsx
```

```bash
LIVE_BASE_URL=http://127.0.0.1:18140 \
  npx playwright test tests/e2e/dashboard-branding.spec.ts \
  --project=desktop -g "data WebDAV"
```

Screenshots to inspect:

- `data-webdav-writeback-intent-desktop.png`
- `data-webdav-writeback-intent-mobile.png`
- `data-webdav-writeback-intent-mobile-scroll.png`
