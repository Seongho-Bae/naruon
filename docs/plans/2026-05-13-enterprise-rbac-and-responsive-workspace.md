# Enterprise RBAC and Responsive Workspace Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a real enterprise-ready RBAC foundation and fix workspace responsiveness so the product matches the intended SaaS operating model and the provided UI design constraints.

**Architecture:** Introduce a small but real authorization context around platform/organization/group/user scopes without breaking existing flows, then adjust the workspace shell so navigation and the relationship graph behave correctly across laptop zoom/resolution constraints. Keep compatibility fallbacks for the current header-based auth while preparing the backend for future Keycloak/Casdoor claims.

**Tech Stack:** FastAPI, SQLAlchemy, Next.js App Router, TypeScript, existing workspace shell, pytest, Playwright.

---

## Task 1: Formalize auth context and scoped roles

**Files:**
- Modify: `backend/api/auth.py`
- Modify: `backend/db/models.py`
- Test: `backend/tests/test_auth_real.py`
- Test: `backend/tests/test_runner_config_api.py`

**Step 1: Write failing tests**
- Add tests that define current role behavior for `platform_admin`, `organization_admin`, `group_admin`, `member`.
- Add tests that organization-scoped resources do not accept cross-scope access.

**Step 2: Run test to verify failure**
Run: `cd backend && DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_auth_real.py tests/test_runner_config_api.py -q`
Expected: FAIL because role model is not formalized.

**Step 3: Implement minimal auth context**
- Add an `AuthContext` shape in `backend/api/auth.py` or equivalent helpers.
- Preserve current header auth fallback for local/dev.
- Encode clear scope derivation rules for organization and group access.

**Step 4: Run tests to verify pass**
Run the same pytest command.
Expected: PASS.

**Step 5: Commit**
`git add backend/api/auth.py backend/db/models.py backend/tests/test_auth_real.py backend/tests/test_runner_config_api.py && git commit -m "feat(auth): add scoped enterprise auth context"`

## Task 2: Clarify settings scope and account ownership in UI/API

**Files:**
- Modify: `frontend/src/app/settings/page.tsx`
- Modify: `backend/api/tenant_config.py`
- Test: `backend/tests/test_tenant_config_api.py`

**Step 1: Write failing test / expected behavior**
- Define expected ownership validation for personal mailbox settings.
- Define explicit copy in settings UI for personal vs organization scope.

**Step 2: Run backend test to verify any mismatch**
Run: `cd backend && DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_tenant_config_api.py -q`
Expected: red on missing scoped behavior or copy mismatch if added.

**Step 3: Implement minimal scope fixes**
- Ensure mailbox settings remain user-owned.
- Tighten API messages and UI labels if needed.

**Step 4: Verify**
- `cd backend && DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_tenant_config_api.py -q`
- `cd frontend && npm run build && npm run lint`

**Step 5: Commit**
`git add frontend/src/app/settings/page.tsx backend/api/tenant_config.py backend/tests/test_tenant_config_api.py && git commit -m "fix(settings): clarify personal mailbox ownership scope"`

## Task 3: Add sidebar scroll and preserve insight visibility

**Files:**
- Modify: `frontend/src/components/DashboardLayout.tsx`
- Test: `frontend/src/components/DashboardLayout.test.tsx`

**Step 1: Write/adjust failing tests**
- Add expectation that sidebar content is scrollable when vertical space is constrained.
- Add expectation that `오늘의 인사이트` remains reachable without 50% zoom hacks.

**Step 2: Run test to verify failure**
Run: `cd frontend && npm test -- DashboardLayout.test.tsx`
Expected: FAIL.

**Step 3: Implement minimal responsive fix**
- Make the sidebar middle region scroll independently.
- Keep footer/insight widget visible or reachable via scroll.
- Avoid collapsing the entire workspace into unusable layouts on laptop viewports.

**Step 4: Verify**
Run: `cd frontend && npm test -- DashboardLayout.test.tsx && npm run build && npm run lint`
Expected: PASS.

**Step 5: Commit**
`git add frontend/src/components/DashboardLayout.tsx frontend/src/components/DashboardLayout.test.tsx && git commit -m "fix(frontend): add sidebar scrolling for constrained workspace heights"`

## Task 4: Make relationship graph responsive to viewport/zoom constraints

**Files:**
- Modify: `frontend/src/components/NetworkGraph.tsx`
- Test: `frontend/src/components/NetworkGraph.test.tsx`

**Step 1: Write failing test**
- Add or extend a test proving the graph container recomputes layout/fit when its viewport changes.

**Step 2: Run test to verify failure**
Run: `cd frontend && npm test -- NetworkGraph.test.tsx`
Expected: FAIL.

**Step 3: Implement minimal fix**
- Add resize handling and a safe `fit()` or equivalent vis-network resize path.
- Ensure graph width/height is not hard-coded in a way that ignores zoomed or constrained layouts.

**Step 4: Verify**
Run: `cd frontend && npm test -- NetworkGraph.test.tsx && npm run build && npm run lint`
Expected: PASS.

**Step 5: Commit**
`git add frontend/src/components/NetworkGraph.tsx frontend/src/components/NetworkGraph.test.tsx && git commit -m "fix(frontend): make relationship graph responsive to viewport changes"`

## Task 5: Full verification and review loop

**Files:**
- Modify as needed from review feedback

**Step 1: Run backend suite**
Run: `cd backend && DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest -q`

**Step 2: Run frontend suite**
Run: `cd frontend && npm test && npm run build && npm run lint`

**Step 3: Run direct browser UAT**
- Verify settings roles and scopes
- Verify sidebar scroll on constrained viewport
- Verify graph responsiveness

**Step 4: Commit final polish**
`git add <files> && git commit -m "fix(workspace): polish enterprise auth and responsive shell"`
