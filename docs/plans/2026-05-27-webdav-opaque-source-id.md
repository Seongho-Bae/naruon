# WebDAV Opaque Source ID Slice

## Goal

Stop exposing sequential WebDAV account primary keys through browser writeback
contracts. WebDAV writeback and self-sent knowledge materialization should use
opaque `webdav_accounts.source_uid` values, matching the CalDAV source-id rule.

## Scope

- Add/backfill `webdav_accounts.source_uid` and a unique index.
- Replace `target_account_id` requests with `target_source_id`.
- Return `source_id` as a string in WebDAV writeback and materialization intent
  responses.
- Keep provider writes out of scope; these endpoints still create intent
  metadata only.
- Keep Strix on direct OpenAI Platform credentials only. Do not use GitHub
  Models.

## Verification

```bash
python3 -m pytest backend/tests/test_webdav_api.py backend/tests/test_bootstrap_db.py -q
cd frontend && npm test -- --run src/app/data/page.test.tsx src/app/tasks/page.test.tsx
```

Browser evidence remains the Data and Tasks E2E screenshots for desktop, mobile,
and mobile-scroll writeback surfaces.
