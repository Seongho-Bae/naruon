# Contributing

## Setup

1. Copy `.env.example` to `.env`.
2. Prefer `docker compose up -d --build` for full-stack local work.
3. For manual backend work, run commands from `backend/`.
4. For frontend work, run `npm install` before lint/build/test.

## Verification before opening a PR

```bash
./scripts/verify_threading.sh
```

For backend-only changes, run `cd backend && python3 -m pytest -q`. For frontend changes, run `cd frontend && npm test && npm run lint && npm run build`.

## Threading changes

- Add or update tests before production code changes.
- Keep `backend/services/threading_service.py` as the only canonical thread assignment owner.
- Keep fixtures in `backend/tests/fixtures` small and synthetic; do not commit real email data.
- Preserve honest send semantics: simulated local send is not delivery proof.
- Do not claim multi-user email isolation until the email owner/mailbox migration exists and queries are scoped.

## Secrets and data

Never commit `.env`, real mailbox exports, SMTP credentials, OAuth secrets, OpenAI keys, or user email content. Use synthetic `.eml` fixtures only.
