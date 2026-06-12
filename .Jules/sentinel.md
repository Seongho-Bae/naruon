## 2026-06-11 - Fastapi CORS Configuration Hardening
**Vulnerability:** Fastapi `allow_origins` for CORS was hardcoded to allow `localhost` in `backend/main.py`.
**Learning:** Hardcoding local domains permits requests from unauthorized local development servers in production, violating secure defaults. Production origins should be strictly injected via environment variables.
**Prevention:** Load CORS allowed origins from an environment variable (like `ALLOWED_CORS_ORIGINS`) via `pydantic-settings` in `core.config.py`, providing local fallback defaults only when the environment variable is not explicitly provided.
