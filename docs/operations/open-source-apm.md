# Open Source APM and Observability

## 확인된 사실 / Confirmed

- `backend/main.py` currently exposes the FastAPI app and routers, but no
  OpenTelemetry instrumentation is wired yet.
- `docker-compose.yml` currently contains db/backend/frontend only; it does not
  run Prometheus, Grafana, Loki, Tempo, Jaeger, or an OpenTelemetry Collector.
- `docker-compose.live-e2e.yml` proves the image-based smoke path before any APM
  stack is claimed as production-ready.

## 가설 / Hypothesis

- The default open-source APM stack should be OpenTelemetry SDK + Collector,
  Prometheus for metrics, Grafana for dashboards, Loki for logs, and Tempo or
  Jaeger for traces.
- Runtime instrumentation should start with request latency, status code,
  dependency calls, and worker-loop spans, while redacting email body and secret
  values.

## 도입 기준

- Add instrumentation behind explicit environment variables.
- Keep `/healthz`, `/readyz`, and `/metrics` semantics separate if those endpoints
  are added later.
- Do not claim APM production readiness until a live stack shows trace, metric,
  and log evidence without leaking user email content.
