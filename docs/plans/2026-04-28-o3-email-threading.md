# Plan: O3 Implement Email Threading

## Context
We need to implement conversation threading so that replies are grouped together, based on the `In-Reply-To` and `References` headers.

## Tasks

### Task 1: Update Database Model
- **File:** `backend/db/models.py`
- **Action:** Add columns `in_reply_to` (String, nullable), `references` (String, nullable), `thread_id` (String, index, nullable) to the `Email` model.
- **Verification:** Ensure the model changes don't break existing tests, and generate/apply a migration if Alembic is used.

### Task 2: Update Email Parser
- **File:** `backend/services/email_parser.py`
- **Action:** Extract `In-Reply-To` and `References` headers when parsing EML. Add these to the resulting `EmailData` dictionary.
- **Verification:** Run parser tests to confirm new fields are extracted.

### Task 3: Implement Threading Service
- **File:** `backend/services/threading_service.py`
- **Action:** Create `assign_thread_id(session, email_data)` that determines the `thread_id` using `in_reply_to` or `references`. If no existing match is found, generate a new one (e.g. from `Message-ID` or a new UUID).
- **Verification:** Add tests for the threading logic.

### Task 4: Update API Endpoints
- **File:** `backend/api/emails.py`
- **Action:** 
  - Call the threading service when ingesting emails.
  - Include `thread_id` in response schemas (`EmailListItem`, `EmailDetailResponse`).
  - Add `in_reply_to` and `references` to `SendEmailRequest` to maintain threads.
- **Verification:** Run API tests.

### Task 5: Frontend Thread Grouping
- **File:** `frontend/src/components/EmailList.tsx` and `frontend/src/components/EmailDetail.tsx`
- **Action:** Update `EmailItem` and `EmailData` interfaces to include the new fields. Group emails by `thread_id` in the list view. Update `EmailDetail` to send `in_reply_to` and `references` when replying.
- **Verification:** Run frontend tests/build to ensure no type errors.

