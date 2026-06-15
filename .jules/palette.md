## 2024-05-24 - Interactive Element Keyboard Accessibility
**Learning:** Found several native `<button>` and `<a>` elements acting as UI controls across various components that relied on hover states (like `hover:underline` and `hover:bg-secondary`) but lacked explicit focus visibility styling (`focus-visible:ring-2`). This causes them to be virtually invisible to keyboard-only users who rely on focus outlines to navigate.
**Action:** Added explicit Tailwind `focus-visible` ring utility classes (e.g. `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40`) to all such interactive elements to ensure clear keyboard accessibility across the frontend application.

## 2025-06-02 - Default button type behavior

**Learning:** Browsers interpret standard `<button>` elements as submit buttons (`type="submit"`) by default when located inside a form context, which can cause unexpected page reloads or form submissions.

**Action:** Always explicitly define `type="button"` on interactive buttons not meant for form submission across all React components to prevent this behavior.
## 2024-06-14 - 비활성화된 버튼의 상태 설명 개선
**Learning:** React/Next.js 기반의 앱에서 로딩 중이거나 권한 문제로 비활성화된 버튼들에 시각적인 변화나 단순한 `disabled` 속성만 부여할 경우, 스크린 리더 사용자뿐만 아니라 일반 사용자도 '왜' 클릭할 수 없는지 명확히 이해하기 어려움.
**Action:** 비활성화 조건(`disabled={condition}`)이 걸린 모든 버튼에는 해당 조건에 부합하는 사유를 명시적으로 설명하는 `title` 속성을 추가하여 UX와 접근성을 동시에 개선함. (예: `title={isLoading ? "데이터를 불러오는 중입니다" : "실행"}`)
