## 2026-05-28 - Missing Default Security Headers in FastAPI
**Vulnerability:** The FastAPI application was missing standard HTTP security headers such as Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options, and Content-Security-Policy in its default responses.
**Learning:** By default, FastAPI does not automatically inject these defense-in-depth headers, leaving the application potentially more susceptible to MIME-sniffing, clickjacking, and injection downgrade paths. X-XSS-Protection is deprecated by major browsers and should not be the default XSS control.
**Prevention:** Always add a global middleware (e.g., via `@app.middleware("http")` or dedicated security middleware plugins) early in the FastAPI application setup to enforce standard security headers across all endpoints, and use a configurable Content-Security-Policy as the modern XSS and framing control.

## 2026-05-30 - Configurable CORS origins enhancement
**Vulnerability:** Permissive Cross-Origin Resource Sharing (CORS) defaults with no environment configuration option to tighten them for production.
**Learning:** Default configuration for CORS Origins was restricted only to localhost instances. While not directly vulnerable in dev, it restricts deployment hardening by omitting a configurable option for production proxy hosts.
**Prevention:** Make `allow_origins` configurable via environment variables (e.g. `ALLOWED_CORS_ORIGINS`) and override default setups when provided, ensuring robust deployment capabilities.
