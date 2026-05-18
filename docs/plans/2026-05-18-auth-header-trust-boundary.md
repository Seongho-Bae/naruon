<!-- markdownlint-disable MD013 -->

# Auth Header Trust Boundary Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strix가 지적한 개발용 `X-User-*` 헤더 인증 우회를 제거하고, 공개 HTTP 요청이 클라이언트 제공 identity/role/organization 값을 인증 수단으로 쓰지 못하게 한다.

**Architecture:** `backend/api/auth.py`는 서버가 명시적으로 `TRUST_DEV_HEADERS`와 `DEV_AUTH_TOKEN`을 설정하고 요청이 `X-Dev-Auth-Token`을 제시한 경우에만 개발용 identity 헤더를 해석한다. FastAPI 엔드포인트 테스트는 production dependency가 아니라 `backend/tests/conftest.py`의 테스트 전용 dependency override로 기존 헤더 기반 fixture를 유지한다. Production OIDC/Keycloak/Casdoor 검증은 별도 후속 slice로 남긴다.

**Tech Stack:** FastAPI dependency injection, Pydantic Settings, pytest, Strix required security gate.

---

## Source finding

- PR #202 Strix check run `76433564514` reported `Authentication Bypass and Privilege Escalation via Trusting Development Headers`.
- Root cause: `build_auth_context()` accepted `X-User-Id` and `X-Organization-Id` from any client, while `DEBUG` or `TRUST_DEV_HEADERS` could also promote `X-User-Role`.
- Security requirement: public `X-User-*` headers alone must never establish identity, organization, or role.

## Files

- Modify: `backend/api/auth.py`
- Modify: `backend/core/config.py`
- Modify: `backend/tests/test_auth_real.py`
- Create: `backend/tests/conftest.py`
- Modify: `ARCHITECTURE.md`
- Modify: `docs/operations/auth-key-management.md`
- Modify: `CHANGELOG.md`

## Task 1: RED tests for unsigned header rejection

- [x] Add regression tests proving `DEBUG=True` does not trust unsigned `X-User-*` headers.
- [x] Add regression tests proving `TRUST_DEV_HEADERS=True` alone is insufficient without a configured token.
- [x] RED evidence:

```bash
PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests/test_auth_real.py::test_debug_mode_does_not_trust_unsigned_identity_headers backend/tests/test_auth_real.py::test_dev_header_trust_requires_configured_token -q
# FAIL: DID NOT RAISE HTTPException
```

## Task 2: Require explicit development auth token

- [x] Add `DEV_AUTH_TOKEN` to settings.
- [x] Require `TRUST_DEV_HEADERS=True` and matching `X-Dev-Auth-Token` before parsing `X-User-Id`, `X-User-Role`, `X-Organization-Id`, or `X-Group-Ids`.
- [x] Stop using `DEBUG` as an auth trust switch.
- [x] Keep invalid/missing dev token errors generic: `401 Authentication required`.

## Task 3: Keep endpoint tests isolated from production auth

- [x] Add `backend/tests/conftest.py` with an opt-in FastAPI dependency
  override fixture for endpoint tests only.
- [x] The override injects the test dev token internally and still reads
  existing test fixture headers, so endpoint tests do not require weakening
  production auth logic.
- [x] Add regression coverage proving auth dependency overrides are absent by
  default, so real authentication regressions cannot be hidden by a global
  autouse test fixture.

## Task 4: Review follow-up regression coverage

- [x] Prove a wrong `X-Dev-Auth-Token` is rejected.
- [x] Prove a matching dev token still fails when `TRUST_DEV_HEADERS=false`.
- [x] Prove a real FastAPI route rejects public `X-User-*` headers when the test-only dependency override is removed.

## Task 5: Strix PR-scope stale context blocker

- [x] Root cause: Strix batch 2 scanned `backend/core/config.py` plus trusted
  backend context from the base branch, so `backend/api/auth.py` appeared with
  the stale vulnerable implementation even though PR #202 changed it.
- [x] Add regression coverage that changed backend context files, including
  filtered non-scannable context such as `backend/requirements.txt`, are copied
  from the PR-head blob when included as context in a different Strix batch.
- [x] Update `scripts/ci/strix_quick_gate.sh` so changed context files fail
  closed on PR-head blob read errors instead of falling back to trusted-base
  content.
- [x] Keep `pull_request_target` unsafe changed paths fail-closed, but do not
  abort regular `pull_request` context construction for unrelated
  unnormalizable filenames that `is_scannable_changed_file()` would already
  ignore.
- [x] RED evidence:

```bash
bash scripts/ci/test_strix_quick_gate.sh
# FAIL: case=pull-request-target-changed-context-uses-pr-head exit code
```

## Verification evidence

```bash
PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest backend/tests/test_auth_real.py -q
# 10 passed

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest backend/tests/test_auth_real.py backend/tests/test_runner_config_api.py backend/tests/test_llm_providers_api.py backend/tests/test_tenant_config_api.py backend/tests/test_emails_api.py backend/tests/test_search.py backend/tests/test_config.py backend/tests/test_calendar_api.py backend/tests/test_runtime_config_api.py backend/tests/test_prompts_api.py backend/tests/test_llm_api.py backend/tests/test_network_api.py backend/tests/test_main.py -q
# 59 passed

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests/test_runner_config_api.py backend/tests/test_llm_providers_api.py backend/tests/test_tenant_config_api.py backend/tests/test_emails_api.py backend/tests/test_search.py backend/tests/test_auth_real.py -q
# 36 passed

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests/test_config.py backend/tests/test_calendar_api.py backend/tests/test_runtime_config_api.py backend/tests/test_prompts_api.py backend/tests/test_llm_api.py backend/tests/test_network_api.py backend/tests/test_main.py -q
# 19 passed

bash scripts/ci/test_strix_quick_gate.sh
# test_strix_quick_gate: PASS

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest backend/tests -q
# 122 passed, 2 skipped; known pre-existing path assertions failed in
# backend/tests/test_apm_observability.py because ../docker-compose.observability.yml
# and ../observability/... are resolved outside the repo root.
```
