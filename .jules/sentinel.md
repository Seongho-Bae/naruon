## 2024-05-24 - Overly Permissive CORS Policy

**Vulnerability:** The CORS configuration in FastAPI allowed wildcards (`*`) for `allow_methods` and `allow_headers`.
**Learning:** This could permit unintended cross-origin interaction, potentially exposing the API to Cross-Site Request Forgery (CSRF) or unintended data exposure, particularly via custom headers or unconventional methods.
**Prevention:** Always restrict `allow_methods` and `allow_headers` in CORS policies to the exact methods and headers required by the application.

## 2024-05-24 - Information Leakage in API Endpoints

**Vulnerability:** Raw exception strings (`str(exc)`) were being returned directly to the client via `HTTPException` details in several API endpoints (`api/emails.py`, `api/tenant_config.py`, `api/calendar.py`).
**Learning:** Returning raw exception strings can expose sensitive internal details, such as stack traces, network configuration paths, or internal validation states, which could aid an attacker in mapping the system architecture or identifying misconfigurations.
**Prevention:** Always catch specific exceptions and return generic, safe error messages to clients (e.g., "Invalid SMTP configuration") rather than relying on `str(exc)`. Log the detailed exception internally for debugging purposes.

## 2024-05-24 - Information Disclosure in Frontend Console

**Vulnerability:** The frontend API client (`ApiClient`) caught errors and re-threw them as standard `Error` objects, maintaining full stack traces which were then printed to the browser console. This could expose internal path structures and function names to a malicious user.
**Learning:** Detailed stack traces should not be exposed in the frontend in a production environment as they leak execution paths and application structure.
**Prevention:** Implement a custom `ApiError` class that overrides the `stack` property (e.g., setting it to an empty string) when running in production (`process.env.NODE_ENV === 'production'`) and use this custom error class for all API interactions.
