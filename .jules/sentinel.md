## 2026-05-28 - Missing Default Security Headers in FastAPI
**Vulnerability:** The FastAPI application was missing standard HTTP security headers such as Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options, and Content-Security-Policy in its default responses.
**Learning:** By default, FastAPI does not automatically inject these defense-in-depth headers, leaving the application potentially more susceptible to MIME-sniffing, clickjacking, and injection downgrade paths. X-XSS-Protection is deprecated by major browsers and should not be the default XSS control.
**Prevention:** Always add a global middleware (e.g., via `@app.middleware("http")` or dedicated security middleware plugins) early in the FastAPI application setup to enforce standard security headers across all endpoints, and use a configurable Content-Security-Policy as the modern XSS and framing control.
## 2025-02-28 - DAV Log Injection
**Vulnerability:** Log Injection / Terminal Escape Sequence Injection (CWE-117)
**Learning:** Custom logic like `path.replace("\n", "").replace("\r", "")` is insufficient to prevent log injection and terminal escape sequence injection, as it leaves characters like ANSI color codes intact.
**Prevention:** Use standard mechanisms like `repr()` or proper unicode escaping instead of custom string replacements.
## 2026-06-09 - Insecure XML Parsing in Tests
**Vulnerability:** Found `xml.etree.ElementTree.fromstring` being used to parse HTTP responses in `backend/tests/test_dav_api.py`.
**Learning:** Using the standard library `xml.etree` module for parsing untrusted or external XML data exposes the application to XML External Entity (XXE) and XML bomb attacks (CWE-20). This was flagged by static analysis tools (Bandit B314).
**Prevention:** Always use `defusedxml.ElementTree` instead of `xml.etree.ElementTree` when parsing XML to ensure protection against XML vulnerabilities. Ensure `defusedxml` is listed in `requirements.txt`.
## 2024-06-16 - Insufficient HMAC Secret Entropy
**Vulnerability:** The application accepted short or low-entropy strings for the JWT `AUTH_SESSION_HMAC_SECRET`, leaving tokens vulnerable to offline brute-force and forgery attacks.
**Learning:** Checking string length (e.g., >= 32 bytes) is insufficient to prevent weak secrets if the string lacks cryptographic entropy (e.g., using repeated characters or simple dictionary words like "password").
**Prevention:** In addition to length checks, validate cryptographic secrets using Shannon entropy or a dedicated key derivation/validation library during application startup to ensure they are randomly generated and secure.
