## 2025-05-28 - Missing Default Security Headers in FastAPI
**Vulnerability:** The FastAPI application was missing standard HTTP security headers (e.g., Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options, X-XSS-Protection) in its default responses.
**Learning:** By default, FastAPI does not automatically inject these defense-in-depth headers, leaving the application potentially more susceptible to MIME-sniffing, clickjacking, and XSS downgrade attacks.
**Prevention:** Always add a global middleware (e.g., via `@app.middleware("http")` or dedicated security middleware plugins) early in the FastAPI application setup to enforce standard security headers across all endpoints.
