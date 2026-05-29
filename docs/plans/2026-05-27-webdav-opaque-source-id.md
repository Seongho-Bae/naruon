# WebDAV Opaque Source ID Slice

## Goal

Stop exposing sequential WebDAV account primary keys through browser writeback
contracts. WebDAV writeback and self-sent knowledge materialization should use
opaque `webdav_accounts.source_uid` values, matching the CalDAV source-id rule.

## Scope

- Add/backfill `webdav_accounts.source_uid` and a unique index. Legacy rows get
  non-sequential opaque values; the browser-visible id is not derived from
  `account_id`.
- Scope WebDAV source lookup by `organization_id` from the signed session and
  honor persisted `writeback_enabled` eligibility.
- Replace `target_account_id` requests with `target_source_id`.
- Return `source_id` as a string in WebDAV writeback and materialization intent
  responses.
- Verify `/accounts`, `/writeback-intent`, and
  `/knowledge-materialization-intent` omit `account_id` and work through signed
  bearer sessions without public identity headers.
- Keep provider writes out of scope; these endpoints still create intent
  metadata only.
- Keep Strix on the current provider governance contract: validated org-secret
  Vertex AI by default, explicit direct OpenAI only when selected, and no GitHub
  Models.

## Verification

```bash
python3 -m pytest backend/tests/test_webdav_api.py backend/tests/test_bootstrap_db.py -q
cd frontend && npm test -- --run src/app/data/page.test.tsx src/app/tasks/page.test.tsx
```

Browser evidence to inspect:

- `data-webdav-writeback-intent-desktop.png`
- `data-webdav-writeback-intent-mobile.png`
- `data-webdav-writeback-intent-mobile-scroll.png`
- `self-sent-knowledge-webdav-intent-desktop.png`
- `self-sent-knowledge-webdav-intent-mobile.png`
- `self-sent-knowledge-webdav-intent-mobile-scroll.png`
