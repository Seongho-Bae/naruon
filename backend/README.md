# Backend

FastAPI service for email ingestion, search, AI summaries, calendar sync, and threaded email APIs.

## Setup

```bash
python3 -m pip install -r requirements.txt
python3 scripts/bootstrap_db.py
python3 -m pytest -q
uvicorn main:app --reload
```

Set `DATABASE_URL` in `.env`; the backend fails fast when the database URL is
missing so deployments never fall back to hardcoded credentials.

Encrypted database fields require `ENCRYPTION_KEY`. The key is mandatory and
must come from local `.env`, a mounted secret, or a managed secret store; the
backend does not include a fallback encryption key.

Protected API routes require signed bearer authentication. Set
`API_AUTH_SIGNING_SECRET` or `API_AUTH_SIGNING_SECRET_FILE`; requests must
include `Authorization: Bearer <signed-token>`, where the token is HMAC-signed,
has a non-expired `exp` claim, and carries the authenticated owner in `sub`.
Missing auth configuration fails closed instead of falling back to a dummy user.
Secret files must be regular files no larger than 10 KiB, and invalid
secret-file configuration fails closed with the generic authentication
configuration error.

For local fixture imports, `OPENAI_API_KEY` is optional. When absent, `import_fixtures.py` uses zero-vector embeddings so the local threading proof path does not need network access.

## Threading endpoints

- `GET /api/emails` returns inbox items grouped by `thread_id` with `reply_count`.
- `GET /api/emails/{id}` returns message details including `thread_id`, `message_id`, `in_reply_to`, `references`, and `reply_to`.
- `GET /api/emails/thread/{thread_id}` returns the conversation oldest to newest.
- `POST /api/emails/send` accepts `in_reply_to` and `references` and
  returns either real send status or explicit simulation status. It rejects
  blank message content, blocks unsafe tenant SMTP targets before send
  orchestration, and applies a database-backed per-authenticated-principal
  send rate limit.

## Tenant mail target safety

Tenant-configured SMTP, IMAP, and POP3 destinations are accepted only as bare
hosts with service-specific mail ports (`25`, `465`, `587`, `2525` for SMTP;
`143`, `993` for IMAP; `110`, `995` for POP3). The backend resolves hostnames
before use and rejects any destination that resolves to loopback, private,
link-local, multicast, unspecified, reserved, or otherwise non-public
addresses. The same guard runs when `/api/config` persists mail settings and
before send/sync orchestration. IMAP and POP3 sync remain simulated until real
network use can pin validated DNS results without a second hostname lookup.

## Schema bootstrap and backfill

`python3 scripts/bootstrap_db.py` creates the `vector` extension, runs `Base.metadata.create_all` for fresh local databases, and applies idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statements for the threading columns (`thread_id`, `in_reply_to`, `references`, `reply_to`) plus the thread index. Existing email rows that predate threading should then be backfilled by reprocessing imported `.eml` files or by assigning `thread_id` with `services.threading_service.assign_thread_id` in chronological order.

`API_AUTH_USER_ID` is only the local fixture/bootstrap owner default used when
backfilling existing rows; runtime authorization comes from signed bearer-token
subjects, not this setting.

## Warning classification

Current backend test warnings are known dependency/toolchain warnings:

- `starlette.formparsers` imports `multipart`, which emits a pending deprecation warning.
- Compiled SWIG metadata emits `__module__` deprecation warnings during import.

Threading code should not add new warnings. Treat any new warning from application modules as a regression.
