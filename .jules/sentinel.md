## 2026-05-28 - Missing Default Security Headers in FastAPI
**Vulnerability:** The FastAPI application was missing standard HTTP security headers such as Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options, and Content-Security-Policy in its default responses.
**Learning:** By default, FastAPI does not automatically inject these defense-in-depth headers, leaving the application potentially more susceptible to MIME-sniffing, clickjacking, and injection downgrade paths. X-XSS-Protection is deprecated by major browsers and should not be the default XSS control.
**Prevention:** Always add a global middleware (e.g., via `@app.middleware("http")` or dedicated security middleware plugins) early in the FastAPI application setup to enforce standard security headers across all endpoints, and use a configurable Content-Security-Policy as the modern XSS and framing control.
## 2025-02-28 - DAV Log Injection
**Vulnerability:** Log Injection / Terminal Escape Sequence Injection (CWE-117)
**Learning:** Custom logic like `path.replace("\n", "").replace("\r", "")` is insufficient to prevent log injection and terminal escape sequence injection, as it leaves characters like ANSI color codes intact.
**Prevention:** Use standard mechanisms like `repr()` or proper unicode escaping instead of custom string replacements.
## 2026-05-28 - Overly Permissive CORS Configuration
**Vulnerability:** The CORS policy in `backend/main.py` hardcoded multiple localhost and 127.0.0.1 development ports directly in the list of allowed origins. This permissive setting would be deployed to production, increasing the risk of CSRF or CORS-based attacks if a malicious or compromised application were hosted on the user's localhost.
**Learning:** Hardcoding development origins directly in the production CORS configuration undermines environment separation and exposes production deployments to localized attacks. Settings should dynamically parse allowed origins based on environment variables.
**Prevention:** Introduce an environment-configurable setting (like `ALLOWED_CORS_ORIGINS`) and parse its values to construct the `allow_origins` array, thereby ensuring strict boundary control in production.
