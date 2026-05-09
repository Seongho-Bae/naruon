# Backend

> 나루온 (Naruon) — AI 이메일 워크스페이스의 백엔드 서비스.

FastAPI service for email ingestion, search, AI summaries, calendar sync, and threaded email APIs.

## Setup

```bash
python3 -m pip install -r requirements.txt
python3 scripts/bootstrap_db.py
python3 -m pytest -q
uvicorn main:app --reload
```

Set `DATABASE_URL` in `.env` or use the default `postgresql+asyncpg://postgres:postgres@localhost:5432/ai_email`.

For local fixture imports, `OPENAI_API_KEY` is optional. When absent, `import_fixtures.py` uses zero-vector embeddings so the local threading proof path does not need network access.

## Threading endpoints

- `GET /api/emails` returns inbox items grouped by `thread_id` with `reply_count`.
- `GET /api/emails/{id}` returns message details including `thread_id`, `message_id`, `in_reply_to`, `references`, and `reply_to`.
- `GET /api/emails/thread/{thread_id}` returns the conversation oldest to newest.
- `POST /api/emails/send` accepts `in_reply_to` and `references` and returns either real send status or explicit simulation status.

## Schema bootstrap and backfill

`python3 scripts/bootstrap_db.py` creates the `vector` extension, runs `Base.metadata.create_all` for fresh local databases, and applies idempotent `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statements for the threading columns (`thread_id`, `in_reply_to`, `references`, `reply_to`) plus the thread index. Existing email rows that predate threading should then be backfilled by reprocessing imported `.eml` files or by assigning `thread_id` with `services.threading_service.assign_thread_id` in chronological order.

Before claiming multi-user safety, add an owner/mailbox column to `emails`, backfill it, and scope every email/search query by that key.

## Warning classification

Current backend test warnings are known dependency/toolchain warnings:

- `starlette.formparsers` imports `multipart`, which emits a pending deprecation warning.
- Compiled SWIG metadata emits `__module__` deprecation warnings during import.

Threading code should not add new warnings. Treat any new warning from application modules as a regression.
