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
- Access control is universal RBAC plus ABAC: data-region, consent, workspace,
  group, source capability, and customer-policy denies take precedence over broad
  role allows. A permitted `platform_admin` can cross organization and resource
  ownership boundaries for platform operations, but not data-region or consent
  denies.
- Keycloak is the default enterprise OIDC evaluation target; Casdoor remains a
  lighter alternative. Traefik and OpenTelemetry are evaluated for edge policy and
  open-source observability.
- PR automation is metadata-only and uses current-head robot-review evidence plus
  required checks. Human approval is not awaited by default under repo policy.
  
## Agentic Ontology & Auto-Organization (Planned)

- **DAG Ontology**: The system evaluates a Directed Acyclic Graph (DAG) for sender relationships to determine "what this sender means to the user", allowing the AI Agent to decide subsequent tasks based on dynamic relationship contexts.
- **Self-Sent Knowledge Indexing**: Emails sent to oneself are automatically parsed and structured into the connected WebDAV/Notes repository, creating a seamless personal knowledge base.

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
First-run frontend sessions open the Today execution dashboard by default, with
explicit entry points to the email workspace and calendar-first workspace.

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

The backend accepts only signed bearer sessions. For local smoke tests, generate
a local-only `AUTH_SESSION_HMAC_SECRET`, start the API with that exact value, and
then mint a short-lived fixture token from the same shell:

```bash
export AUTH_SESSION_HMAC_SECRET="$(python3 - <<'PY'
import secrets

print(secrets.token_urlsafe(48))
PY
)"
export NARUON_DEV_BEARER="$(python3 - <<'PY'
import base64, hashlib, hmac, json, os, time

secret = os.environ["AUTH_SESSION_HMAC_SECRET"].encode()
payload = {
    "ver": 1,
    "iss": "naruon-control-plane",
    "aud": "naruon-api",
    "sub": "default",
    "role": "organization_admin",
    "org": "default",
    "groups": [],
    "workspace": "default",
    "exp": int(time.time()) + 300,
}
enc = lambda raw: base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
header = enc(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
body = enc(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
sig = enc(hmac.new(secret, f"{header}.{body}".encode(), hashlib.sha256).digest())
print(f"{header}.{body}.{sig}")
PY
)"
```

