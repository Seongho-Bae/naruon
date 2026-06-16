## 2025-02-28 - Add Loader2 spinner to async buttons in SettingsLayout.tsx
**Learning:** Providing explicit visual feedback (like a spinning loader) during asynchronous save operations prevents users from wondering if their click registered, significantly improving perceived performance and UX.
**Action:** Always map loading states (e.g., `isSaving`, `isLoading`) to explicit UI indicators like the `Loader2` icon with `animate-spin` class inside submit buttons, rather than just changing button text or disabling the button.
