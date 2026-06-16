## 2024-06-06 - Replacing UI dev notes with user-facing text
**Learning:** Legacy UI components might contain placeholder or dev-centric descriptive text (e.g., "legacy AuditLog는 직접 노출하지 않습니다.") that isn't ideal for end-users.
**Action:** When finding UI elements describing internal technical details, replace them with clear, end-user descriptions explaining the feature's value in a localized and user-friendly manner, then verify via visual playwright inspection.

## 2026-06-08 - Add loading state to Search Submit Button
**Learning:** The search submit button lacked a disabled and visual loading state during query execution, which can lead to accidental duplicate submissions and poor user feedback. Using the existing loading state, disabling the button with appropriate styling `disabled:cursor-wait disabled:opacity-60`, and changing the copy to "검색 중" resolves this.
**Action:** Always ensure async operations, like search or submit buttons, have explicit loading feedback and are disabled to prevent duplicate actions.

## 2026-06-08 - Accessible Search Inputs Across Layouts
**Learning:** Search inputs placed in complex dashboard layouts frequently miss explicitly associated labels and IDs, relying only on placeholders or visual icons, which creates barriers for screen reader users navigating the page landmarks.
**Action:** Always provide a visually hidden `<label>` explicitly tied to the input via `htmlFor` and `id`, and ensure any adjacent decorative search icons have `aria-hidden="true"`.

## 2026-06-08 - Accessible Loading States for Buttons
**Learning:** The native HTML `disabled` attribute inherently communicates the disabled state to screen readers and removes elements from the tab order. Adding `aria-disabled="true"` to a `disabled` button is redundant and can be flagged by accessibility linters. However, adding `aria-busy="true"` during an async operation correctly communicates to screen readers that the element is actively updating.
**Action:** When adding accessible loading states to buttons, use `disabled={isLoading}` for state, add `aria-busy={isLoading}` for context, but avoid redundant `aria-disabled={isLoading}`.
