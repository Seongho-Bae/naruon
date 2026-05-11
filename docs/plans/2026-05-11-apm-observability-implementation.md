# Open Source APM & Observability Implementation Plan

## Overview
Implement OpenTelemetry, Prometheus, Grafana, Loki, and Tempo for Open Source Application Performance Monitoring (APM).

## Reference
- Target Issue: #135 (Closed for design, but we will reopen/implement)

## Architecture
- **Grafana**: Dashboards and visualization.
- **Prometheus**: Metrics backend.
- **Loki**: Log aggregation.
- **Tempo**: Distributed tracing.
- **Alloy / OpenTelemetry Collector**: Receive traces/metrics from FastAPI/Next.js and route to backends.

## Tasks
1. Create `docker-compose.observability.yml` to provision Grafana, Prometheus, Loki, and Tempo.
2. Update backend FastAPI application to include OpenTelemetry instrumentation.
   - `opentelemetry-instrumentation-fastapi`
   - `opentelemetry-exporter-otlp`
3. Update frontend Next.js to expose basic metrics or tracing if applicable.
4. Set up Grafana provisioning (Datasources for Prometheus, Loki, Tempo).
5. Verify via live tests that the stack comes up and endpoints return 200 OK.
