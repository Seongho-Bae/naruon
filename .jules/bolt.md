## 2024-05-18 - Optimized SQL Commit in Python Loop
**Learning:** Extracting an `await db.commit()` and `await db.refresh(task)` loop-bound statements out of iterative logic significantly drops transaction overhead and improves processing time, especially on retry workflows with `IntegrityError`.
**Action:** Always inspect the operations surrounding the `except IntegrityError:` loop handling during bulk creation when debugging Python SQLAlchemy database bottlenecks.

## 2026-06-07 - AsyncDBAPI Batch Execution Overhead
**Learning:** When executing multiple SQLAlchemy text statements sequentially (like a database bootstrap schema backfill) over an async connection, awaiting `conn.execute()` iteratively incurs Python async event loop context switching overhead for each query.
**Action:** Extract the loop into a synchronous helper function and pass it to `await conn.run_sync()`. This executes the iterative batch within the async context's worker thread via a single blocking DBAPI call, significantly reducing execution overhead (measured ~30% faster locally).

## 2026-06-06 - Missing OSError Coverage in test_email_parser.py
**Learning:** We need to explicitly mock built-in operations like `open()` to test generic exception types like `OSError` effectively, instead of relying solely on missing files to raise `FileNotFoundError` (which is a subclass, but might not trigger all handlers correctly if the code depends on string matching the exception or other side effects).
**Action:** When covering explicit `except OSError:` blocks, use `unittest.mock.patch('builtins.open', side_effect=OSError('...'))` to guarantee the exact exception type and message is raised for the test assertion.

## 2025-03-09 - O(n^2) nested loop optimization in thread_reply_candidate
**Learning:** `thread_reply_candidate` iterated over `any(...)` loop over all `ordered_messages` nested inside a loop over `ordered_messages`, resulting in a O(n^2) complexity.
**Action:** By looping backwards (reversed `ordered_messages`), the last external response date can be memoized, reducing the complexity to O(n). This dramatically increased the performance, taking 0.01s instead of 0.20s in my benchmark over 1,000 runs of 100 random messages.
## 2026-05-29 - Pre-compile Regex in network graph extraction
**Learning:** Found an inline regex compilation for `extract_emails` inside a frequently hit API endpoint (`/api/network/graph`) which is called on potentially thousands of records. Compiling regex repeatedly introduces measurable overhead.
**Action:** Pre-compile regex at the module level using `re.compile`. This optimization significantly improves the runtime speed by roughly 25% (as measured via timeit).
## 2026-06-01 - O(n^2) nested loop optimization in extract_reference_ids
**Learning:** `extract_reference_ids` and `assign_thread_id` used `not in list` to deduplicate email references resulting in an O(n^2) complexity over large headers.
**Action:** By keeping a `seen = set()` for O(1) lookups, the operation runs in O(n) time.
## 2025-05-30 - O(N^2) optimization in emails api and useMemo in frontend graph
**Learning:** `thread_matches_folder` in `get_emails` iterated through a thread's messages over and over again for `visible_groups` checking `if folder == "sent"`. Memoizing this lookup conditionally improved this behavior to O(N). Also, repeated maps and filters on render in the frontend can quickly become problematic, which is solved cleanly via `useMemo`.
**Action:** When filtering objects mapped iteratively, identify overlapping inner iterators (like checking for matching inner properties across items) and build them in a lookup dictionary ahead of time. In React, safely memoize constant properties built sequentially.

## 2025-02-12 - Prevent Blocking UI on Slow LLM Endpoints
**Learning:** In React components fetching both fast core data and slow AI-generated data concurrently inside `useEffect` (like `EmailDetail.tsx` waiting for LLM summarization), awaiting the slow request blocks the component from setting its fast core data state. This results in the user waiting artificially long for content that's already arrived.
**Action:** Always fetch the primary/fast core data first, set the core data state, and disable the top-level loading indicator immediately. Then, fire secondary/slow (LLM) promises without awaiting them in the primary render path, allowing them to independently update their own state placeholders when they complete.

## 2026-06-06 - Refactoring repetitive assert any loops
**Learning:** Repetitive single-statement `assert any(...)` calls can be cleanly refactored into an `expected_substrings` list that loops over assertions. When extracting strings to build the list, it's very helpful to use `re.sub()` to simultaneously capture strings via a replacer function while replacing the matches with placeholders, and then substitute the newly generated list block into the code.
**Action:** Always prefer lists and loops over repeated code structures when possible, maintaining test readability.

## 2026-06-07 - Redundant SHA256 Hashing during UniqueThread Deduplication
**Learning:** `create_unique_thread_intent` iterates over candidates twice to first extract lookups and fingerprint sets, and then iterates over them a second time inside `_find_matches_for_candidates` to match those lookups. This caused `candidate_strong_fingerprint(candidate)` (which performs a SHA256 encoding) to be redundantly executed twice per candidate.
**Action:** Extract expensive lookups (`candidate_strong_fingerprint` and regex normalizations) into dictionaries mapped by `candidate_key` during the first iteration to prevent redundant processing.

## 2026-06-09 - [Extract and Memoize List Items to Prevent Unnecessary Re-renders]
**Learning:** React re-renders long lists entirely when the selected item changes if items are inline mapped. Even if the array length isn't massive (e.g. 50 items), the inline function instantiations and DOM reconciliation add up across the list.
**Action:** Always extract complex list items into isolated `React.memo` components, especially when selection state is hoisted to the parent component.
