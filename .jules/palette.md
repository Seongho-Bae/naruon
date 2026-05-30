## 2026-05-30 - Added loading spinners to EmailDetail async actions
**Learning:** Adding explicit visual feedback (like a spinning `Loader2` icon) to buttons during asynchronous operations greatly improves the user experience by signaling that work is happening, especially since the UI doesn't always automatically reflect state changes instantly.
**Action:** Always include loading indicators on action buttons that trigger API requests or long-running tasks.
