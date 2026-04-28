# O3: Finalize Tenant Config Refactoring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix `import_fixtures.py` script to properly pass `openai_api_key` to `generate_embeddings` and add a dummy authentication dependency `get_current_user` to prevent IDOR in endpoints.

**Architecture:** 
- Add `get_current_user` dependency in `backend/api/auth.py` that reads the `X-User-Id` header (defaults to "default").
- Protect endpoints in `api/tenant_config.py`, `api/search.py`, `api/network.py`, `api/llm.py`, and `api/emails.py` by ensuring the requested `user_id` matches the authenticated `current_user`.
- Update `backend/import_fixtures.py` to read `OPENAI_API_KEY` from the environment and pass it to `generate_embeddings`.

**Tech Stack:** FastAPI, Python, SQLAlchemy

---

### Task 1: Create Dummy Authentication Dependency

**Files:**
- Create: `backend/api/auth.py`

**Step 1: Write implementation**

Create `backend/api/auth.py` with the following:
```python
from fastapi import Header

async def get_current_user(x_user_id: str | None = Header(None, alias="X-User-Id")) -> str:
    """
    Dummy authentication dependency.
    Extracts the user ID from the X-User-Id header.
    Defaults to "default" if not provided.
    """
    return x_user_id or "default"
```

---

### Task 2: Protect Tenant Config Endpoints

**Files:**
- Modify: `backend/api/tenant_config.py`

**Step 1: Update implementation**
Add import for `get_current_user` and `HTTPException`:
```python
from fastapi import APIRouter, Depends, HTTPException
...
from api.auth import get_current_user
```
Update `create_or_update_config` and `get_config` to use the dependency and enforce authorization.

---

### Task 3: Protect Other API Endpoints

**Files:**
- Modify: `backend/api/search.py`
- Modify: `backend/api/network.py`
- Modify: `backend/api/llm.py`
- Modify: `backend/api/emails.py`

**Step 1: Update implementation**
For each endpoint taking `user_id`, add `current_user: str = Depends(get_current_user)` and raise 403 if `user_id` is provided but does not match `current_user`. Replace `user_id or "default"` with `current_user`.

---

### Task 4: Fix import_fixtures.py Script

**Files:**
- Modify: `backend/import_fixtures.py`

**Step 1: Update implementation**
Read `OPENAI_API_KEY` using `os.environ.get("OPENAI_API_KEY")` and pass it to `generate_embeddings` calls.

---

### Task 5: Verification and PR

**Step 1: Run linter/typecheck**
Ensure no syntax or type errors.

**Step 2: Commit, Push and PR**
Commit the changes, push to branch, and create a PR to merge.