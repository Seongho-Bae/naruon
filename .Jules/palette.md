## 2024-05-24 - Add `aria-busy` to async operation buttons
**Learning:** Action buttons triggering asynchronous network operations need an `aria-busy` attribute, alongside `disabled` state and visual indicators, to correctly communicate their loading state to screen reader users.
**Action:** Add `aria-busy={isLoading}` to action buttons alongside existing spinner and disabled states for network interactions.
## 2024-05-17 - Update UI Terminology Mapping
**Learning:** Blind, global string replacement (regex) for translating or standardizing Korean UI terms can lead to semantical breaks. For example, blindly replacing "할 일" to "실행 항목" breaks other valid Korean words containing "할 일" such as "표시할 일정" (changing it to "표시실행 항목정"). Similarly, replacing "검색" with "맥락 검색" indiscriminately can lead to redundant strings like "맥락 맥락 검색".
**Action:** When updating localization strings or terminology across a large codebase, apply context-aware parsing or careful target-word bound replacements rather than naive global string matching. Always manually verify the `git diff` for readability and semantical correctness after applying bulk string manipulations.
