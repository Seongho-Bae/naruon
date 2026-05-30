## 2026-05-28 - Missing Default Security Headers in FastAPI
**Vulnerability:** The FastAPI application was missing standard HTTP security headers such as Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options, and Content-Security-Policy in its default responses.
**Learning:** By default, FastAPI does not automatically inject these defense-in-depth headers, leaving the application potentially more susceptible to MIME-sniffing, clickjacking, and injection downgrade paths. X-XSS-Protection is deprecated by major browsers and should not be the default XSS control.
**Prevention:** Always add a global middleware (e.g., via `@app.middleware("http")` or dedicated security middleware plugins) early in the FastAPI application setup to enforce standard security headers across all endpoints, and use a configurable Content-Security-Policy as the modern XSS and framing control.
## 2026-05-28 - Missing Referrer-Policy and Frontend noopener
**Vulnerability:** Missing `Referrer-Policy: strict-origin-when-cross-origin` in the backend API and missing `noopener` on `target="_blank"` anchors on the frontend.
**Learning:** `noreferrer` on external links implicitly covers `noopener` in modern browsers, but explicitly adding both alongside `target="_blank"` is standard defense-in-depth against reverse tabnabbing. Missing `Referrer-Policy` could leak information in referer headers.
**Prevention:** Enforce `Referrer-Policy` globally via FastAPI middleware and explicitly mandate `noopener noreferrer` on `target="_blank"` React anchors.
