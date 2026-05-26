# Phase 12: Application Performance Monitoring (APM) and Security Governance Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Open Source Application Performance Monitoring (APM) via OpenTelemetry and enforce security/GRC rules including RBAC endpoints and authentication.

**Architecture:**
- Add OpenTelemetry SDK instrumentation to FastAPI.
- Complete the APM infrastructure (Prometheus, Loki, Tempo, Grafana) definition in `docker-compose.infra.yml`.
- Implement actual backend dependencies for `get_current_user_role` and enforce RBAC on specific endpoints.
- Address any `Timeout`, `Fatal`, `Warn`, `Denied` suppression to ensure tests pass strictly.

**Tech Stack:** FastAPI, OpenTelemetry, Prometheus, Docker Compose.

---

## Task 1: OpenTelemetry Instrumentation

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/main.py`
- Modify: `backend/tests/test_apm_observability.py`

- [ ] **Step 1: Write a test ensuring `/metrics` is exposed and traces are configurable**
- [ ] **Step 2: Add `opentelemetry-instrumentation-fastapi` and `prometheus-fastapi-instrumentator` to requirements**
- [ ] **Step 3: Wire up `FastAPIInstrumentor.instrument_app(app)` in `main.py`**
- [ ] **Step 4: Verify test passes without warnings**

## Task 2: Grafana & APM Infrastructure Definition

**Files:**
- Modify: `docker-compose.infra.yml`
- Create: `observability/grafana/provisioning/datasources/datasources.yaml`
- Create: `observability/prometheus.yml`
- Create: `observability/tempo.yaml`

- [ ] **Step 1: Write tests ensuring these files exist in `test_apm_observability.py`**
- [ ] **Step 2: Define Loki, Tempo, Prometheus, and Grafana containers in `docker-compose.infra.yml`**
- [ ] **Step 3: Create the config files for the observability stack**
- [ ] **Step 4: Verify tests pass**

## Task 3: RBAC Endpoint Enforcement

**Files:**
- Modify: `backend/api/tenant_config.py`
- Modify: `backend/tests/test_tenant_config_api.py`

- [ ] **Step 1: Write tests asserting non-admins receive 403 Forbidden for admin endpoints**
- [ ] **Step 2: Use `get_current_user_role` to secure `/api/tenant_config/global`**
- [ ] **Step 3: Verify the changes correctly deny access to `member` roles**
