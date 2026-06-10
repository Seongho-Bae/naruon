1. **Analyze `backend/api/tasks.py:131`**:
   The function `create_reply_sla_escalations` is too long, mostly due to duplication of fetching logic, task updating logic, and complex error handling (IntegrityError with a fallback path).

2. **Extract common operations**:
   - Create `_fetch_existing_sla_tasks` to fetch and index existing SLA tasks by `related_email_id`.
   - Create `_update_sla_task` to handle updating an existing task.
   - Create `_build_new_sla_task` to encapsulate the creation of a new `TicketTask`.

3. **Extract Fallback Logic**:
   - Extract the entire `IntegrityError` fallback block into a new function: `_process_sla_escalations_fallback`. This makes the main function's happy path clearer and separates the complex nested retry logic.

4. **Verify**:
   - Run tests and ensure no functionality is broken.
   - Run linter/formatting (`black`, `ruff`, etc., based on the project's setup).
