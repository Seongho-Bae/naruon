## 2024-06-06 - Replacing UI dev notes with user-facing text
**Learning:** Legacy UI components might contain placeholder or dev-centric descriptive text (e.g., "legacy AuditLog는 직접 노출하지 않습니다.") that isn't ideal for end-users.
**Action:** When finding UI elements describing internal technical details, replace them with clear, end-user descriptions explaining the feature's value in a localized and user-friendly manner, then verify via visual playwright inspection.

## 2026-06-08 - Accessible Search Inputs Across Layouts
**Learning:** Search inputs placed in complex dashboard layouts frequently miss explicitly associated labels and IDs, relying only on placeholders or visual icons, which creates barriers for screen reader users navigating the page landmarks.
**Action:** Always provide a visually hidden `<label>` explicitly tied to the input via `htmlFor` and `id`, and ensure any adjacent decorative search icons have `aria-hidden="true"`.
