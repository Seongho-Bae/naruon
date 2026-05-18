<!-- markdownlint-disable MD013 -->

# Auth Header Trust Boundary Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strix가 지적한 개발용 `X-User-*` 헤더 인증 우회를 제거하고, 공개 HTTP 요청이 클라이언트 제공 identity/role/organization 값을 인증 수단으로 쓰지 못하게 한다.

**Architecture:** `backend/api/auth.py`는 서버가 `RUNTIME_ENVIRONMENT=local|development|test`, `TRUST_DEV_HEADERS=true`, 32자 이상 `DEV_AUTH_TOKEN`을 명시적으로 설정하고 요청이 `X-Dev-Auth-Token`을 제시한 경우에만 개발용 identity 헤더를 해석한다. `admin` 같은 user id는 더 이상 관리자 role을 암시하지 않으며, 관리자 권한은 token gate 뒤의 명시적 trusted role header에서만 온다. FastAPI 엔드포인트 테스트는 production dependency가 아니라 `backend/tests/conftest.py`의 테스트 전용 dependency override로 기존 헤더 기반 fixture를 유지한다. Production OIDC/Keycloak/Casdoor 검증은 별도 후속 slice로 남긴다.

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

## Task 6: Strix hardcoded fallback encryption key blocker

- [x] Root cause: `backend/db/models.py` used a static `FALLBACK_KEY` whenever
  `ENCRYPTION_KEY` was missing and `DEBUG=true`, so debug mode could encrypt
  sensitive fields with a repository-known Fernet key.
- [x] Add a regression test proving `get_fernet()` still rejects a missing
  `ENCRYPTION_KEY` when `DEBUG=true`.
- [x] Remove the fallback Fernet key and require explicit key configuration in
  every runtime mode.
- [x] Update auth/key management and architecture docs to state that encrypted
  secret fields have no code fallback key.
- [x] RED evidence:

```bash
python3 -m pytest backend/tests/test_tenant_config_model.py::test_get_fernet_requires_encryption_key_even_when_debug_enabled
# FAIL: DID NOT RAISE <class 'RuntimeError'>
```

## Task 7: Strix development header runtime hardening blocker

- [x] Root cause: 최신 Strix run `26011987560`은 현재 PR head에서도 개발용
  header auth가 production misconfiguration으로 활성화될 수 있고,
  `user_id == "admin"` fallback이 `organization_admin`으로 승격되는 경로를
  critical CWE-287로 보고했다.
- [x] Add regression coverage proving a matching dev token is rejected when
  `RUNTIME_ENVIRONMENT=production`.
- [x] Add regression coverage proving weak development tokens are rejected even
  when the local/test header path is enabled.
- [x] Add regression coverage proving `X-User-Id: admin` without an explicit
  trusted role header defaults to `member`.
- [x] Require `RUNTIME_ENVIRONMENT` to be `local`, `development`, or `test`, a
  configured 32+ character `DEV_AUTH_TOKEN`, and `TRUST_DEV_HEADERS=true` before
  accepting development identity headers.
- [x] Remove the hardcoded `admin` user-id role fallback.
- [x] RED evidence:

```bash
PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests/test_auth_real.py::test_admin_user_id_without_explicit_role_defaults_to_member backend/tests/test_auth_real.py::test_dev_header_trust_is_rejected_in_production_environment backend/tests/test_auth_real.py::test_dev_header_trust_requires_strong_token -q
# 3 failed
```

## Verification evidence

```bash
PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest backend/tests/test_auth_real.py -q
# 13 passed

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest backend/tests/test_auth_real.py backend/tests/test_runner_config_api.py backend/tests/test_llm_providers_api.py backend/tests/test_tenant_config_api.py backend/tests/test_emails_api.py backend/tests/test_search.py backend/tests/test_config.py backend/tests/test_calendar_api.py backend/tests/test_runtime_config_api.py backend/tests/test_prompts_api.py backend/tests/test_llm_api.py backend/tests/test_network_api.py backend/tests/test_main.py -q
# 62 passed

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests/test_runner_config_api.py backend/tests/test_llm_providers_api.py backend/tests/test_tenant_config_api.py backend/tests/test_emails_api.py backend/tests/test_search.py backend/tests/test_auth_real.py -q
# 36 passed

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests/test_config.py backend/tests/test_calendar_api.py backend/tests/test_runtime_config_api.py backend/tests/test_prompts_api.py backend/tests/test_llm_api.py backend/tests/test_network_api.py backend/tests/test_main.py -q
# 19 passed

bash scripts/ci/test_strix_quick_gate.sh
# test_strix_quick_gate: PASS

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests/test_tenant_config_model.py -q
# 3 passed

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests/test_auth_real.py::test_admin_user_id_without_explicit_role_defaults_to_member backend/tests/test_auth_real.py::test_dev_header_trust_is_rejected_in_production_environment backend/tests/test_auth_real.py::test_dev_header_trust_requires_strong_token -q
# 3 passed

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests -q
# 2 failed, 126 passed, 2 skipped; known pre-existing path assertions failed in
# backend/tests/test_apm_observability.py because ../docker-compose.observability.yml
# and ../observability/... are resolved outside the repo root.
```
