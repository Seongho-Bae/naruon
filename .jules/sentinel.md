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
## 2025-02-28 - Insecure CORS Default Fix
**Vulnerability:** The default for `ALLOWED_CORS_ORIGINS` in Pydantic Settings was set to an empty string (`""`). This is overly permissive (or rather, overly implicit and insecure fallback behavior) because an unconfigured deployment would not explicitly force the operator to define CORS origins, leading to potential misconfigurations or users overriding checks with wildcard fallbacks due to friction.
**Learning:** Empty string defaults for critical security settings like CORS bypass the explicit requirement validation of Pydantic. It's better to make critical list-based security policies explicitly required by omitting the default so it fails securely and noticeably upon startup.
**Prevention:** Remove default values like `= ""` or `= []` for strictly required security lists in application settings (e.g. `ALLOWED_CORS_ORIGINS: str`) to mandate explicit environment configuration.
