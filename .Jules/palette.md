## 2024-05-24 - Add `aria-busy` to async operation buttons
**Learning:** Action buttons triggering asynchronous network operations need an `aria-busy` attribute, alongside `disabled` state and visual indicators, to correctly communicate their loading state to screen reader users.
**Action:** Add `aria-busy={isLoading}` to action buttons alongside existing spinner and disabled states for network interactions.
