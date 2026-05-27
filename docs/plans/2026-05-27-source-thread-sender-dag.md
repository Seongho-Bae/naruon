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
