## 2024-05-24 - Overly Permissive CORS Policy

**Vulnerability:** The CORS configuration in FastAPI allowed wildcards (`*`) for `allow_methods` and `allow_headers`.
**Learning:** This could permit unintended cross-origin interaction, potentially exposing the API to Cross-Site Request Forgery (CSRF) or unintended data exposure, particularly via custom headers or unconventional methods.
**Prevention:** Always restrict `allow_methods` and `allow_headers` in CORS policies to the exact methods and headers required by the application.

## 2024-05-30 - [Sanitize Internal Error Exposure in Calendar API]
**Vulnerability:** The Calendar API exposed raw exception messages by directly returning `str(e)` in the `HTTPException` detail field upon `CalendarServiceError`. This risked leaking internal operational details and stack traces to clients.
**Learning:** Returning `str(e)` or `str(exc)` in HTTP responses is unsafe and violates defense-in-depth principles. Even wrapped exceptions can carry unexpected stack details.
**Prevention:** Fail securely by using generic user-friendly error messages (e.g., "Failed to sync calendar event") and log the raw exceptions on the server-side via `logger.error(..., exc_info=True)` for safe debugging.
