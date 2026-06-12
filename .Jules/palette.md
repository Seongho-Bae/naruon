## 2024-06-04 - Semantic Buttons for Task Interactions
**Learning:** Interactive areas that trigger actions (like opening a task detail view or navigating to a source) should be semantic `<button>` elements rather than `<div>`s with `onClick` handlers. `div`s lack native keyboard accessibility, focus rings, and proper screen reader roles. Also, `aria-label`s should be context-aware (e.g., "접수 더보기" instead of just "더보기").
**Action:** When creating new components that function as clickable cards or icon triggers, always wrap them in `<button type="button">` and ensure they have `focus-visible` styles and contextually descriptive `aria-label`s.
## 2026-06-08 - Focus-visible styles on interactive elements
**Learning:** Keyboard accessibility relies on visual indicators when elements receive focus. Standard focus-visible rings (e.g. `focus-visible:ring-2 focus-visible:ring-ring/40`) must be applied globally to all interactive elements like buttons and tabs, instead of randomly missing them in different pages.
**Action:** Audit all interactive elements (buttons, links, custom inputs) across components and standardise on `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40` to provide predictable tab navigation feedback.
## 2024-03-20 - Add ARIA Labels to Missing Buttons
**Learning:** Found multiple instances where buttons lacked `aria-label`s, which is critical for screen reader users and assistive technologies, especially for icon-only buttons or interactive elements like 'Add Item' and 'Change Status'.
**Action:** When inspecting components with multiple interactive actions (like TasksLayout, CalendarLayout, and AIHubLayout), always ensure `aria-label`s are consistently applied alongside existing visual and keyboard styling.
