# 오픈소스 APM 운영 설계

Naruon의 APM은 SaaS 의존 없이 OpenTelemetry, Prometheus, Grafana, Loki,
Tempo로 시작한다. 목표는 릴리스가 실제로 기동되는지, API가 느려지는지,
메일 동기화 워커가 외부 메일 서버 장애를 사용자 요청으로 전파하지 않는지
확인하는 것이다.

## 구성

```text
FastAPI /metrics ─┐
                  ├─ Prometheus ─ Grafana
OTLP traces ─ OTel Collector ─ Tempo ─ Grafana
Docker logs ─ Grafana Alloy ─ Loki ─ Grafana
```

## 로컬 실행

```bash
POSTGRES_PASSWORD=change-me-local-only docker compose up -d --build
curl -fsS http://localhost:8000/healthz
curl -fsS http://localhost:8000/readyz
curl -fsS http://localhost:8000/metrics | grep python_info
curl -fsS http://localhost:9090/-/ready
python3 -m webbrowser http://localhost:3001
```

If common local ports are already occupied, override only the host-facing ports;
container-to-container service names stay unchanged:

```bash
POSTGRES_PASSWORD=change-me-local-only \
BACKEND_HOST_PORT=18000 FRONTEND_HOST_PORT=13000 \
PROMETHEUS_HOST_PORT=19090 GRAFANA_HOST_PORT=13001 \
LOKI_HOST_PORT=13100 TEMPO_HOST_PORT=13200 \
OTEL_GRPC_HOST_PORT=14317 OTEL_HTTP_HOST_PORT=14318 \
docker compose up -d --build
```

PostgreSQL is intentionally not published to the host by default. The API and
worker use `db:5432` on the Compose network, which avoids host-level monitoring
probes creating false `FATAL` authentication noise in release evidence.

## 릴리스 게이트

- `/healthz`는 외부 의존성 없이 프로세스 생존 여부만 확인한다.
- `/readyz`는 PostgreSQL 연결을 확인한다.
- `/metrics`는 Prometheus text format으로 노출된다.
- FastAPI HTTP traces are emitted only when `OTEL_EXPORTER_OTLP_ENDPOINT` is set;
  local Compose sets it to `http://otel-collector:4317` so Tempo receives real
  request traces instead of only documenting a trace path.
- Compose keeps Grafana and Tempo warning visibility enabled. Release log scans
  use `scripts/check_compose_logs.py`, which has an exact allowlist for known
  Grafana 11.5.x and Tempo 2.7.x startup messages while still failing unknown
  warning, deprecated, notice, denied, fatal, or unable logs. Health, Prometheus
  target, and Tempo trace-query evidence are still required to prove the service
  paths.
- 경고, deprecated, fatal, denied, notice 로그는 릴리스 실패로 본다.
- Grafana 기본 계정은 로컬 전용이며 운영에서는 Secret 또는 SSO로 교체한다.

## 운영 원칙

- APM은 장애를 숨기기 위한 대시보드가 아니라 배포 판단 증거다.
- 외부 SaaS로 로그, 메일 본문, 토큰, tenant secret을 내보내지 않는다.
- Naruon API와 메일 워커의 지표는 분리해서 본다. API replica 증가가 메일
  sync 중복 실행으로 이어지면 안 된다.
