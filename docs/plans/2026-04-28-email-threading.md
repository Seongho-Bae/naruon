# O3: Implement Email Threading Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement email threading functionality in the AI email client to group emails by thread.

**Architecture:** Add `thread_id`, `in_reply_to`, and `references` to the `Email` model. Update `email_parser.py` to extract these headers. Create an endpoint `/api/emails/thread/{thread_id}` to fetch an entire thread. Update `EmailList.tsx` and `EmailDetail.tsx` to support viewing threaded conversations.

**Tech Stack:** FastAPI, SQLAlchemy, React, shadcn/ui

---

### Task 1: Add Threading Fields to Database Model

**Files:**
- Modify: `/Users/seonghobae/opencode_tasks/ai_email_client/backend/db/models.py`

**Step 1: Write the code**
Ensure `thread_id`, `in_reply_to`, and `references` exist in `Email` model.

**Step 2: Commit**
```bash
git add backend/db/models.py
git commit -m "feat: add threading fields to email model"
```

### Task 2: Update Email Parser

**Files:**
- Modify: `/Users/seonghobae/opencode_tasks/ai_email_client/backend/services/email_parser.py`

**Step 1: Write the code**
Ensure parsing logic for `In-Reply-To` and `References` headers exists.

**Step 2: Commit**
```bash
git add backend/services/email_parser.py
git commit -m "feat: extract threading headers in email parser"
```

### Task 3: Create Thread API Endpoint

**Files:**
- Modify: `/Users/seonghobae/opencode_tasks/ai_email_client/backend/api/emails.py`

**Step 1: Write the code**
Ensure `/api/emails/thread/{thread_id}` endpoint is correctly implemented.

**Step 2: Commit**
```bash
git add backend/api/emails.py
git commit -m "feat: add endpoint for email threading"
```

### Task 4: Update Frontend UI

**Files:**
- Modify: `/Users/seonghobae/opencode_tasks/ai_email_client/frontend/src/components/EmailList.tsx`
- Modify: `/Users/seonghobae/opencode_tasks/ai_email_client/frontend/src/components/EmailDetail.tsx`

**Step 1: Write the code**
Ensure `EmailList.tsx` displays thread counts and `EmailDetail.tsx` fetches and shows threaded conversations. Use `shadcn-ui` components appropriately.

**Step 2: Commit**
```bash
git add frontend/src/components/EmailList.tsx frontend/src/components/EmailDetail.tsx
git commit -m "feat: implement threading UI in frontend"
```
