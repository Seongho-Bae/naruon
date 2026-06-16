## 2024-05-24 - Overly Permissive CORS Policy

**Vulnerability:** The CORS configuration in FastAPI allowed wildcards (`*`) for `allow_methods` and `allow_headers`.
**Learning:** This could permit unintended cross-origin interaction, potentially exposing the API to Cross-Site Request Forgery (CSRF) or unintended data exposure, particularly via custom headers or unconventional methods.
**Prevention:** Always restrict `allow_methods` and `allow_headers` in CORS policies to the exact methods and headers required by the application.

## 2026-06-16 - TOCTOU vulnerability in email import service
 **Vulnerability:** The email import service read an email file into bytes and then passed the file path to `parse_eml` which re-opened and re-read the file. This created a TOCTOU race condition where an attacker could swap the file contents between the two reads, leading to mismatched hash generation and contents.
 **Learning:** Reading a file and then passing its path to another function to read it again is a classic TOCTOU pattern.
 **Prevention:** Always perform operations on the initial in-memory byte buffer read from disk rather than re-reading from the filesystem. Use `parse_eml_bytes(content)` instead of `parse_eml(path)` when the content has already been loaded.
