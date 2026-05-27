# CalDAV Writeback Source Registry Slice

## Goal

Close the production placeholder in `/api/calendar/writeback-intent` by reading
server-authoritative CalDAV source rows from PostgreSQL while keeping Naruon as a
client/control plane, not a calendar host.

## Implementation

- Add `calendar_writeback_sources` with two-word snake-case columns and opaque
  `source_uid` values for browser-visible source ids.
- Scope registry lookup by signed `AuthContext`: members see only their owner
  scope, tenant admins can target same-organization rows, and system admins can
  target any row.
- Return intent metadata only: protocol, provider, ETag/If-Match requirement,
  provenance, and audit event. No provider write is executed in this slice.
- Keep Strix on direct OpenAI Platform credentials only; no GitHub Models path is
  part of this work.

## Verification

```bash
python3 -m pytest backend/tests/test_calendar_api.py backend/tests/test_bootstrap_db.py -q
python3 -m pytest backend/tests/test_calendar_api.py -m postgres -q
```

Screenshots stay covered by the existing Calendar writeback E2E because the
browser contract and signed `Authorization: Bearer` path are unchanged.
