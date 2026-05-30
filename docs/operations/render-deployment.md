# Render.com Deployment

This runbook describes how to deploy Naruon on Render.com using the
`render.yaml` Blueprint at the repository root.

## Why a Blueprint instead of one Dockerfile

Render's single-service "New Web Service" form has one `Dockerfile Path`
field, which makes it look like only one Dockerfile per repo is supported.
That is a UI limitation, not a platform limitation. Render Blueprints
register many services from a single YAML file, and each service can point
at its own Dockerfile. The Naruon repo ships two Dockerfiles on purpose:

| Component | Dockerfile | Why split |
|---|---|---|
| Backend (FastAPI) | `./Dockerfile` | Python toolchain, `bootstrap_db.py` + `start_backend.py` entrypoint, scaling on CPU/IO. |
| Frontend (Next.js) | `./frontend/Dockerfile` | Node 22 toolchain, Next.js build artifacts, scaling on memory. |

This is the same split used by `docker-compose.yml` and `k8s/*.yaml`,
and it preserves the AGENTS.md boundary that the browser never holds
backend secrets.

## What `render.yaml` declares

* **`naruon-postgres`** — managed Postgres 16 (`basic-256mb` plan).
  Required because the backend uses pgvector and managed Postgres on
  Render supports the `vector` extension.
* **`naruon-backend`** (`type: web`, `runtime: docker`) — builds from
  `./Dockerfile`. Overrides the container `CMD` so `start_backend.py`
  receives Render's injected `$PORT` and so the managed-Postgres URL
  is rewritten to the SQLAlchemy async-driver form
  (`postgresql+asyncpg://...`) that `backend/db/session.py` requires.
  Render Blueprints do not support variable interpolation, so the
  rewrite happens in the start command shell — no code default is
  added to the backend (AGENTS.md rule preserved). The boot path
  still runs through `scripts/start_backend.py`; we never call
  `uvicorn` directly.
* **`naruon-frontend`** (`type: web`, `runtime: docker`) — builds from
  `./frontend/Dockerfile`. Receives the backend's public URL via the
  `BACKEND_INTERNAL_URL` env var, populated from
  `naruon-backend`'s `RENDER_EXTERNAL_URL`. `next.config.ts` reads
  `BACKEND_INTERNAL_URL` at runtime and rewrites `/api/*` to that
  origin. The browser only ever talks to the frontend's own origin, so
  no public identity headers cross the boundary.

  When `BACKEND_INTERNAL_URL` is set explicitly, `next.config.ts`
  enforces SSRF guards before accepting it: the URL must use `https://`
  and the hostname must not fall into a private (RFC 1918), loopback,
  IPv6 ULA/link-local, or cloud metadata (`169.254.0.0/16`) range.
  Render's `RENDER_EXTERNAL_URL` is an HTTPS `*.onrender.com` host and
  satisfies these checks. If the variable is unset, the loopback
  fallback `http://127.0.0.1:8000` is used — this is the intended
  local-dev path only and the guards are intentionally bypassed for
  the no-config case so `docker compose up` keeps working.

## First-time setup

1. Push this branch (with `render.yaml`) to GitHub.
2. In the Render dashboard choose **New → Blueprint** and select the
   `naruon` repo. Render parses `render.yaml` and lists the resources
   it will create.
3. Render prompts for any `sync: false` values. Provide them now:
   * `OPENAI_API_KEY` — your real key, or a placeholder if running
     without OpenAI features.
   You will be able to update or rotate these later from the service's
   **Environment** tab.
4. Confirm the sync. Render provisions `naruon-postgres` first, then
   builds `naruon-backend` and `naruon-frontend` in parallel.
5. **pgvector extension.** `backend/scripts/bootstrap_db.py` runs
   `CREATE EXTENSION IF NOT EXISTS vector` on every boot. If Render's
   application role has the privilege, the first deploy enables the
   extension automatically and there is nothing else to do. If the
   first backend deploy fails with
   `permission denied to create extension "vector"` (or
   `Must be superuser to create this extension`), open the
   database's **Connect** tab in the Render dashboard, click the
   `PSQL Command` button to start a privileged session, run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
   and trigger a redeploy of `naruon-backend`. The bootstrap script
   becomes a no-op for the extension after that.

## Verifying the deploy

1. Visit `https://naruon-backend.onrender.com/` — expect a JSON or HTML
   landing response from FastAPI (the exact body depends on the
   current `/` handler).
2. Visit `https://naruon-frontend.onrender.com/` — the Next.js app
   should render.
3. From the frontend service's URL, exercise a feature that calls
   `/api/...`. The request is rewritten to the backend via
   `BACKEND_INTERNAL_URL`. If the frontend logs a 502 on `/api/*`,
   double-check that `BACKEND_INTERNAL_URL` resolves to the backend's
   `RENDER_EXTERNAL_URL` (visible in the frontend service's
   **Environment** tab).

## Optional: disable background workers on first boot

`backend/main.py` starts the IMAP sync worker in its lifespan. If you
deploy to Render before any tenant has configured IMAP credentials,
the worker logs harmless errors on its retry loop. To silence them
until you are ready, add the following to the **Environment** tab of
`naruon-backend`:

```bash
DISABLE_BACKGROUND_WORKERS=1
```

Remove the variable when you want IMAP sync to run.

## Rotating secrets

* `AUTH_SESSION_HMAC_SECRET` is generated automatically by Render
  (`generateValue: true`, base64-encoded 256-bit value, well over the
  32-byte minimum enforced by `backend/core/runtime_secrets.py`).
  Rotate by deleting the variable in the dashboard and triggering a
  redeploy; Render generates a fresh value. Rotating invalidates all
  in-flight signed sessions, so plan a maintenance window.

  Rare failure mode: the generated value happens to contain a banned
  substring (`change`, `example`, `password`, `secret`) and the
  backend refuses to boot with
  `AUTH_SESSION_HMAC_SECRET must not contain placeholder terms`.
  Delete the variable in the dashboard and redeploy to regenerate.
* `OPENAI_API_KEY` and any other `sync: false` value: edit in the
  service's **Environment** tab. The Blueprint never overrides
  user-supplied secret values on subsequent syncs.

## Local development is unaffected

`docker-compose up` continues to work with no Render-specific
environment variables. `next.config.ts` falls back to
`http://127.0.0.1:8000` when `BACKEND_INTERNAL_URL` is unset, which is
the same loopback the rewrite used before this change.

## What this Blueprint deliberately does not do

* It does not bundle frontend and backend into one container with
  `supervisord` or `nginx` as a reverse proxy. That pattern violates
  the "one container, one process" principle that the rest of the
  repo (Compose, K8s) is built around, and Render does not require
  it.
* It does not modify `Dockerfile`, `frontend/Dockerfile`,
  `docker-compose.yml`, or `k8s/*.yaml`. Those remain the source of
  truth for non-Render environments.
* It does not pin `OPENAI_MODEL` to anything other than the existing
  Compose default. Adjust in the dashboard if your account uses a
  different model.
