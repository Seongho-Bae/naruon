## 2024-05-24 - Add `aria-busy` to async operation buttons
**Learning:** Action buttons triggering asynchronous network operations need an `aria-busy` attribute, alongside `disabled` state and visual indicators, to correctly communicate their loading state to screen reader users.
**Action:** Add `aria-busy={isLoading}` to action buttons alongside existing spinner and disabled states for network interactions.
## 2024-05-24 - Refresh button loading states
**Learning:** Adding explicit visual indicators (like `animate-spin`) and `aria-busy` to buttons alongside `disabled` states prevents multiple clicks and effectively communicates asynchronous loading to screen readers.
**Action:** When creating action buttons for async operations like '새로고침' (Refresh), always include `disabled={loading}`, `aria-busy={loading}`, adjust opacity (`disabled:opacity-60`), change cursor (`disabled:cursor-not-allowed`), spin icons, and update text to '새로고침 중'.
