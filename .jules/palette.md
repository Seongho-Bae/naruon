## 2024-05-24 - Interactive Element Keyboard Accessibility
**Learning:** Found several native `<button>` and `<a>` elements acting as UI controls across various components that relied on hover states (like `hover:underline` and `hover:bg-secondary`) but lacked explicit focus visibility styling (`focus-visible:ring-2`). This causes them to be virtually invisible to keyboard-only users who rely on focus outlines to navigate.
**Action:** Added explicit Tailwind `focus-visible` ring utility classes (e.g. `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40`) to all such interactive elements to ensure clear keyboard accessibility across the frontend application.

## 2025-06-02 - Default button type behavior

**Learning:** Browsers interpret standard `<button>` elements as submit buttons (`type="submit"`) by default when located inside a form context, which can cause unexpected page reloads or form submissions.

**Action:** Always explicitly define `type="button"` on interactive buttons not meant for form submission across all React components to prevent this behavior.
## 2024-06-14 - 비활성화된 설정 저장 버튼 상태 설명 개선
**Learning:** React/Next.js 기반의 앱에서 사용자 폼(설정 페이지)의 버튼이 입력값 부족이나 서버 요청 중인 상태로 인해 비활성화되었을 때, 단순한 `disabled` 속성만 부여하면 사용자가 혼란을 겪을 수 있음.
**Action:** `SettingsLayout.tsx`의 계정 설정 저장, OIDC 로그인/로그아웃 등 비활성화 조건(`disabled={condition}`)이 걸린 버튼에 `title` 속성을 추가하여 시각적인 툴팁으로 사용자가 직관적으로 원인을 알 수 있도록 개선함.
