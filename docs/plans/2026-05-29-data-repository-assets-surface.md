# Data Repository Assets Surface

## Verified Gap

- `frontend/branding/naruon-ux-mockup-7.png` shows Data as a file-oriented
  workspace: document store, file state, metadata, ingestion, embedding, and
  quality panels in one operational surface.
- `docs/plans/2026-05-28-data-quality-surface.md` made repository counts,
  ingestion, embeddings, and quality source-backed, but the document repository
  tab still lacked source-linked file assets derived from actual mail and
  attachment rows.
- The next thin slice should not add Naruon-owned file storage. It should expose
  read-only evidence from customer-owned email attachments and keep WebDAV
  writeback as intent metadata until connector execution can enforce
  capability, consent, and ETag/If-Match.

## External Best-Practice Inputs Checked

- OpenLineage documents jobs, datasets, and runs as consistently identified
  lineage events. This slice keeps stable opaque asset keys and evidence-source
  labels so future ingestion jobs can attach lineage without exposing database
  primary keys. Source: https://openlineage.io/docs/
- Great Expectations treats quality as explicit checks with outcomes. This slice
  keeps file asset state tied to concrete checks: extracted attachment content
  and canonical thread evidence. Source:
  https://docs.greatexpectations.io/
- WebDAV lost-update protection relies on ETag/If-Match semantics. Data remains
  read-only here and continues routing provider writes through existing WebDAV
  intent endpoints with If-Match evidence. Source:
  https://www.rfc-editor.org/rfc/rfc4918

## Implemented Slice

- Extend signed `GET /api/data/quality-surface` with `repository_assets`.
- Derive each asset from existing `attachments` joined to scoped `emails`.
- Return only browser-safe evidence:
  - opaque `asset_key`;
  - sanitized attachment filename and source subject;
  - opaque thread key or `thread_missing`;
  - extracted content character count;
  - captured timestamp from the source email;
  - state based on attachment content and canonical thread evidence;
  - `provider_write_executed=false`.
- Do not expose attachment ids, email ids, raw message ids, raw thread ids,
  message body, provider URLs, usernames, credentials, or WebDAV storage claims.
- Render the Data document repository tab with the recent file/attachment asset
  list before WebDAV writeback intent controls.

## Verification Plan

- Backend mocked tests cover signed-session response shape, opaque identifiers,
  safe display text, and secret/private identifier omission.
- Backend PostgreSQL smoke seeds scoped and rival email/attachment rows and
  proves only signed-scope assets return.
- Frontend unit tests prove the Data page renders repository assets from
  `/api/data/quality-surface` and continues using bearer-session headers without
  public identity headers.
- Browser E2E covers desktop repository asset screenshots plus existing
  pipeline, embedding, quality, mobile scroll, and hamburger checks.

## Follow-Up Roadmap

- Add durable ingestion run and dataset lineage tables only after connector jobs
  emit source-backed run events. New DB names must remain two-word
  `snake_case`.
- Add WebDAV provider write execution only after connector execution can enforce
  source capability, consent, credential reference, remote href, and If-Match.
- Add a file metadata side panel only after source rows carry provider-safe MIME,
  size, and classification evidence.
