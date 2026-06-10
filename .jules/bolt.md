## 2025-02-20 - Optimize redundant dictionary lookups in python loops

 **Learning:** Using `dict.setdefault` and multiple `dict.get` or `key in dict` checks inside tight loops significantly impacts performance due to repeated dictionary lookups and unnecessary list allocations. Caching dictionary lookups (e.g., using a single `dict.get(key)`) and conditionally handling the logic based on the result is much more performant.
 **Action:** When aggregating or grouping items in a loop, avoid `setdefault`. Instead, check if the key exists using a single `.get()`, and perform initialization/updates conditionally. Additionally, hoist loop-invariant checks (e.g., `folder == "sent"`) outside the loop to avoid redundant evaluations.
