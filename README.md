# AI Email Client

Full-stack email client with a FastAPI backend, Next.js frontend, vector search, AI summaries, and hardened email threading.

## Five-minute local path

```bash
cp .env.example .env
export ENCRYPTION_KEY="$(python3 -c 'import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())')"
export AUTH_TOKEN_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
python3 -m pip install "PyJWT==2.12.0"
export API_AUTH_TOKEN="$(python3 scripts/create_auth_token.py test_user)"
export API_PROXY_ALLOW_SHARED_TOKEN=true
POSTGRES_PASSWORD=change-me-local-only docker compose up -d --build
docker compose exec backend python import_fixtures.py
curl -s -H "Authorization: Bearer $API_AUTH_TOKEN" http://localhost:8000/api/emails
python3 -m webbrowser http://localhost:3000
```

What you should see: the fixture import loads a three-message `Quarterly plan` conversation. `/api/emails` returns one threaded inbox item with `reply_count` greater than 1, and the frontend shows conversation history oldest to newest.

The fixture importer uses real OpenAI embeddings only when `OPENAI_API_KEY` is set. With the default empty key it writes local zero-vector embeddings so the threading proof path works offline.

`DATABASE_URL` is required and has no hardcoded credential fallback. Point it at a database credential issued by your local environment, Compose `.env`, Kubernetes Secret, or deployment secret manager.

`ENCRYPTION_KEY` is required before writing encrypted tenant secrets. Generate a Fernet-compatible key once per environment and keep it stable for existing data; rotating it requires re-encrypting any stored `TenantConfig` secrets.

`AUTH_TOKEN_SECRET` is required for API authentication. API clients must send a PyJWT-signed bearer token whose subject is the current user and whose `jti` can be blocklisted server-side through `POST /api/auth/revoke`. For local development, `scripts/create_auth_token.py` generates `API_AUTH_TOKEN`; the Next.js frontend keeps it server-side and only enables the shared-token `/api/backend/...` proxy when `API_PROXY_ALLOW_SHARED_TOKEN=true` is set explicitly for local demo use. Production deployments should replace this helper with the deployment identity provider's token issuance path instead of enabling the shared-token proxy.

## Manual development path

Backend:

```bash
cd backend
python3 -m pip install -r requirements.txt
export DATABASE_URL="postgresql+asyncpg://<user>:<password>@localhost:5432/ai_email"
export ENCRYPTION_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
python3 scripts/bootstrap_db.py
python3 -m pytest -q
uvicorn main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm test
npm run lint
npm run build
npm run dev
```

## Threading proof points

- Canonical thread IDs are assigned in `backend/services/threading_service.py`.
- Parser output preserves raw `Message-ID`, `In-Reply-To`, `References`, and `Reply-To` headers.
- Parsed and API-returned email bodies are sanitized server-side as plain text before storage or JSON responses, including inbox, detail, thread, and search snippets.
- Importers persist the canonical service-assigned `thread_id`; they do not recompute their own thread IDs.
- Replies include `In-Reply-To` and `References` headers in the send payload.
- Tenant SMTP endpoints must resolve to public addresses and use standard SMTP ports 25, 465, or 587; development sends are explicit simulations unless a real SMTP path is wired.

## API smoke examples

```bash
curl -s -H "Authorization: Bearer $API_AUTH_TOKEN" http://localhost:8000/api/emails | jq '.emails[] | {subject, thread_id, reply_count}'
curl -s -H "Authorization: Bearer $API_AUTH_TOKEN" http://localhost:8000/api/emails/thread/thread-root@example.com | jq '.thread[] | {message_id, in_reply_to, references}'

# Revoke the current local token by storing its JWT jti until expiration.
curl -s -X POST -H "Authorization: Bearer $API_AUTH_TOKEN" http://localhost:8000/api/auth/revoke

# Requires a tenant OpenAI key because search generates a query embedding.
curl -s -X POST http://localhost:8000/api/search -H "Authorization: Bearer $API_AUTH_TOKEN" -H 'content-type: application/json' -d '{"query":"Quarterly plan"}'

# Send remains honest in local/dev mode: if SMTP is not configured, the API returns 400.
curl -s -X POST http://localhost:8000/api/emails/send \
  -H "Authorization: Bearer $API_AUTH_TOKEN" \
  -H 'content-type: application/json' \
  -d '{"to":"alice@example.com","subject":"Re: Quarterly plan","body":"Thanks","in_reply_to":"<thread-reply-2@example.com>","references":"<thread-root@example.com> <thread-reply-1@example.com> <thread-reply-2@example.com>"}'
```

## Error-message contract

Errors should tell a contributor what failed and avoid leaking internals:

| Flow | Expected signal | Fix |
|---|---|---|
| SMTP not configured | `400 {"detail":"SMTP is not configured"}` | Create a tenant config with SMTP host, port, and username before testing real send. |
| Local simulated send | `{"status":"simulated","simulated":true}` | Treat as payload/header verification only, not delivery proof. |
| Search without OpenAI key | `400 {"detail":"OpenAI API key not configured"}` | Add a tenant OpenAI key or skip search smoke locally. |
| Search backend failure | `500 {"detail":"Search failed"}` | Check backend logs; raw exceptions are intentionally not returned to clients. |
| Missing thread | `404 {"detail":"Thread not found"}` | Re-import fixtures or verify the URL uses the normalized thread id. |

## Current scope contract

The backend requires signed bearer-token authentication, and email rows persist an owner in `emails.user_id`. Email detail, thread, inbox, search, network graph, calendar sync, import, and threading lookups are scoped to the authenticated token subject; production deployments must issue these tokens from a trusted identity boundary rather than the local helper.

## Verification used for this hardening pass

```bash
./scripts/verify_threading.sh

# Equivalent manual checks:
cd backend && python3 -m pytest -q
cd frontend && npm test && npm run lint && npm run build
```

Known local warnings: backend tests emit dependency/toolchain deprecation warnings from Starlette multipart and compiled SWIG metadata (`SwigPy*` / `swigvarlink`). They are not caused by threading code.
