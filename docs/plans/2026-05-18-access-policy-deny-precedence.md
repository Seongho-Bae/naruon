# Access Policy Deny Precedence Slice

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the first pure domain service for Naruon's RBAC + ABAC policy boundary so ABAC denials always win over role/group allows.

**Architecture:** Keep the first slice I/O-free and testable. `services.access_policy.evaluate_access` evaluates a request and resource policy with the ubiquitous terms `AccessRequest`, `ResourcePolicy`, and `AccessDecision`. Denial order is explicit: organization, data region, consent, ownership/delegation, then RBAC role/group allow. This prepares mailbox/search/calendar integration without coupling the rule model to today's header-derived dev auth or FastAPI settings import graph.

**Tech Stack:** Python dataclasses, existing `api.auth.RoleName`, pytest.

---

## Source gap

- `docs/plans/2026-05-17-north-star-platform-roadmap.md` requires Keycloak/Casdoor-ready app policy with RBAC + ABAC + delegation + sovereignty.
- The same roadmap requires ABAC denial precedence over RBAC allow for data region, delegation, consent, and resource ownership.
- `backend/api/auth.py` currently builds scoped auth context, but there was no pure policy service for resource decisions.

## Bounded context and ubiquitous language

- **AccessRequest:** authenticated actor claims needed for a resource decision.
- **ResourcePolicy:** resource-side ownership, organization, data-region, consent, delegation, role, and group requirements.
- **AccessDecision:** final allow/deny plus a stable reason string for future audit logs.

## Task 1: Data-region denial beats platform-admin role allow

- [x] **Step 1: Write failing test**

  `backend/tests/test_access_policy.py` requires a `platform_admin` with an RBAC allow to be denied when request and resource data regions differ.

- [x] **Step 2: Verify RED**

  Focused pytest failed because `services.access_policy` did not exist.

- [x] **Step 3: Implement minimal domain service**

  `backend/services/access_policy.py` adds immutable dataclasses and `evaluate_access`.

## Task 2: Ownership, consent, and delegation precedence

- [x] **Step 1: Write failing tests**

  Tests require non-owner access without delegation and missing consent to be denied even when role/group checks would pass.

- [x] **Step 2: Implement minimal denial ordering**

  `evaluate_access` checks consent and owner/delegation before RBAC role/group allow.

## Acceptance evidence

- RED: `PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_access_policy.py -q` failed with `ModuleNotFoundError: No module named 'services.access_policy'` before implementation.
- GREEN: `PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_access_policy.py -q` passed with 4 tests after initial implementation.
- Review-fix regression: `PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_access_policy.py tests/test_auth_real.py tests/test_calendar_api.py tests/test_runner_config_api.py tests/test_release_governance.py -q` passed with 30 tests after adding organization-denial coverage and removing API-layer coupling.
- Review follow-up: DDD subagent found the first implementation imported `RoleName` from `api.auth` and lacked direct organization-denial coverage. The policy module now owns pure `PolicyRoleName`/`DecisionReason` literals and the test suite covers `organization_denied` explicitly.
