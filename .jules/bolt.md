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
## 2026-06-06 - Refactoring repetitive assert any loops
**Learning:** Repetitive single-statement `assert any(...)` calls can be cleanly refactored into an `expected_substrings` list that loops over assertions. When extracting strings to build the list, it's very helpful to use `re.sub()` to simultaneously capture strings via a replacer function while replacing the matches with placeholders, and then substitute the newly generated list block into the code.
**Action:** Always prefer lists and loops over repeated code structures when possible, maintaining test readability.
