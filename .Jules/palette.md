## 2024-05-23 - Add context-rich ARIA labels to utility buttons
**Learning:** Basic tooltips or titles are sometimes missing on icon-only or ambiguous utility buttons (e.g., '위치 보기', '의사결정 추가'). Including contextual information in the `aria-label` (e.g., '출시 회의 일정 삭제', '회의실 A (4층) 위치 보기') provides a significantly better experience for screen reader users by disambiguating the action target.
**Action:** Proactively ensure that all utility actions have `aria-label`s that combine the action with its explicit context/target, rather than relying solely on surrounding text or icons.
