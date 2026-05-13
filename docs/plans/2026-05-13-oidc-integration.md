# OIDC Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current header-based auth fallback with a real OIDC/JWT validation path suitable for Keycloak or Casdoor while preserving a strict local-only dev mode.

**Architecture:** Introduce verified token parsing on the backend, map claims into the existing `AuthContext`, and add a minimal frontend login/session path that makes `/settings` and future admin pages depend on real claims rather than browser-controlled headers. Keep a small explicit dev-only auth shim for localhost/LAN UAT.

**Tech Stack:** FastAPI, PyJWT/JWK validation, Next.js App Router, existing AuthContext, pytest.

---

## Task 1: Backend token validation contract

**Files:**
- Modify: `backend/core/config.py`
- Modify: `backend/api/auth.py`
- Test: `backend/tests/test_auth_real.py`

**Step 1: Write failing tests**
- Add tests for bearer-token parsing and claim mapping.
- Add tests that invalid/missing signatures are rejected.
- Add tests that dev-header fallback is only allowed when explicit local mode is on.

**Step 2: Run tests to verify failure**
Run: `cd backend && DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_auth_real.py -q`
Expected: FAIL.

**Step 3: Implement minimal backend validation**
- Add OIDC config fields (issuer, audience, jwks url, auth mode).
- Implement JWT/JWK validation.
- Map claims to `AuthContext` fields (`user_id`, `role`, `organization_id`, `group_ids`).

**Step 4: Verify pass**
Run the same pytest command.
Expected: PASS.

**Step 5: Commit**
`git add backend/core/config.py backend/api/auth.py backend/tests/test_auth_real.py && git commit -m "feat(auth): add OIDC token validation and claim mapping"`

## Task 2: Frontend session entrypoint

**Files:**
- Modify: `frontend/src/lib/api-client.ts`
- Create: `frontend/src/app/login/page.tsx`
- Modify: `frontend/src/app/settings/page.tsx`
- Test: frontend build/lint

**Step 1: Implement minimal frontend session path**
- Add a login page that explains OIDC/SSO mode and local dev mode.
- Make `apiClient` send Authorization bearer tokens when present.
- Stop relying on default fake user outside explicit dev mode.

**Step 2: Verify**
Run: `cd frontend && npm test && npm run build && npm run lint`
Expected: PASS.

**Step 3: Commit**
`git add frontend/src/lib/api-client.ts frontend/src/app/login/page.tsx frontend/src/app/settings/page.tsx && git commit -m "feat(frontend): add OIDC session plumbing"`

## Task 3: Wire admin/settings to real claims

**Files:**
- Modify: `backend/api/llm_providers.py`
- Modify: `backend/api/runner_config.py`
- Modify: `frontend/src/app/settings/page.tsx`
- Test: `backend/tests/test_llm_providers_api.py`
- Test: `backend/tests/test_runner_config_api.py`

**Step 1: Update tests first**
- Replace header-only assumptions with claim-driven fixtures.
- Verify org admins can manage org resources, members cannot.

**Step 2: Implement minimal code**
- Switch settings/admin APIs to the new token/claim path.
- Keep dev fallback only for local mode.

**Step 3: Verify**
Run:
- `cd backend && DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_llm_providers_api.py tests/test_runner_config_api.py -q`
- `cd frontend && npm run build && npm run lint`
Expected: PASS.

**Step 4: Commit**
`git add backend/api/llm_providers.py backend/api/runner_config.py backend/tests/test_llm_providers_api.py backend/tests/test_runner_config_api.py frontend/src/app/settings/page.tsx && git commit -m "fix(auth): connect admin settings to real OIDC claims"`

## Task 4: Full verification and release path

**Files:**
- Modify as needed based on review feedback

**Step 1: Run full backend suite**
`cd backend && DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest -q`

**Step 2: Run full frontend suite**
`cd frontend && npm test && npm run build && npm run lint`

**Step 3: Direct browser UAT**
- verify login page
- verify settings access denied without admin claim
- verify dev-local toggle still works only in explicit dev mode

**Step 4: Commit final polish**
`git add <files> && git commit -m "fix(auth): polish OIDC integration flow"`
