# Source-Thread Sender DAG Slice

## Goal

Search detail must show what a sender means to the signed-in user in the exact
source email/thread context, so the agent can choose a next action from durable
ontology evidence instead of a global, unscoped relationship graph.

## Scope

- Persist sender relationship provenance on `sender_relationships` with
  `source_message_id` and `source_thread_id`.
- Backfill existing databases with idempotent column/index SQL and replace the
  old user/sender-only uniqueness with owner/source-aware uniqueness.
- Return `/api/ontology/relationships` only for the signed session owner and
  organization, with optional `source_message_id` and `source_thread_id`
  filters.
- Include `source_message_id` in `/api/search` results so the frontend can load
  the matching sender DAG without exposing new sequential database ids.
- Render a Search detail sender DAG panel that shows relationship type,
  confidence, next action, and source/thread provenance.

## External best-practice inputs checked

- W3C PROV models provenance around entities, activities, agents, and qualified
  relationships. This slice keeps the relationship tied to the source email and
  thread entity instead of presenting a global sender label as current evidence.
  Source: https://www.w3.org/TR/prov-o/
- Schema.org `potentialAction` provides a lightweight precedent for attaching
  possible next actions to an entity. Naruon keeps this as deterministic
  `next_action` metadata, not autonomous provider mutation.
  Source: https://schema.org/potentialAction

## Implemented capture slice

- Add signed `POST /api/ontology/relationships/capture-source`.
- The endpoint accepts a `source_message_id`, re-reads the source `Email` row
  under the signed owner and organization scope, derives the thread id
  server-side, and writes/updates `sender_relationships` through the existing
  ontology service.
- The browser sends only the source message id from the selected Search result.
  It does not submit public identity headers, relationship labels, confidence
  scores, or provider write claims.
- Search detail now shows a `발신자 관계 캡처` action when the current source has
  no DAG evidence. The returned relationship immediately replaces the empty
  state and shows the next action.

## Non-Goals

- No provider writeback.
- No GitHub Models path.
- No mailbox data sovereignty change: Naruon stores ontology metadata and
  source references only for the connected customer-owned mail context.

## Verification

- Backend ontology API/pipeline/search/bootstrap tests.
- Frontend Search route unit test proving signed-session ontology requests and
  absence of public identity headers.
- Playwright desktop/mobile Search screenshots with scroll checks.
- Real PostgreSQL bootstrap/smoke for DB-affecting schema changes before merge
  evidence is complete.
