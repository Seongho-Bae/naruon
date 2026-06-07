## 2024-05-30 - N+1 Query Fix for Reply SLA Task Escalations
**Learning:** When encountering `IntegrityError` in a loop where objects are inserted individually due to conflict with existing objects, relying on single queries inside the exception handler leads to N+1 database queries.
**Action:** Extract the query for existing objects into a batch query outside the loop using `.in_()`, then look up existing objects from an in-memory dictionary. This avoids querying the database inside the loop and improves performance significantly when multiple conflicts occur.
