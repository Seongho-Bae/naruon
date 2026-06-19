## 2024-06-06 - Replacing UI dev notes with user-facing text
**Learning:** Legacy UI components might contain placeholder or dev-centric descriptive text (e.g., "legacy AuditLog는 직접 노출하지 않습니다.") that isn't ideal for end-users.
**Action:** When finding UI elements describing internal technical details, replace them with clear, end-user descriptions explaining the feature's value in a localized and user-friendly manner, then verify via visual playwright inspection.

## 2026-06-08 - Add loading state to Search Submit Button
**Learning:** The search submit button lacked a disabled and visual loading state during query execution, which can lead to accidental duplicate submissions and poor user feedback. Using the existing loading state, disabling the button with appropriate styling `disabled:cursor-wait disabled:opacity-60`, and changing the copy to "검색 중" resolves this.
**Action:** Always ensure async operations, like search or submit buttons, have explicit loading feedback and are disabled to prevent duplicate actions.

## 2026-06-08 - Accessible Search Inputs Across Layouts
**Learning:** Search inputs placed in complex dashboard layouts frequently miss explicitly associated labels and IDs, relying only on placeholders or visual icons, which creates barriers for screen reader users navigating the page landmarks.
**Action:** Always provide a visually hidden `<label>` explicitly tied to the input via `htmlFor` and `id`, and ensure any adjacent decorative search icons have `aria-hidden="true"`.

## 2024-06-04 - Semantic Buttons for Task Interactions
**Learning:** Interactive areas that trigger actions (like opening a task detail view or navigating to a source) should be semantic `<button>` elements rather than `<div>`s with `onClick` handlers. `div`s lack native keyboard accessibility, focus rings, and proper screen reader roles. Also, `aria-label`s should be context-aware (e.g., "접수 더보기" instead of just "더보기").
**Action:** When creating new components that function as clickable cards or icon triggers, always wrap them in `<button type="button">` and ensure they have `focus-visible` styles and contextually descriptive `aria-label`s.

## 2024-06-06 - Always Include Focus States for Custom Buttons
**Learning:** Custom UI buttons without explicitly defined focus styles become invisible during keyboard navigation. This fundamentally breaks keyboard accessibility, leaving power users and screen reader users unable to track their current position on the page. In this application, several action and filter buttons lacked proper focus indicators despite having hover states.
**Action:** Whenever creating or modifying custom interactive elements (like `<button>` or `<a>`), unconditionally add standard focus styles, such as `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40`.

## 2026-06-11 - Adding Repository Badges and Communication Guidelines
**Learning:** Organizing a repository with Issue/PR templates, CI badges, and a Code of Conduct creates an immediate impression of professionalism and hygiene, saving developers time on repetitive questions.
**Action:** When setting up a new repository or performing repository hygiene, always ensure a base set of standard templates and CI badges are included.

## 2024-06-12 - Adding a11y Roles to InsightCard Status States
**Learning:** Generic wrapper components like `InsightCard` which dynamically load and present data often conditionally render a generic loader or error state. Screen readers may ignore these visual cues unless they are accompanied by proper semantic roles, such as `role="status"` and `aria-live="polite"` for loading spinners, and `role="alert"` for error messages. Also adding `aria-hidden="true"` to visual icons within these states reduces noise.
**Action:** When creating reusable data-fetching card components, always annotate loading and error state container elements with the appropriate ARIA roles and live regions, and hide purely decorative elements.

## 2026-06-13 - Use type=text for Custom Search Inputs
**Learning:** When implementing a custom clear button for search inputs, using `type="search"` causes WebKit browsers to display a native clear button, resulting in double buttons. While CSS `::-webkit-search-cancel-button` tricks exist, they can be unreliable across environments.
**Action:** Use `<input type="text" inputMode="search" role="searchbox">`. This prevents the native clear button from rendering while perfectly preserving screen reader semantics and triggering the mobile search keyboard.

## 2025-02-05 - Search clear action keyboard focus flow
**Learning:** When users click a "clear search" icon button to empty an input field, screen readers and keyboard navigation can lose their place in the DOM structure.
**Action:** Always capture a `useRef` to the `<Input>` and explicitly call `ref.current?.focus()` inside the clear button's `onClick` handler to preserve interaction flow.

## 2026-06-16 - Internal tool form accessibility and visual feedback
**Learning:** Internal tool forms can miss basic accessibility attributes like stable IDs, linked labels, and clear async feedback on submit buttons. Without those details, screen readers lose form context and users get weak confirmation during long-running actions.
**Action:** Verify internal form inputs use explicit `label htmlFor`/`id` pairs, decorative icons are `aria-hidden`, and async buttons expose disabled loading states with visible spinner feedback.
