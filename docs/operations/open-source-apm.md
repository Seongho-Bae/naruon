# Open Source APM and Observability

## 확인된 사실 / Confirmed

- `backend/main.py` wires optional OpenTelemetry FastAPI instrumentation and
  exposes Prometheus `/metrics` only when `ENABLE_PROMETHEUS_METRICS=true`.
- `backend/api/observability.py` exposes signed-session
  `/api/observability/operational-signals` for organization admins. It reports
  Prometheus/OTel configuration, self-hosted connector registration, active
  outbound runner connection state, and the remaining instrumentation gaps
  without executing provider writes.
- `backend/requirements.txt` includes `prometheus-fastapi-instrumentator` and
  OpenTelemetry dependencies used by the FastAPI app.
- `docker-compose.observability.yml`, `docker-compose.apm.yml`, and
  `docker-compose.infra.yml` document local Prometheus/APM stack entry points.
- `docker-compose.live-e2e.yml` proves the image-based smoke path before any APM
  stack is claimed as production-ready.

## 가설 / Hypothesis

- The default open-source APM stack should be OpenTelemetry SDK + Collector,
  Prometheus for metrics, Grafana for dashboards, Loki for logs, and Tempo or
  Jaeger for traces.
- Runtime instrumentation should start with request latency, status code,
  dependency calls, and worker-loop spans, while redacting email body and secret
  values.

## North-star telemetry targets

- Connector heartbeat, version, queue depth, and outbound control-channel health.
- Sync lag per mailbox/calendar/file source, provider throttling, retry budgets,
  and conflict rates.
- Writeback intent lifecycle: selected source, ETag/If-Match requirement,
  provider response class, conflict outcome, and audit event id.
- Tenant/workspace latency, error budget, AI action audit events, and prompt/model
  usage without logging email bodies, secrets, DSNs, or raw provider tokens.

## 도입 기준

- Keep instrumentation and scrape endpoints behind explicit environment
  variables where telemetry can export outside the process. `/metrics` must stay
  disabled by default and enabled only behind a trusted scrape path or reverse
  proxy access policy.
- Keep `/healthz`, `/readyz`, and `/metrics` semantics separate as the stack
  matures.
- Do not claim APM production readiness until a live stack shows trace, metric,
  and log evidence without leaking user email content.

## Remaining gaps

- Persist connector heartbeat history and queue depth beyond the in-process
  runner WebSocket manager.
- Add sync lag, writeback conflict, and AI action audit dashboards fed by
  source-backed connector/provider events.
- Add log and trace redaction tests for email bodies, provider tokens, DSNs, and
  calendar/file descriptions.
