# AI Email Client

Full-stack email client with a FastAPI backend, Next.js frontend, vector search, AI summaries, and hardened email threading.

## Five-minute local path

```bash
cp .env.example .env
POSTGRES_PASSWORD=change-me-local-only API_AUTH_BEARER_TOKEN=change-me-local-token docker compose up -d --build
docker compose exec backend python import_fixtures.py
curl -s -H 'Authorization: Bearer change-me-local-token' http://localhost:8000/api/emails
python3 -m webbrowser http://localhost:3000
```

What you should see: the fixture import loads a three-message `Quarterly plan` conversation. `/api/emails` returns one threaded inbox item with `reply_count` greater than 1, and the frontend shows conversation history oldest to newest.

The fixture importer uses real OpenAI embeddings only when `OPENAI_API_KEY` is set. With the default empty key it writes local zero-vector embeddings so the threading proof path works offline.

## Manual development path

Backend:

```bash
cd backend
python3 -m pip install -r requirements.txt
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
- Importers persist the canonical service-assigned `thread_id`; they do not recompute their own thread IDs.
- Replies include `In-Reply-To` and `References` headers in the send payload.
- Development sends are explicit simulations unless a real SMTP path is wired.

## API smoke examples

```bash
curl -s -H 'Authorization: Bearer change-me-local-token' http://localhost:8000/api/emails | jq '.emails[] | {subject, thread_id, reply_count}'
curl -s -H 'Authorization: Bearer change-me-local-token' http://localhost:8000/api/emails/thread/thread-root@example.com | jq '.thread[] | {message_id, in_reply_to, references}'

# Requires a tenant OpenAI key because search generates a query embedding.
curl -s -X POST http://localhost:8000/api/search -H 'Authorization: Bearer change-me-local-token' -H 'content-type: application/json' -d '{"query":"Quarterly plan"}'

# Send remains honest in local/dev mode: if SMTP is not configured, the API returns 400.
curl -s -X POST http://localhost:8000/api/emails/send \
  -H 'Authorization: Bearer change-me-local-token' \
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

This repo uses configured single-principal bearer authentication and does not persist an owner/mailbox key on email rows. Treat local data as single-user development data until a mailbox ownership migration is added. Configure `API_AUTH_BEARER_TOKEN` or `API_AUTH_BEARER_TOKEN_FILE` on the backend, and set `NEXT_PUBLIC_API_AUTH_TOKEN` only for local browser development because public frontend variables are visible to users.

## Verification used for this hardening pass

```bash
./scripts/verify_threading.sh

# Equivalent manual checks:
cd backend && python3 -m pytest -q
cd frontend && npm test && npm run lint && npm run build
```

Known local warnings: backend tests emit dependency/toolchain deprecation warnings from Starlette multipart and compiled SWIG metadata. They are not caused by threading code.
