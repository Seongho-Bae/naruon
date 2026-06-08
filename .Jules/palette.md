## 2024-06-04 - Semantic Buttons for Task Interactions
**Learning:** Interactive areas that trigger actions (like opening a task detail view or navigating to a source) should be semantic `<button>` elements rather than `<div>`s with `onClick` handlers. `div`s lack native keyboard accessibility, focus rings, and proper screen reader roles. Also, `aria-label`s should be context-aware (e.g., "접수 더보기" instead of just "더보기").
**Action:** When creating new components that function as clickable cards or icon triggers, always wrap them in `<button type="button">` and ensure they have `focus-visible` styles and contextually descriptive `aria-label`s.

## 2024-06-08 - Keyboard Accessibility for Custom Buttons
**Learning:** Custom `<button>` elements in layout components (e.g., `DataLayout.tsx`, `ProjectsLayout.tsx`) often lack native focus rings when styled with Tailwind CSS, which impacts keyboard accessibility.
**Action:** Consistently apply `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40` utility classes to interactive elements like buttons and links to ensure clear visual feedback during keyboard navigation.
