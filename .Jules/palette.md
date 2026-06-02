## 2025-06-02 - Default button type behavior

**Learning:** Browsers interpret standard `<button>` elements as submit buttons (`type="submit"`) by default when located inside a form context, which can cause unexpected page reloads or form submissions.

**Action:** Always explicitly define `type="button"` on interactive buttons not meant for form submission across all React components to prevent this behavior.
