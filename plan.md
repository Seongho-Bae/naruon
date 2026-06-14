1. Add `useCallback` to memoize `handleSelectEmail` in `frontend/src/components/WorkspaceHome.tsx`.
   - The `EmailListItemComponent` is already wrapped in `React.memo` to prevent unnecessary re-renders of individual emails in the list.
   - However, the `handleSelectEmail` function passed to `EmailList` and then down to `EmailListItemComponent` is recreated on every render of `WorkspaceHome.tsx` because it's not wrapped in `useCallback`.
   - Memoizing `handleSelectEmail` with `useCallback` will prevent the `onSelectEmail` prop from changing, allowing `React.memo` on `EmailListItemComponent` to effectively prevent re-renders of all unchanged email list items when the user interacts with the app (like opening a panel, resizing, or switching views).
2. Complete pre-commit instructions.
   - Ensure the application still works correctly.
   - Run linter and tests in the frontend.
3. Submit the change.
