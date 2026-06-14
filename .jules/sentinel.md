## 2025-02-27 - [Fix Open Redirect in OIDC Auth Callback]
**Vulnerability:** The application was vulnerable to Open Redirects and potential XSS due to an unvalidated `returnTo` variable retrieved from session storage and passed directly into `window.location.replace()` in the OIDC callback handler.
**Learning:** OIDC callbacks that restore user state via session storage can be vectors for injection if the stored return paths aren't sanitized or validated strictly as local paths.
**Prevention:** Always validate client-side redirect paths originating from unverified storage or inputs. Ensure the path strictly starts with `/` and not `//` (to block protocol-relative URLs) before executing a location replace.
