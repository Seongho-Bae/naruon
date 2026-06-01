# Self-Sent Knowledge WebDAV Materialization Intent

## Goal

Turn self-sent knowledge ticket tasks into a source-scoped WebDAV/Notes
materialization intent without performing a provider write from the browser or
from an unscoped backend path.

## Contract

- Naruon remains a control plane, not a WebDAV or Notes storage provider.
- The request starts from an opaque `source_task_id`; clients must not submit raw
  email ids, owner ids, organization ids, provider credentials, or target paths.
- The backend verifies the task belongs to the signed session owner and
  organization, and that `source_type` is `self_sent_knowledge`.
- Same-tenant non-self-sent tasks return `422`; other-owner or missing tasks
  return `404`.
- The backend chooses the customer WebDAV source through the existing
  server-authoritative account lookup using opaque `webdav_accounts.source_uid`
  values, the signed session `organization_id`, and persisted
  `writeback_enabled` eligibility. It returns intent metadata only:
  `target_path`, `server_url`, `requires_if_match`, `provenance`,
  `provider_write_executed=false`, and the audit event name.
- Clients may pass `target_source_id`; legacy sequential `target_account_id`
  payloads are rejected.
- Actual DAV `PUT`, ETag negotiation, Notes object synthesis, and provider
  writeback remain future connector execution work.

## Implementation

- Add `POST /api/webdav/knowledge-materialization-intent` behind
  `get_auth_context`.
- Add backend tests for successful intent, required task id, other-owner 404,
  non-self-sent 422, no WebDAV account 422, signed bearer acceptance, and service
  source-type rejection.
- Add a Tasks workspace subsection for self-sent knowledge tasks. It calls the
  intent endpoint with the stored `naruon_session_token` bearer path through
  `apiClient`, and displays the planned target without claiming execution.
- Extend Playwright mocks and screenshots for desktop/mobile/mobile-scroll
  evidence.

## Verification

```bash
python3 -m pytest backend/tests/test_webdav_api.py -q
```

```bash
cd frontend
npm test -- --run src/app/tasks/page.test.tsx
```

Browser evidence to inspect:

- `self-sent-knowledge-webdav-intent-desktop.png`
- `self-sent-knowledge-webdav-intent-mobile.png`
- `self-sent-knowledge-webdav-intent-mobile-scroll.png`

## Governance

- Strix follows the current provider governance contract: the approved default
  is the validated org-secret Vertex AI model `vertex_ai/gemini-2.5-flash`,
  while direct OpenAI GPT-5.4+ remains explicit-only through
  `STRIX_OPENAI_API_KEY`.
- GitHub Models, `github.token`, generic `LLM_API_KEY`, arbitrary
  Gemini/Vertex fallback, GPT-4o, and GPT-4.1 are not valid Strix routes.
