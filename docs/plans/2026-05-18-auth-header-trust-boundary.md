<!-- markdownlint-disable MD013 -->

# Auth Header Trust Boundary Remediation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strix가 지적한 개발용 `X-User-*` 헤더 인증 우회를 제거하고, 공개 HTTP 요청이 클라이언트 제공 identity/role/organization 값을 인증 수단으로 쓰지 못하게 한다.

**Architecture:** `backend/api/auth.py`의 runtime FastAPI dependency는 공개 `X-User-*`, `X-Organization-*`, `X-Group-*`, `X-Dev-Auth-Token` 헤더를 더 이상 인증 material로 해석하지 않고 fail-closed 한다. FastAPI 엔드포인트 테스트는 production dependency가 아니라 `backend/tests/conftest.py`의 테스트 전용 dependency override로 기존 헤더 기반 fixture를 유지한다. Production OIDC/Keycloak/Casdoor 검증은 별도 후속 slice로 남긴다.

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

## Task 2: Superseded development-token mitigation

- [x] Initial mitigation added an explicit development-token gate.
- [x] Later Strix review showed any mutable runtime switch for public identity
  headers inside production code remained too risky, so Task 8 superseded this
  with complete runtime removal of the development-header auth path.
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
- [x] The intermediate runtime/environment/token gate was superseded by Task 8,
  which removed the development-header identity path from production code.
- [x] Remove the hardcoded `admin` user-id role fallback.
- [x] RED evidence:

```bash
PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests/test_auth_real.py::test_admin_user_id_is_rejected_without_verified_identity_provider backend/tests/test_auth_real.py::test_dev_header_trust_is_rejected_in_production_environment backend/tests/test_auth_real.py::test_dev_header_trust_requires_strong_token -q
# 3 failed
```

## Task 8: Strix development header production-code separation blocker

- [x] Root cause: 최신 Strix run `26013001731`은 defaults/token/runtime gate가
  있어도 production artifact 안에 mutable environment 설정으로 다시 켤 수
  있는 development-header auth path가 남아 있다고 보았다.
- [x] Add RED regression coverage proving even fully enabled local dev flags and
  matching `X-Dev-Auth-Token` cannot authenticate the runtime dependency or a
  real HTTP route.
- [x] Make `backend/api/auth.py` fail closed until verified OIDC/JWT/session
  claims are implemented, so public headers cannot forge identity, role,
  organization, group, or workspace scope.
- [x] Move endpoint fixture identity to the explicit pytest dependency override
  in `backend/tests/conftest.py`, constructing `AuthContext` directly instead of
  calling production `build_auth_context()`.
- [x] RED evidence:

```bash
PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests/test_auth_real.py::test_runtime_auth_rejects_dev_headers_even_when_local_flags_enabled backend/tests/test_auth_real.py::test_http_route_rejects_dev_token_and_forged_role_even_when_flags_enabled -q
# 2 failed: runtime dependency accepted forged headers; HTTP route reached DB and returned 500 instead of 401.
```

## Task 9: Strix verified runtime session blocker

- [x] Root cause: 최신 Strix run `26028878019`는 development-header path 제거
  이후에도 runtime `build_auth_context()`가 verified success path 없이 항상
  fail-closed 하는 placeholder라 실제 인증 부재(CWE-287)로 보고했다.
- [x] Add RED regression coverage for HMAC-signed bearer session acceptance and
  forged/tampered/wrong-secret/expired/weak-secret/invalid-role/non-ASCII token
  rejection.
- [x] Add regression coverage proving `sub=admin` does not imply elevated role,
  while an explicit signed `platform_admin` role is accepted.
- [x] Add route-level regression coverage proving signed bearer auth works and
  forged public identity/dev headers are ignored.
- [x] Implement a narrow stdlib HMAC-SHA256 session envelope behind
  `AUTH_SESSION_HMAC_SECRET` until a full OIDC/JWT provider is adopted.
- [x] RED evidence:

```bash
python3 -m pytest -q backend/tests/test_auth_real.py
# 9 failed, 16 passed: Settings had no AUTH_SESSION_HMAC_SECRET and get_auth_context() had no authorization parameter.

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest -q backend/tests/test_auth_real.py::test_signed_bearer_session_rejects_non_ascii_token_segment
# FAIL: UnicodeEncodeError escaped instead of returning HTTPException 401.

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest -q backend/tests/test_auth_real.py::test_signed_bearer_session_rejects_non_ascii_claim_values backend/tests/test_auth_real.py::test_signed_bearer_session_rejects_non_finite_expiration
# 2 failed: non-ASCII claim values and NaN exp authenticated instead of failing closed.
```

## Task 10: Strix calendar credential and email IDOR blockers

