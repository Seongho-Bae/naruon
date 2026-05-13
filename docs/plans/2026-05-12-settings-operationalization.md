# Settings Operationalization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn the current placeholder settings tabs into real user workflows for personal mailbox configuration and organization-scoped self-hosted runner token management.

**Architecture:** Reuse the existing tenant config aggregate for personal mailbox settings, extending it with missing IMAP/SMTP credential fields and secret masking. Add a small organization-scoped runner-token aggregate with admin-only API endpoints, then wire the existing `/settings` tabs to those APIs while keeping BYOK configuration in the workspace tab.

**Tech Stack:** FastAPI, SQLAlchemy, encrypted model fields, Next.js App Router, TypeScript, existing `apiClient`, pytest.

---

## Task 1: Extend tenant config model and API for real mailbox settings

**Files:**
- Modify: `backend/db/models.py`
- Modify: `backend/api/tenant_config.py`
- Modify: `backend/api/emails.py`
- Modify: `backend/services/email_client.py`
- Test: `backend/tests/test_tenant_config_model.py`
- Test: `backend/tests/test_tenant_config_api.py`

**Step 1: Write failing tests for new personal mailbox fields**

Add tests that assert `imap_username`, `imap_password`, and `smtp_password` are persisted and masked in API responses.

**Step 2: Run tests to verify failure**

Run: `cd backend && DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_tenant_config_api.py tests/test_tenant_config_model.py -q`

Expected: FAIL because fields do not exist.

**Step 3: Implement minimal backend support**

- Add `imap_username`, `imap_password`, `smtp_password` to `TenantConfig`.
- Extend request/response models and masking logic.
- Pass `smtp_password` into the send-email path.

**Step 4: Run tests to verify pass**

Run the same pytest command and confirm PASS.

**Step 5: Commit**

`git add backend/db/models.py backend/api/tenant_config.py backend/api/emails.py backend/services/email_client.py backend/tests/test_tenant_config_api.py backend/tests/test_tenant_config_model.py && git commit -m "feat(settings): add real mailbox credential fields"`

## Task 2: Add organization-scoped runner token aggregate and API

**Files:**
- Modify: `backend/db/models.py`
- Create: `backend/api/runner_config.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_runner_config_api.py`

**Step 1: Write failing tests for runner token endpoints**

Add tests for:
- member GET/POST forbidden
- admin GET returns current runner metadata
- admin POST rotate returns a new raw token and stores masked metadata on subsequent GET

**Step 2: Run test to verify failure**

Run: `cd backend && DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest tests/test_runner_config_api.py -q`

Expected: FAIL because router/model do not exist.

**Step 3: Implement minimal backend support**

- Add `WorkspaceRunnerConfig` model with `workspace_id`, encrypted `registration_token`, `updated_at`.
- Add admin-only `GET /api/runner-config` and `POST /api/runner-config/rotate`.
- Generate tokens with `secrets.token_urlsafe`.

**Step 4: Run test to verify pass**

Run the same pytest command and confirm PASS.

**Step 5: Commit**

`git add backend/db/models.py backend/api/runner_config.py backend/main.py backend/tests/test_runner_config_api.py && git commit -m "feat(settings): add organization runner token endpoints"`

## Task 3: Replace personal settings placeholder UI with real mailbox form

**Files:**
- Modify: `frontend/src/lib/api-client.ts`
- Modify: `frontend/src/app/settings/page.tsx`

**Step 1: Write the minimal failing behavior check**

Define the expected visible workflow:
- personal tab loads current config
- save button posts config
- masked secrets remain masked when unchanged

Verification by direct browser exercise is acceptable because frontend component tests for this repo are sparse.

**Step 2: Implement UI**

- Add a `getCurrentUserId()` helper to `apiClient`.
- Load `/api/config?user_id=<currentUser>`.
- Render IMAP/SMTP fields and save button.
- Reuse `********` masking convention.

**Step 3: Verify locally**

Run:
- `cd frontend && npm run build`
- direct browser/Playwright check against live stack

Expected: PASS.

**Step 4: Commit**

`git add frontend/src/lib/api-client.ts frontend/src/app/settings/page.tsx && git commit -m "feat(settings): replace personal mailbox placeholder with real config form"`

## Task 4: Replace runner placeholder UI with token issuance and scoped explanation

**Files:**
- Modify: `frontend/src/app/settings/page.tsx`

**Step 1: Implement UI**

- Load `/api/runner-config` in admin mode.
- Show current runner metadata and a one-time raw token after rotation.
- Add rotate/regenerate button.
- Keep scope explanation explicit: organization-scoped, not personal, not Naruon-global.

**Step 2: Verify locally**

Run:
- `cd frontend && npm run build`
- direct browser/Playwright check against live stack in admin mode

Expected: PASS.

**Step 3: Commit**

`git add frontend/src/app/settings/page.tsx && git commit -m "feat(settings): replace runner placeholder with token issuance flow"`

## Task 5: End-to-end verification and review loop

**Files:**
- Modify if needed based on review feedback

**Step 1: Run backend verification**

Run: `cd backend && DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python3 -m pytest -q`

**Step 2: Run frontend verification**

Run:
- `cd frontend && npm run build`
- `cd frontend && npm test`
- `cd frontend && npm run lint`

**Step 3: Run direct live UAT**

Verify in live stack:
- personal mailbox form saves successfully
- member cannot rotate runner token
- admin can rotate runner token and see raw token once

**Step 4: Commit final polish**

`git add <files> && git commit -m "fix(settings): polish mailbox and runner workflows"`
