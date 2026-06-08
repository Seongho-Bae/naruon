## 2026-06-04 - Add loading state to SearchLayout button
**Learning:** Users notice the little things. Missing loading states on async actions makes users unsure if their action registered. Adding a simple loading spinner provides immediate feedback and aligns with accessibility best practices when making dynamic state changes.
**Action:** Always include a visual loading state like `Loader2` for async actions (like the '발신자 관계 캡처' button) to provide immediate feedback to the user.
## 2024-06-07 - Refactoring CalendarLayout buttons
**Learning:** Raw HTML `<button>` elements with complex Tailwind class strings were scattered throughout layout components, which led to inconsistent hover, focus-visible states, and accessibility properties compared to standard design system components.
**Action:** Replace raw HTML `<button>` tags with the `@/components/ui/button` `Button` component using appropriate variants (`ghost`, `outline`) and sizes (`icon-sm`, `sm`) to instantly standardize accessible focus rings and interaction feedback.
