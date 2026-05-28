# DAV Registry Hardening Phase

## Goal

Stop legacy DAV paths from implying that Naruon owns customer calendar or file
state. Naruon remains a signed client/control plane over customer-owned
CalDAV/CardDAV/WebDAV sources.

## Implemented Slice

- Legacy `CalDavService.determine_writeback_target()` now returns only opaque,
  writeback-eligible `source_id` values and returns `None` when no eligible
  customer source exists. It no longer returns sequential `account_id` values or
  the synthetic `default_system_caldav` fallback.
- `project_folders.folder_uid` is added as the browser-visible WebDAV folder
  identifier. `/api/webdav/folders`, backend mocks, frontend Data types, unit
  mocks, and E2E mocks now use `folder_uid` and stop exposing `folder_id`.
- `project_folders.organization_id` is added and folder lookup is scoped by both
  signed-session `user_id` and `organization_id`, closing the Strix-confirmed
  cross-tenant folder listing finding for principals reused across B2B tenants.
- `/dav` `PUT` now fails closed with `501` until provider-backed source
  selection, capability checks, credential execution, and ETag/If-Match
  semantics exist. It does not fabricate `201 Created` or ETag headers.
- README, AGENTS, and source-of-truth docs record the regression guardrail so
  copied examples do not reintroduce internal id leaks or fake DAV writes.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest \
  backend/tests/test_caldav.py \
  backend/tests/test_dav_api.py \
  backend/tests/test_webdav_api.py \
  backend/tests/test_bootstrap_db.py -q

npm test -- src/app/data/page.test.tsx
npm run lint -- src/components/DataLayout.tsx src/app/data/page.test.tsx tests/e2e/helpers.ts
npm run typecheck
```

The WebDAV folder smoke test includes a real PostgreSQL path when the configured
database is reachable; otherwise it skips with the existing PostgreSQL-unavailable
guard used by other WebDAV smoke tests.
