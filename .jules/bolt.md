## 2024-05-18 - Optimized SQL Commit in Python Loop
**Learning:** Extracting an `await db.commit()` and `await db.refresh(task)` loop-bound statements out of iterative logic significantly drops transaction overhead and improves processing time, especially on retry workflows with `IntegrityError`.
**Action:** Always inspect the operations surrounding the `except IntegrityError:` loop handling during bulk creation when debugging Python SQLAlchemy database bottlenecks.
