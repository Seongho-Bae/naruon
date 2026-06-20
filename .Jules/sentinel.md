## 2024-06-19 - Insecure Direct Object Reference (IDOR) via Exposed Resource Identifiers
**Vulnerability:** The SecurityLayout dashboard's `/api/security/access-surface` endpoint leaked internal resource identifiers (like `source_id` and `event_uid`) directly to the frontend.
**Learning:** Returning sequential or predictable direct IDs for resources such as WebDAV accounts and audit events exposes internal implementation details and allows attackers to modify IDs to exploit authorization bypasses or IDOR vulnerabilities.
**Prevention:** Always use indirect references or obfuscate identifiers (e.g., using `uuid.uuid5` with a namespace) when exposing resource IDs to the client that aren't strictly required to be exact.
