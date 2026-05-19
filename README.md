# Naruon AI Email Workspace

Full-stack AI workspace with a FastAPI backend, Next.js frontend, vector search,
AI summaries, hardened email threading, and relay/proxy contracts for external
mail/calendar/file systems.

## North-star scope contract

- Naruon is not an SMTP server, IMAP server, MX host, or mailbox capacity
  provider. It is a web client/control plane that works through member-configured
  providers and customer-owned systems.
- Customer mail, CalDAV/CardDAV, and WebDAV accounts remain the source of truth;
  Naruon stores bounded metadata, indexes, preferences, and auditable action
  intent rather than replacing those systems.
- Private-network protocols use an outbound-only self-hosted connector to
  `naruon.net`; GitHub self-hosted runners are CI smoke infrastructure, not the
  production connector itself.
- Calendar/file/contact writeback is opt-in, server-authoritative, and
  conflict-aware through source capabilities, provenance, ETags/If-Match, and
  audit logs.
- Access control is universal RBAC plus ABAC: data-region, consent, delegation,
  workspace, group, and ownership denies take precedence over broad role allows.
- Keycloak is the default enterprise OIDC evaluation target; Casdoor remains a
  lighter alternative. Traefik and OpenTelemetry are evaluated for edge policy and
  open-source observability.
- PR automation is metadata-only and uses current-head robot-review evidence plus
  required checks. Human approval is not awaited by default under repo policy.

## Five-minute local path

```bash
cp .env.example .env
POSTGRES_PASSWORD=change-me-local-only docker compose up -d --build
docker compose exec backend python import_fixtures.py
curl -s http://localhost:8000/api/emails
python3 -m webbrowser http://localhost:3000
```

What you should see: the fixture import loads a three-message `Quarterly plan`
conversation. `/api/emails` returns one threaded inbox item with `reply_count`
greater than 1, and the frontend shows conversation history oldest to newest.

The fixture importer uses real OpenAI embeddings only when `OPENAI_API_KEY` is
set. With the default empty key it writes local zero-vector embeddings so the
threading proof path works offline.

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
- Parser output preserves raw `Message-ID`, `In-Reply-To`, `References`, and
  `Reply-To` headers.
- Importers persist the canonical service-assigned `thread_id`; they do not
  recompute their own thread IDs.
- Replies include `In-Reply-To` and `References` headers in the send payload.
- Development sends are explicit simulations unless a real SMTP path is wired.

## API smoke examples

```bash
curl -s http://localhost:8000/api/emails \
  | jq '.emails[] | {subject, thread_id, reply_count}'
curl -s http://localhost:8000/api/emails/thread/thread-root@example.com \
  | jq '.thread[] | {message_id, in_reply_to, references}'

# Requires a tenant OpenAI key because search generates a query embedding.
curl -s -X POST http://localhost:8000/api/search \
  -H 'content-type: application/json' \
  -d '{"query":"Quarterly plan"}'

# Send remains honest in local/dev mode: missing SMTP config returns 400.
curl -s -X POST http://localhost:8000/api/emails/send \
  -H 'content-type: application/json' \
  -d '{"to":"alice@example.com","subject":"Re: Quarterly plan","body":"Thanks"}'
```

## Error-message contract

Errors should tell a contributor what failed and avoid leaking internals:

- SMTP not configured: `400 {"detail":"SMTP is not configured"}`. Create a
  tenant config with SMTP host, port, and username before testing real send.
- Local simulated send: `{"status":"simulated","simulated":true}`. Treat as
  payload/header verification only, not delivery proof.
- Search without OpenAI key: `400 {"detail":"OpenAI API key not configured"}`.
  Add a tenant OpenAI key or skip search smoke locally.
- Search backend failure: `500 {"detail":"Search failed"}`. Check backend logs;
  raw exceptions are intentionally not returned to clients.
- Missing thread: `404 {"detail":"Thread not found"}`. Re-import fixtures or
  verify the URL uses the normalized thread id.

## Current scope contract

Runtime auth no longer trusts public `X-User-*`, `X-Organization-*`,
`X-Group-*`, or `X-Dev-Auth-Token` headers. Email rows now carry a nullable
`user_id` owner key, and email/search/network graph endpoints scope reads to the
authenticated user. Local bootstrap and fixture imports default that owner to
`default`; production
multi-user use still needs a verified OIDC provider plus an audited
mailbox-owner migration/backfill before real tenant data is mixed.

## Operations and release docs

- `docs/operations/release-deployment-architecture.md`: release, CI, GHCR, and
  live E2E evidence path.
- `docs/operations/open-source-apm.md`: OpenTelemetry, Prometheus, Grafana, Loki,
  Tempo/Jaeger adoption plan.
- `docs/operations/email-relay-proxy-boundary.md`: Naruon is a web client
  relay/proxy, not an email server.
- `docs/operations/source-of-truth-and-writeback-sovereignty.md`: customer-owned
  source-of-truth, connector, writeback, and audit rules.
- `docs/operations/postgresql-physical-replication.md`: physical replication,
  WAL, restore, and read-routing plan.
- `docs/operations/auth-key-management.md`: auth boundary, Fernet key management,
  and Keycloak/Casdoor evaluation.
- `docs/operations/traefik-evaluation.md`: Traefik versus current NGINX ingress
  evaluation.
- `docs/development/merge-gate-policy.md`: metadata-only PR governance,
  current-head CodeRabbit evidence, and required-check behavior.

## Verification used for this hardening pass

```bash
./scripts/verify_threading.sh

# Equivalent manual checks:
cd backend && python3 -m pytest -q
cd frontend && npm test && npm run lint && npm run build
```

Known local warnings: backend tests emit dependency/toolchain deprecation warnings
from Starlette multipart and compiled SWIG metadata. They are not caused by
threading code.
