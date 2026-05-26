# Backend

FastAPI service for email ingestion, search, AI summaries, calendar sync, and
threaded email APIs.

## Setup

```bash
python3 -m pip install -r requirements.txt
python3 scripts/bootstrap_db.py
python3 -m pytest -q
uvicorn main:app --reload
```

Set `DATABASE_URL` explicitly through `.env`, Docker Compose, CI secrets, or the
runtime environment. The backend has no code default for the database URL and
fails closed when it is missing.

Outbound SMTP also fails closed unless the normalized tenant SMTP host is listed
in `ALLOWED_SMTP_HOSTS` and the port is listed in `ALLOWED_SMTP_PORTS`.

For local fixture imports, `OPENAI_API_KEY` is optional. When absent,
`import_fixtures.py` uses zero-vector embeddings so the local threading proof
path does not need network access.

## Threading endpoints

- `GET /api/emails` returns inbox items grouped by `thread_id` with `reply_count`.
- `GET /api/emails/{id}` returns message details including `thread_id`,
  `message_id`, `in_reply_to`, `references`, and `reply_to`.
- `GET /api/emails/thread/{thread_id}` returns the conversation oldest to newest.
- `POST /api/emails/send` accepts `in_reply_to` and `references` and returns
  either real send status or explicit simulation status.

## Schema bootstrap and backfill

`python3 scripts/bootstrap_db.py` creates the `vector` extension, runs
`Base.metadata.create_all` for fresh local databases, and applies idempotent
`ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statements for the email owner key
(`user_id`) and threading columns (`thread_id`, `in_reply_to`, `references`,
`reply_to`) plus the owner/thread indexes. Existing email rows that predate
threading should then be backfilled by reprocessing imported `.eml` files or by
assigning `thread_id` with `services.threading_service.assign_thread_id` in
chronological order.

For existing local databases, the bootstrap stamps null `emails.user_id` values
with `NARUON_IMPORT_USER_ID` or `default` so local rows remain visible through
the authenticated-user query scope. Before claiming production multi-user
safety, audit and backfill historical `emails.user_id` values against verified
mailbox owners.

## Warning classification

Backend evidence should be collected with warnings promoted to errors whenever
the slice is under active change:

```bash
PYTHONWARNINGS=error python3 -m pytest -q
```

Historical third-party dependency warnings should be isolated or filtered with
an explicit rationale before merge evidence is accepted:

- `starlette.formparsers` imports `multipart`, which emits a pending deprecation
  warning.
- Compiled SWIG metadata emits `__module__` deprecation warnings during import.

Threading code should not add new warnings. Treat any new application warning
or log output containing `Timeout`, `Fatal`, `Warn`, or `Denied` as a regression.
