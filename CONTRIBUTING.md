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

Release and CI/CD changes must also run:

```bash
cd backend
DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python -m pytest tests/test_release_governance.py tests/test_repo_hygiene.py -q
POSTGRES_PASSWORD=change-me-local-only docker compose config --quiet
```

Do not treat warnings, deprecations, notices, denied messages, or fatal logs as
successful output. Fix the root cause or file a Korean blocker issue with the
exact run URL/command evidence.

## Threading changes

- Add or update tests before production code changes.
- Keep `backend/services/threading_service.py` as the only canonical thread assignment owner.
- Keep fixtures in `backend/tests/fixtures` small and synthetic; do not commit real email data.
- Preserve honest send semantics: simulated local send is not delivery proof.
- Do not claim multi-user email isolation until the email owner/mailbox migration exists and queries are scoped.

## Secrets and data

Never commit `.env`, real mailbox exports, SMTP credentials, OAuth secrets, OpenAI keys, or user email content. Use synthetic `.eml` fixtures only.

## Mail runner boundary

Naruon is not an email server. It does not provide SMTP, IMAP, MX, or mail relay
services. Internal-only SMTP/IMAP smoke tests must run on the protected
`mail-egress` self-hosted runner through `.github/workflows/mail-smoke.yml`.
