# Issue 83: Implement Email Threading

## Context
The user requested to group emails by thread. Some partial implementation exists but it is flawed:
- `backend/db/models.py` has duplicate `thread_id` definitions.
- `backend/api/emails.py` returns emails individually without grouping by thread.
- `EmailList.tsx` shows individual emails instead of threads.

## Tasks

### Task 1: Clean up models.py
- **File**: `backend/db/models.py`
- **Action**: Remove duplicate `thread_id` columns from the `Email` model. Keep only one definition.
- **Spec Compliance**: The model should be valid SQLAlchemy without duplicate column definitions.

### Task 2: Group emails in backend API
- **File**: `backend/api/emails.py`
- **Action**: 
  - Update `EmailListItem` to include an optional `reply_count` integer.
  - Update `get_emails` endpoint to group emails by `thread_id`. It should return the latest email for each thread and set the `reply_count` (number of emails in that thread).
  - Ensure compatibility with SQLite/Postgres by grouping in Python or using portable SQLAlchemy. A simple way: fetch all emails, group by `thread_id` in Python, sort by date descending, and take the top `limit`. Since `limit` was 50, we might need to fetch more or use a window function. For simplicity, we can fetch `limit * 2` and group in Python, or use a proper SQLAlchemy query if possible. The simplest robust way is a subquery or grouping in Python for now.
- **Spec Compliance**: The `/api/emails` endpoint should return unique threads, not individual emails from the same thread.

### Task 3: Update EmailList.tsx
- **File**: `frontend/src/components/EmailList.tsx`
- **Action**:
  - Update `EmailItem` interface to include `reply_count?: number`.
  - In the email list render, if `reply_count` is > 1, show a small badge or text indicating the number of messages in the thread (e.g., `Badge` component with text `${email.reply_count} msgs`).
- **Spec Compliance**: The UI must use `shadcn-ui` Badge component to indicate thread count.

### Task 4: Ensure email_parser.py works
- **File**: `backend/services/email_parser.py`
- **Action**: The parser currently extracts `In-Reply-To` and `References`. Ensure it sets `thread_id` robustly. No major changes needed unless bugs are found, but verify.
- **Spec Compliance**: Parser must correctly handle missing headers.
