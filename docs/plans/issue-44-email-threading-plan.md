# Email Threading Implementation Plan

## Task 1: Update DB Model and Schemas
Update the `Email` model in `backend/db/models.py` to include a `thread_id` field.
It should be a String, nullable, with an index for fast lookups.
Update `EmailListItem` and `EmailDetailResponse` in `backend/api/emails.py` to include `thread_id: str | None = None`.

## Task 2: Implement Email Parsing Logic for Threading
Update `EmailData` in `backend/services/email_parser.py` to include `thread_id: str | None`.
Implement logic to extract or generate a `thread_id` from the email headers:
- Extract `In-Reply-To` and `References` headers.
- If `References` exists, use the first ID in the references list as the `thread_id` (this represents the root of the thread).
- If `References` is missing but `In-Reply-To` exists, use `In-Reply-To` as the `thread_id`.
- If both are missing, use the email's own `Message-ID` as the `thread_id`.
Update tests in `backend/tests/test_email_parser.py` to verify this behavior.

## Task 3: Update DB Insertion and Import Logic
Ensure `thread_id` is passed when saving emails to the database.
Check `backend/import_fixtures.py`, `backend/scripts/import_fixtures.py`, and `backend/services/imap_worker.py` (if it creates DB objects). Wait, let's just make sure anywhere `Email(message_id=...)` is instantiated, `thread_id` is also provided.

## Task 4: Fix Tests
Ensure all tests in `backend/tests/` pass. 
Particularly check `test_db.py`, `test_emails_api.py`, `test_import_fixtures.py` to make sure they account for `thread_id`.