# Search DAG API UI Slice

Date: 2026-05-27

## Scope

Implement a small Context Search slice that replaces the static `/search` screen
with signed API-backed search results, reply-tracking metadata, and the existing
sender relationship graph. This is a UI/API-wiring slice only; it does not add a
new provider write path or a new database object.

## Confirmed Inputs

- `backend/api/search.py` already exposes `POST /api/search` and returns
  `thread_id`, `reply_count`, and `score` for email and attachment matches.
- `backend/api/network.py` returns graph edges as `source` and `target`.
- `frontend/src/components/NetworkGraph.tsx` used `from` and `to`, so the UI
  needed an adapter before the backend graph shape could be trusted.
- `frontend/src/components/SearchLayout.tsx` was static mock data before this
  slice.

## Product Research Notes

- Microsoft Search guidance separates result verticals and filters so users can
  narrow large result sets by type/source while preserving permission-aware
  results:
  https://learn.microsoft.com/en-us/microsoftsearch/manage-verticals and
  https://learn.microsoft.com/en-us/microsoftsearch/custom-filters
- Jira's email update flow links replies back to work items using stable issue
  identifiers and mail headers, which supports surfacing `thread_id` and
  `reply_count` in Naruon's search details before implementing deeper agent
  actions:
  https://support.atlassian.com/jira/kb/how-jira-updates-issues-from-email/

## Implementation Plan

1. Search API wiring
   - Call `apiClient.post('/api/search', { query, limit: 8 })`.
   - Preserve the stored `naruon_session_token` as `Authorization: Bearer`.
   - Do not emit public identity headers.
   - Render loading, empty, error, and success states.

2. Reply and thread detail
   - Render `thread_id`, `reply_count`, sender, date, snippet, and score.
   - Provide simple result filters for all/thread/single-result views.

3. Sender DAG surface
   - Keep using `/api/network/graph`.
   - Normalize backend `source/target` edges to vis-network `from/to` edges.
   - Preserve text-only tooltip sanitization.

4. Responsive evidence
   - Add desktop/mobile E2E coverage for `/search`.
   - Capture screenshots and test scroll/overflow on mobile.

## Verification

- `cd frontend && npm test -- src/app/search/page.test.tsx src/components/NetworkGraph.test.tsx`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `cd frontend && LIVE_BASE_URL=http://127.0.0.1:<port> npx playwright test tests/e2e/dashboard-branding.spec.ts --project=desktop -g "context search"`
