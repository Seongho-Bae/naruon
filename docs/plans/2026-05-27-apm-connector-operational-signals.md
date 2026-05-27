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
- Keep sync lag, provider throttling, writeback conflict, and AI action audit
  signals explicit as `instrumentation_pending` or `intent_only` until
  source-backed events exist.
- Render the signals in Settings with signed bearer API calls and no public
  identity headers.

## Non-Goals

- No IMAP/SMTP/CalDAV/WebDAV provider execution.
- No Naruon-hosted mailbox/storage claim.
- No GitHub Models routing for Strix or security scans.
- No new database objects in this slice.

## Verification

- Backend mocked API tests cover admin/member authorization, unconfigured state,
  configured telemetry, connected runner state, and token non-disclosure.
- Runner WebSocket tests cover manager connect/disconnect metadata without raw
  token leakage.
- Frontend unit tests cover signed API wiring and no client-controlled identity
  headers.
- Browser E2E captures Settings desktop/mobile scroll screenshots for the
  connector/APM panel.
