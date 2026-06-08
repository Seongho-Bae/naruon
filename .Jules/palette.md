## 2024-06-04 - Semantic Buttons for Task Interactions
**Learning:** Interactive areas that trigger actions (like opening a task detail view or navigating to a source) should be semantic `<button>` elements rather than `<div>`s with `onClick` handlers. `div`s lack native keyboard accessibility, focus rings, and proper screen reader roles. Also, `aria-label`s should be context-aware (e.g., "접수 더보기" instead of just "더보기").
**Action:** When creating new components that function as clickable cards or icon triggers, always wrap them in `<button type="button">` and ensure they have `focus-visible` styles and contextually descriptive `aria-label`s.

## 2024-06-06 - Always Include Focus States for Custom Buttons
**Learning:** Custom UI buttons without explicitly defined focus styles become invisible during keyboard navigation. This fundamentally breaks keyboard accessibility, leaving power users and screen reader users unable to track their current position on the page. In this application, several action and filter buttons lacked proper focus indicators despite having hover states.
**Action:** Whenever creating or modifying custom interactive elements (like `<button>` or `<a>`), unconditionally add standard focus styles, such as `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40`.
