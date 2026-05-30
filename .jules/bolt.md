## 2025-03-09 - O(n^2) nested loop optimization in thread_reply_candidate
**Learning:** `thread_reply_candidate` iterated over `any(...)` loop over all `ordered_messages` nested inside a loop over `ordered_messages`, resulting in a O(n^2) complexity.
**Action:** By looping backwards (reversed `ordered_messages`), the last external response date can be memoized, reducing the complexity to O(n). This dramatically increased the performance, taking 0.01s instead of 0.20s in my benchmark over 1,000 runs of 100 random messages.
