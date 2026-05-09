# 나루온 (Naruon)

> 흩어진 이메일의 흐름을 건너, 더 나은 판단과 실행으로 나아가게 하는 AI 워크스페이스.

Naruon is an AI email workspace that synthesizes scattered context — mail, attachments, schedules, relationships, decisions — into better judgment and execution.

기술적으로는 FastAPI 백엔드, Next.js 프론트엔드, 벡터 검색, AI 요약, 강건한 이메일 스레딩으로 구성된 풀스택 이메일 클라이언트입니다.

## 왜 나루온인가

**나루**는 물길을 건너는 곳입니다.
이메일도 하나의 물길처럼 계속 흐릅니다. 그 안에는 단순한 텍스트뿐 아니라 사람, 약속, 일정, 책임, 결정, 감정, 리스크가 섞여 있습니다.

나루온은 그 흐름을 단순히 짧게 줄이는 도구가 아닙니다.
흩어진 메일, 첨부, 일정, 관계, 결정 포인트를 하나로 종합해 사용자가 **더 잘 판단하고, 더 잘 실행하고, 더 나은 일과 삶으로 건너가도록 돕는 AI 이메일 워크스페이스**입니다.

뒤의 **on**은 세 가지 의미를 가집니다.

1. 맥락이 **켜진다 (context on).**
2. 일이 다음 행동으로 **이어진다 (continues on).**
3. 사용자가 흐름 위에서 다시 **앞으로 나아간다 (moves on).**

그래서 나루온은 단순한 이메일 앱 이름이 아니라,
**정보의 흐름에서 지혜로운 실행으로 건너가는 장소**라는 뜻을 담고 있습니다.

## About the name (English)

Naruon comes from the Korean word **나루 (naru)**, a crossing point over a river, combined with **on**, meaning context and action switched on. Email is not just a message inbox; it is a stream of work, relationships, decisions, and schedules. Naruon helps users cross that stream by synthesizing scattered context into better judgment and execution.

## Five-minute local path

```bash
cp .env.example .env
POSTGRES_PASSWORD=change-me-local-only docker compose up -d --build
docker compose exec backend python import_fixtures.py
curl -s http://localhost:8000/api/emails
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
curl -s http://localhost:8000/api/emails | jq '.emails[] | {subject, thread_id, reply_count}'
curl -s http://localhost:8000/api/emails/thread/thread-root@example.com | jq '.thread[] | {message_id, in_reply_to, references}'

# Requires a tenant OpenAI key because search generates a query embedding.
curl -s -X POST http://localhost:8000/api/search -H 'content-type: application/json' -d '{"query":"Quarterly plan"}'

# Send remains honest in local/dev mode: if SMTP is not configured, the API returns 400.
curl -s -X POST http://localhost:8000/api/emails/send \
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

This repo still uses dummy header auth and does not persist an owner/mailbox key on email rows. Treat local data as single-user development data until a mailbox ownership migration is added.

## Verification used for this hardening pass

```bash
./scripts/verify_threading.sh

# Equivalent manual checks:
cd backend && python3 -m pytest -q
cd frontend && npm test && npm run lint && npm run build
```

Known local warnings: backend tests emit dependency/toolchain deprecation warnings from Starlette multipart and compiled SWIG metadata. They are not caused by threading code.
