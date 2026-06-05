## 2024-05-24 - Interactive Element Keyboard Accessibility
**Learning:** Found several native `<button>` and `<a>` elements acting as UI controls across various components that relied on hover states (like `hover:underline` and `hover:bg-secondary`) but lacked explicit focus visibility styling (`focus-visible:ring-2`). This causes them to be virtually invisible to keyboard-only users who rely on focus outlines to navigate.
**Action:** Added explicit Tailwind `focus-visible` ring utility classes (e.g. `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40`) to all such interactive elements to ensure clear keyboard accessibility across the frontend application.

## 2025-06-02 - Default button type behavior

**Learning:** Browsers interpret standard `<button>` elements as submit buttons (`type="submit"`) by default when located inside a form context, which can cause unexpected page reloads or form submissions.

**Action:** Always explicitly define `type="button"` on interactive buttons not meant for form submission across all React components to prevent this behavior.
