# APM Connector Operational Signals Slice

## Goal

Wire the Settings developer surface to server-authoritative open-source APM and
self-hosted connector state without claiming provider execution that does not
exist yet.

## Scope

- Add signed `GET /api/observability/operational-signals` for organization
  admins.
- Return Prometheus and OpenTelemetry runtime configuration from server
  settings/environment.
- Return self-hosted connector registration and active outbound runner
  connection state from the existing runner config table and WebSocket manager.
- Persist connector connect, heartbeat, and disconnect events in
  `connector_signal_events` so Settings can show recent durable APM evidence
  after the runner socket is gone.
- Keep sync lag, provider throttling, writeback conflict, and AI action audit
  signals explicit as `instrumentation_pending` or `intent_only` until
  source-backed events exist.
- Render the signals in Settings with signed bearer API calls and no public
  identity headers.

## Non-Goals

- No IMAP/SMTP/CalDAV/WebDAV provider execution.
- No Naruon-hosted mailbox/storage claim.
- No generic LLM credentials or cross-provider fallback for Strix or security
  scans.
- No queue-depth, provider-throttling, sync-lag, or writeback-conflict
  execution events until source-backed connector jobs emit them.

## Verification

- Backend mocked API tests cover admin/member authorization, unconfigured state,
  configured telemetry, connected runner state, durable connector history, and
  token non-disclosure.
- Runner WebSocket tests cover manager connect/touch/disconnect event capture
  without raw token leakage.
- PostgreSQL bootstrap coverage asserts `connector_signal_events` and its
  scope/time index use two-word `snake_case` names; run
  `python3 -m pytest backend/tests/test_bootstrap_db.py backend/tests/test_observability_api.py -m postgres -q`
  against a pgvector PostgreSQL smoke database before merge.
- Frontend unit tests cover signed API wiring and no client-controlled identity
  headers.
- Browser E2E captures Settings desktop/mobile scroll screenshots for the
  connector/APM panel and recent connector signal timeline.
