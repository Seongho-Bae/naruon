# Backend

FastAPI service for email ingestion, search, AI summaries, calendar sync, and threaded email APIs.

## Setup

```bash
python3 -m pip install -r requirements.txt
export DATABASE_URL="postgresql+asyncpg://<user>:<password>@localhost:5432/ai_email"
export ENCRYPTION_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
export AUTH_TOKEN_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export API_AUTH_TOKEN="$(python3 ../scripts/create_auth_token.py test_user)"
python3 scripts/bootstrap_db.py
python3 -m pytest -q
uvicorn main:app --reload
```

Set `DATABASE_URL` in `.env`, your shell, Docker Compose, Kubernetes Secret, or a deployment secret manager. The backend refuses to start without an explicit value and rejects the insecure `postgres:postgres` default credential pair. The sample Kubernetes deployment reads this from `ai-email-client-secrets` key `database-url`.
Set `ENCRYPTION_KEY` before creating or reading encrypted tenant secrets. Keep this Fernet-compatible key stable for existing data; key rotation requires re-encrypting stored `TenantConfig` secret fields.
Set `AUTH_TOKEN_SECRET` before serving protected API routes. Local smoke requests should send `Authorization: Bearer $API_AUTH_TOKEN`; production should issue equivalent PyJWT signed bearer credentials from a real identity provider. Tokens include `jti` IDs so compromised credentials can be invalidated through `POST /api/auth/revoke`, which records the current token ID in the server-side revocation table until expiration.

For local fixture imports, `OPENAI_API_KEY` is optional. When absent, `import_fixtures.py` uses zero-vector embeddings so the local threading proof path does not need network access.

## Threading endpoints

- `POST /api/auth/revoke` invalidates the current bearer token by persisting its JWT `jti`.
- `GET /api/emails` returns inbox items grouped by `thread_id` with `reply_count`.
- `GET /api/emails/{id}` returns message details including `thread_id`, `message_id`, `in_reply_to`, `references`, and `reply_to`.
- `GET /api/emails/thread/{thread_id}` returns the conversation oldest to newest.
- `POST /api/emails/send` accepts `in_reply_to` and `references` and returns either real send status or explicit simulation status.

## Schema bootstrap and backfill

`python3 scripts/bootstrap_db.py` creates the `vector` extension, runs `Base.metadata.create_all` for fresh local databases, and applies idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statements for the threading columns (`thread_id`, `in_reply_to`, `references`, `reply_to`) plus the thread index. Fresh databases also include `revoked_auth_tokens` for JWT `jti` blocklist entries. Existing email rows that predate threading should then be backfilled by reprocessing imported `.eml` files or by assigning `thread_id` with `services.threading_service.assign_thread_id` in chronological order.

Email rows include an owner column, and user-facing email/search/network/calendar routes require the authenticated token subject. HTML email bodies are sanitized server-side before storage and again before JSON responses, including search snippets, so clients receive text-safe content even if old rows contain raw HTML.

## Warning classification

Current backend test warnings are known dependency/toolchain warnings:

- `starlette.formparsers` imports `multipart`, which emits a pending deprecation warning.
- Compiled SWIG metadata emits `__module__` deprecation warnings during import (`SwigPy*` / `swigvarlink`).

Threading code should not add new warnings. Treat any new warning from application modules as a regression.