- [x] Root cause: latest Strix run `26034843236` still found two public API
  trust-boundary defects. `POST /api/calendar/sync` accepted client-provided
  Google credential payloads, and email/search reads did not enforce a persisted
  mailbox owner key.
- [x] Add RED regression coverage proving calendar sync rejects extra
  client-supplied token data and only calls `create_calendar_event()` with a
  server-authoritative credential dependency.
- [x] Add RED regression coverage proving email list, detail, thread, search,
  and network graph query statements include the authenticated user's
  `emails.user_id` scope.
- [x] Remove the development-header bypass settings from runtime configuration,
  add `emails.user_id`, add idempotent local schema backfill/indexing that stamps
  null local rows with `NARUON_IMPORT_USER_ID` or `default`, and stamp fixture
  imports with the same owner value.
- [x] Keep production calendar credential lookup fail-closed until a connector
  registry provides trusted per-user credentials.

## Task 11: Strix frontend identity-header blocker

- [x] Root cause: latest Strix run `26142440689` found that
  `frontend/src/lib/api-client.ts` could synthesize `X-User-Id` from
  `localStorage.naruon_dev_user`, leaving a client-controlled public identity
  header in the browser request path even after backend runtime auth ignored it.
- [x] Add RED regression coverage proving the API client does not emit the
  local-storage development identity header and strips caller-provided public
  identity headers while preserving non-identity custom headers.
- [x] Remove the `naruon_dev_user`/`getCurrentUserId()` fallback from the
  frontend API client, re-scope `getCurrentUserId()` to decode only the stored
  signed-session payload for UI request shaping, remove the legacy dev auth
  switcher, sanitize caller headers, and update frontend E2E CORS mocks plus
  architecture docs to keep fixtures aligned with signed-session authentication.
- [x] RED evidence:

```bash
npm test -- src/lib/api-client.test.ts
# 1 failed: expected headers not to have property "X-User-Id"; received "attacker-selected-user".

npm test -- src/lib/api-client.test.ts
# 1 failed: caller-supplied "X-User-Id" was forwarded.

npm test -- src/lib/api-client.test.ts
# 1 failed: caller-supplied "X-Group-Ids" was forwarded.

npm test -- src/lib/api-client.test.ts
# 1 failed: lowercase caller-supplied "authorization" shadow header survived.
```

## Verification evidence

```bash
PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest -q backend/tests/test_auth_real.py
# 28 passed

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest -q backend/tests/test_auth_real.py backend/tests/test_runner_config_api.py backend/tests/test_calendar_api.py backend/tests/test_config.py
# 44 passed

uvx black --check backend/api/auth.py backend/core/config.py backend/tests/test_auth_real.py
# 3 files would be left unchanged.

uvx ruff check backend/api/auth.py backend/core/config.py backend/tests/test_auth_real.py
# All checks passed.

bash scripts/ci/test_strix_quick_gate.sh
# test_strix_quick_gate: PASS

git diff --check
# pass

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest backend/tests/test_auth_real.py -q
# 16 passed

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest backend/tests/test_auth_real.py backend/tests/test_runner_config_api.py backend/tests/test_llm_providers_api.py backend/tests/test_tenant_config_api.py backend/tests/test_emails_api.py backend/tests/test_search.py backend/tests/test_config.py backend/tests/test_calendar_api.py backend/tests/test_runtime_config_api.py backend/tests/test_prompts_api.py backend/tests/test_llm_api.py backend/tests/test_network_api.py backend/tests/test_main.py -q
# 67 passed

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests/test_runner_config_api.py backend/tests/test_llm_providers_api.py backend/tests/test_tenant_config_api.py backend/tests/test_emails_api.py backend/tests/test_search.py backend/tests/test_auth_real.py -q
# 36 passed

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests/test_config.py backend/tests/test_calendar_api.py backend/tests/test_runtime_config_api.py backend/tests/test_prompts_api.py backend/tests/test_llm_api.py backend/tests/test_network_api.py backend/tests/test_main.py -q
# 19 passed

bash scripts/ci/test_strix_quick_gate.sh
# test_strix_quick_gate: PASS

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests/test_tenant_config_model.py -q
# 3 passed

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests/test_auth_real.py::test_admin_user_id_is_rejected_without_verified_identity_provider backend/tests/test_auth_real.py::test_dev_header_trust_is_rejected_in_production_environment backend/tests/test_auth_real.py::test_dev_header_trust_requires_strong_token -q
# 3 passed

PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 python3 -m pytest backend/tests -q
# 2 failed, 131 passed, 2 skipped; known pre-existing path assertions failed in
# backend/tests/test_apm_observability.py because ../docker-compose.observability.yml
# and ../observability/... are resolved outside the repo root.
```
