## 2024-05-24 - Overly Permissive CORS Policy

**Vulnerability:** The CORS configuration in FastAPI allowed wildcards (`*`) for `allow_methods` and `allow_headers`.
**Learning:** This could permit unintended cross-origin interaction, potentially exposing the API to Cross-Site Request Forgery (CSRF) or unintended data exposure, particularly via custom headers or unconventional methods.
**Prevention:** Always restrict `allow_methods` and `allow_headers` in CORS policies to the exact methods and headers required by the application.
## 2026-05-28 - Missing Next.js Security Headers
**Vulnerability:** The Next.js frontend was missing critical HTTP security headers (Content-Security-Policy, X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security).
**Learning:** Security headers should be explicitly configured in Next.js applications via the `headers()` method in `next.config.ts`, as they are not included by default.
**Prevention:** Always enforce a strong CSP and other security headers at the application framework level, even if the application is purely API-driven.

## 2025-02-24 - [DAV Path Traversal Vulnerability]
**Vulnerability:** A path traversal vulnerability existed in the `/dav/{path:path}` endpoint where `_dav_path_owner_user_id` extracted the owner user ID using `path.partition("/")` without validating or normalizing `..` segments.
**Learning:** This allowed an attacker to supply a path like `my_user_id/../other_user_id/projects`, tricking the authorization check `_ensure_dav_owner_scope` into passing because the first segment matched their authenticated `user_id`. The remaining path could then be used downstream to access resources of `other_user_id`. When testing this against FastAPI's TestClient, the TestClient normalizes `../` automatically; `..%2F` must be used to test the router correctly.
**Prevention:** Always validate or normalize dynamic paths used for authorization constraints, explicitly rejecting paths containing traversal segments like `..` before parsing hierarchical data.

## YYYY-MM-DD - Authentication Bypass in Dashboard Routing
**Vulnerability:** Client-side DashboardLayout lacked proper route protection, allowing unauthenticated access to protected routes like '/settings' and relying on a hardcoded session ('Seongho').
**Learning:** Client-side routing without an overarching layout guard allows users to navigate to protected views. Hardcoded data bypasses session enforcement.
**Prevention:** Integrate a session verification hook (e.g., `fetch('/auth/session')`) within the root layout component and block rendering until authentication state is confirmed. Redirect unauthenticated users.

## YYYY-MM-DD - Missing Authentication Middleware
**Vulnerability:** Client-side routing left the application without server-side authentication protection.
**Learning:** Client-side only checks in components like `DashboardLayout` are insufficient. A security scanner (Strix) flagged it as CVSS 9.8 because routes were still accessible via direct requests.
**Prevention:** Implement a server-side `middleware.ts` verifying session cookies using `normalizeSessionToken` before forwarding requests to protected Next.js routes.

## YYYY-MM-DD - XSS Vulnerability in Global Search
**Vulnerability:** The global search input field `globalSearchQuery` bound user input directly without sanitization, posing an XSS risk if the value were to be reflected unsafely elsewhere.
**Learning:** Even if React naturally escapes text node children, automated scanners (like STRIX) and defense-in-depth principles require explicit sanitization for user inputs, especially search fields.
**Prevention:** Use an existing sanitization utility like `toSafeReactText` to strip dangerous control characters from user input before updating component state.
