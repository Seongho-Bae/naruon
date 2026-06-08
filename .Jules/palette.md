## 2026-06-08 - Add loading state to Search Submit Button
**Learning:** The search submit button lacked a disabled and visual loading state during query execution, which can lead to accidental duplicate submissions and poor user feedback. Using the existing loading state, disabling the button with appropriate styling `disabled:cursor-wait disabled:opacity-60`, and changing the copy to '검색 중' (Searching) resolves this.
**Action:** Always ensure async operations, like search or submit buttons, have explicit loading feedback and are disabled to prevent duplicate actions.
