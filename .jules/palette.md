## 2024-06-06 - Replacing UI dev notes with user-facing text
**Learning:** Legacy UI components might contain placeholder or dev-centric descriptive text (e.g., "legacy AuditLog는 직접 노출하지 않습니다.") that isn't ideal for end-users.
**Action:** When finding UI elements describing internal technical details, replace them with clear, end-user descriptions explaining the feature's value in a localized and user-friendly manner, then verify via visual playwright inspection.

## 2026-06-08 - Add loading state to Search Submit Button
**Learning:** The search submit button lacked a disabled and visual loading state during query execution, which can lead to accidental duplicate submissions and poor user feedback. Using the existing loading state, disabling the button with appropriate styling `disabled:cursor-wait disabled:opacity-60`, and changing the copy to "검색 중" resolves this.
**Action:** Always ensure async operations, like search or submit buttons, have explicit loading feedback and are disabled to prevent duplicate actions.

## 2026-06-08 - Accessible Search Inputs Across Layouts
**Learning:** Search inputs placed in complex dashboard layouts frequently miss explicitly associated labels and IDs, relying only on placeholders or visual icons, which creates barriers for screen reader users navigating the page landmarks.
**Action:** Always provide a visually hidden `<label>` explicitly tied to the input via `htmlFor` and `id`, and ensure any adjacent decorative search icons have `aria-hidden="true"`.

## 2026-06-10 - Add context-rich ARIA labels to utility buttons
**Learning:** Basic tooltips or titles are sometimes missing on icon-only or ambiguous utility buttons (e.g., '위치 보기', '의사결정 추가'). Including contextual information in the `aria-label` (e.g., '출시 회의 일정 삭제', '회의실 A (4층) 위치 보기') provides a significantly better experience for screen reader users by disambiguating the action target.
**Action:** Proactively ensure that all utility actions have `aria-label`s that combine the action with its explicit context/target, rather than relying solely on surrounding text or icons.
