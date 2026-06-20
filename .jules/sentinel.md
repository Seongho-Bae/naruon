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
## 2026-06-20 - Missing Auth on update_tenant_config (Already Mitigated)
**Vulnerability:** A previous state of the codebase was reported to be missing `Depends(get_auth_context)` on `update_tenant_config`.
**Learning:** `auth_ctx: AuthContext = Depends(get_auth_context)` is already correctly implemented in the endpoint signature.
**Prevention:** Always rely on FastAPI dependency injection to enforce endpoint security.
