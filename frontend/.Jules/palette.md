## 2026-06-08 - WorkspaceHome unused import investigation
**Learning:** Investigating unused import reports should first verify the current file because the codebase may already have evolved. The repo lint entrypoint is `eslint`, and the focused check for this investigation was `npx eslint src/components/WorkspaceHome.tsx`.
**Action:** Use the focused `npx eslint src/components/WorkspaceHome.tsx` check when confirming WorkspaceHome import health, and reserve broader `eslint` runs for full frontend lint validation.
