## 2024-05-24 - Add `aria-busy` to async operation buttons
**Learning:** Action buttons triggering asynchronous network operations need an `aria-busy` attribute, alongside `disabled` state and visual indicators, to correctly communicate their loading state to screen reader users.
**Action:** Add `aria-busy={isLoading}` to action buttons alongside existing spinner and disabled states for network interactions.
## 2024-05-24 - Refresh button loading states
**Learning:** Adding explicit visual indicators (like `animate-spin`) and `aria-busy` to buttons alongside `disabled` states prevents multiple clicks and effectively communicates asynchronous loading to screen readers.
**Action:** When creating action buttons for async operations like '새로고침' (Refresh), always include `disabled={loading}`, `aria-busy={loading}`, adjust opacity (`disabled:opacity-60`), change cursor (`disabled:cursor-not-allowed`), spin icons, and update text to '새로고침 중'.
## 2024-05-17 - Update UI Terminology Mapping
**Learning:** Blind, global string replacement (regex) for translating or standardizing Korean UI terms can lead to semantical breaks. For example, blindly replacing "할 일" to "실행 항목" breaks other valid Korean words containing "할 일" such as "표시할 일정" (changing it to "표시실행 항목정"). Similarly, replacing "검색" with "맥락 검색" indiscriminately can lead to redundant strings like "맥락 맥락 검색".
**Action:** When updating localization strings or terminology across a large codebase, apply context-aware parsing or careful target-word bound replacements rather than naive global string matching. Always manually verify the `git diff` for readability and semantical correctness after applying bulk string manipulations.
## 2026-06-20 - Use semantic `type="search"` with custom clear buttons
**Learning:** Using `type="search"` on input fields improves mobile UX by rendering a semantic search keyboard (with a "Search" submit button instead of "Go/Enter"). However, when adding a custom clear button ('X') using UI components or Tailwind CSS, the native webkit clear button overlaps with it.
**Action:** When implementing search fields, always use `type="search"` instead of `type="text"` to get the semantic keyboard benefits. To prevent visual overlaps with custom clear icons, add the `[&::-webkit-search-cancel-button]:hidden` Tailwind utility class to hide the native webkit clear button.
## 2024-05-24 - Ensure aria-busy accompanies disabled for async UI buttons
**Learning:** Action buttons triggering asynchronous network operations that already implement `disabled={loading}` and visual spinners MUST also include an `aria-busy={loading}` attribute to correctly communicate the active loading state to screen reader users without requiring focus shifts.
**Action:** When adding or auditing buttons for async operations like '동기화 중', '전송 중', or '검색 중', ensure `aria-busy={loadingVariable}` is explicitly added alongside existing spinner and disabled states.

## 2026-06-25 - Add loading state to CalendarLayout writeback intent buttons
**Learning:** Async calendar writeback operations in `CalendarLayout.tsx` were missing clear visual loading indicators, leaving the user unsure if the action was being processed. Adding a spinning `Loader2` icon to the buttons during the `isWritebackLoading` state provides immediate feedback, aligning with a11y `aria-busy` states already present.
**Action:** Always complement `aria-busy={true}` with a visual loading indicator (like `Loader2 animate-spin`) on action buttons for better immediate user feedback during async operations.

## 2026-06-25 - PR Resubmission and CI Failures
**Learning:** Security scanners like Strix can sometimes output false positives or scan failures during infrastructure/LLM API outages ("Below-threshold findings detected, but infrastructure errors occurred"). This can block PR reviews.
**Action:** If a PR review fails explicitly due to a hallucinated scanner finding or LLM API outage rather than a code error, document the reason, discard out-of-scope backend fixes if acting under a strict frontend UX persona, and resubmit the original intended code changes on a new branch.

## 2026-06-25 - OpenCode deterministic fallback
**Learning:** The `opencode-review` CI workflow will fail closed if the underlying LLM API times out or returns a 429 Too Many Requests error, unless the PR only contains 'low risk' files (like `.md` or `.txt`). Modifying any `.py` or `.tsx` file prevents the deterministic fallback from approving the PR during an API outage.
**Action:** Do not attempt to bypass `opencode-review` API timeouts by rewriting the CI workflow. Instead, wait and resubmit the original PR code to retry the review process when the underlying APIs recover.

## 2026-06-25 - Extraneous CI File Modifications
**Learning:** During PR resubmission, it is critical to ensure that no unrelated core infrastructure or CI script changes (like modifications to `.github/workflows/opencode-review.yml` or `scripts/ci/test_strix_quick_gate.sh`) are inadvertently carried over or pushed, as this violates strict persona boundaries and causes severe pipeline regressions.
**Action:** When working on a frontend UX task on a new branch, run `git diff origin/develop --name-only` to explicitly verify that only the intended frontend application files (and changelogs/journals) are modified before committing and submitting.

## 2026-06-25 - Prevent DOMPurify hallucinations
**Learning:** Security scanners sometimes mistakenly flag simple dictionary lookups (e.g. mapping string keys to predefined localized strings) or hardcoded static state string renderings as XSS vulnerabilities, demanding the addition of `DOMPurify`.
**Action:** When a scanner incorrectly flags a React component for XSS in an area rendering strictly static dictionary lookups (`getProtocolLabel(source.protocol)`) or hardcoded state strings (`selectedDetailEvent?.description`), do NOT introduce heavy dependencies like `DOMPurify`. The STRIX finding is a false positive because the underlying data is hardcoded mock data in the component state, not unsanitized user input. Discard the hallucinated security fix requests if acting strictly as a frontend UX agent.

## 2026-06-25 - Simplify Writeback Success Messages
**Learning:** Rendering raw system architecture details (like specific protocols, ETag requirements, and writeback modes) in the UI upon successful operations creates information disclosure vulnerabilities (as flagged by STRIX) and degrades UX with unnecessary technical jargon.
**Action:** Replace detailed technical breakdowns in success states with concise, user-friendly messages (e.g., "요청이 성공적으로 처리되었습니다.") to improve both security (reducing information disclosure) and usability.