```bash
curl -s http://localhost:8000/api/emails \
  -H "Authorization: Bearer $NARUON_DEV_BEARER" \
  | jq '.emails[] | {subject, thread_id, reply_count}'
curl -s http://localhost:8000/api/emails/thread/thread-root@example.com \
  -H "Authorization: Bearer $NARUON_DEV_BEARER" \
  | jq '.thread[] | {message_id, in_reply_to, references}'

# Requires a tenant OpenAI key because search generates a query embedding.
curl -s -X POST http://localhost:8000/api/search \
  -H "Authorization: Bearer $NARUON_DEV_BEARER" \
  -H 'content-type: application/json' \
  -d '{"query":"Quarterly plan"}'

# Send remains honest in local/dev mode: missing SMTP config returns 400.
curl -s -X POST http://localhost:8000/api/emails/send \
  -H "Authorization: Bearer $NARUON_DEV_BEARER" \
  -H 'content-type: application/json' \
  -d '{"to":"alice@example.com","subject":"Re: Quarterly plan","body":"Thanks"}'

# Convert email-derived execution items into source-linked ticket tasks.
TASK_BODY="$(cat <<'JSON'
{
  "source_email_id": "<root@example.com>",
  "thread_id": "thread-root@example.com",
  "items": ["담당자 확인"]
}
JSON
)"
curl -s -X POST http://localhost:8000/api/tasks/from-email \
  -H "Authorization: Bearer $NARUON_DEV_BEARER" \
  -H 'content-type: application/json' \
  -d "$TASK_BODY"

# Request a customer-owned calendar writeback intent. This selects a trusted
# server-side source and returns no provider secret or direct write proof.
curl -s -X POST http://localhost:8000/api/calendar/writeback-intent \
  -H "Authorization: Bearer $NARUON_DEV_BEARER" \
  -H 'content-type: application/json' \
  -d '{"action":"create","summary":"담당자 확인 회의"}'
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
- Task creation from a missing or unauthorized source email:
  `404 {"detail":"Source email not found"}`.
- Task creation without usable execution items:
  `422 {"detail":"At least one execution item is required"}`.
- Calendar writeback with no trusted customer-owned CalDAV/CardDAV/WebDAV source:
  `422 {"detail":"No customer-owned writeback source is available"}`. The
  frontend must show this as a writeback-intent failure, not as a completed
  provider calendar write.

## Current scope contract

Runtime auth no longer trusts public `X-User-*`, `X-Organization-*`,
`X-Group-*`, or `X-Dev-Auth-Token` headers. Email rows now carry a nullable
`user_id` owner key, and email/search/network graph endpoints scope reads to the
authenticated user. Local bootstrap and fixture imports default that owner to
`default`; production
multi-user use still needs a verified OIDC provider plus an audited
mailbox-owner migration/backfill before real tenant data is mixed.

The current frontend shell now exposes the north-star workspace map in the
primary and mobile menus: Today dashboard, Mail, Calendar, Tasks, Projects,
Context Search, AI Hub, Data, Security, and Settings. The `/mail`, `/search`,
`/tasks`, `/calendar`, `/projects`, `/ai-hub`, `/data`, `/security`, and
`/settings` destinations must render real work-detail surfaces rather than
static placeholder copy: calendar month/week/detail/coordination and CalDAV
writeback queues, ticket task boards and source-linked details, integrated
search result/detail graph timelines, project decision logs, document
repository/ingestion/embedding/quality queues, security dashboards and policy
screens, and operational settings. Provider write execution and enterprise
identity remain future connector/auth slices until source-backed integrations
exist. Browser writes to signed backend routes use the stored
`naruon_session_token` as an `Authorization: Bearer` session, and the frontend
API client strips public identity headers such as `X-User-Id` and
`X-Organization-Id`, including group and dev-token variants, rather than
forwarding development identity fallbacks.

Email-derived work is tracked through `/api/tasks/from-email`. Created ticket
tasks retain an internal source-email foreign key, expose source message/thread
provenance, sanitize NUL bytes from LLM/email-derived titles, and return opaque
public task ids instead of exposing database integer surrogates. The new
`ticket_tasks` table keeps database names two-word `snake_case` such as
`task_id`, `task_title`, `status_code`, and `priority_code`.

Calendar actions in `EmailDetail` now request `/api/calendar/writeback-intent`
for each extracted execution item and display the selected trusted source
provenance. The browser no longer claims `/api/calendar/sync` success from the
mail-detail action path; direct provider writes stay deferred until connector and
source registry work can enforce ETag/If-Match and owner capability checks.

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

Additional focused checks for the current workspace/task/governance slice:

```bash
cd backend && \
  PYTHONDONTWRITEBYTECODE=1 DISABLE_BACKGROUND_WORKERS=1 \
  pytest tests/test_tasks_api.py -q
cd frontend && npm test -- \
  src/lib/api-client.test.ts \
  src/lib/workspace-preferences.test.ts \
  src/components/DashboardLayout.test.tsx \
  src/app/calendar/page.test.tsx \
  src/app/tasks/page.test.tsx \
  src/app/search/page.test.tsx \
  src/app/projects/page.test.tsx \
  src/app/data/page.test.tsx \
  src/app/security/page.test.tsx \
  src/app/page.test.tsx \
  src/components/EmailDetail.test.tsx
cd frontend && LIVE_BASE_URL=http://127.0.0.1:18081 npm run test:e2e -- tests/e2e/dashboard-branding.spec.ts
bash scripts/ci/test_pr_governance_gate.sh
```

Known local warnings: backend tests emit dependency/toolchain deprecation warnings
from Starlette multipart and compiled SWIG metadata. They are not caused by
threading code.
