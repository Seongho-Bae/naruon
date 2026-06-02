# WebDAV If-Match Source Evidence Slice

## Verified gap

- `frontend/branding/naruon-ux-mockup-7.png` shows Data as an operational
  document store, ingestion, embedding, and quality workspace with source
  status rather than static copy.
- `docs/plans/2026-05-27-data-webdav-writeback-intent-ui.md` requires current
  ETag state before WebDAV writeback intent, but `/api/webdav/accounts` only
  returned `source_id`, `display_label`, and `writeback_enabled`.
- The Data UI already expected an optional `etag` and rendered
  `etag=missing` when the backend omitted it, so the operator could not tell
  whether an If-Match writeback would use a current provider ETag.
- RFC 4918 describes WebDAV clients using entity tags in `If-Match` headers to
  avoid lost updates, which matches Naruon's intent-only conflict boundary:
  https://www.rfc-editor.org/rfc/rfc4918

## Implemented slice

- Add nullable `webdav_accounts.etag_value` as a two-word snake-case source
  evidence column.
- Include `etag` in `/api/webdav/accounts` without exposing provider URLs,
  usernames, credentials, or sequential `account_id` values.
- Include `if_match` in `/api/webdav/writeback-intent` and self-sent knowledge
  materialization intent responses for the selected source.
- Keep `requires_if_match=true`, `provider_write_executed=false`, and
  `provenance=server-authoritative`; this slice still does not execute provider
  writes.
- Update frontend and E2E mocks so screenshots prove the Data workspace shows
  source ETag and selected intent If-Match evidence.

## Verification

```bash
python -m pytest tests/test_webdav_api.py tests/test_bootstrap_db.py -q
```

```bash
npm test -- src/app/data/page.test.tsx
```

Responsive browser evidence should cover:

- `data-webdav-writeback-intent-desktop.png`
- `data-webdav-writeback-intent-mobile.png`
- `data-webdav-writeback-intent-mobile-scroll.png`
- mobile hamburger drawer sanity after Data navigation
