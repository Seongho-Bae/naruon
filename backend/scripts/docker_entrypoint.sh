#!/usr/bin/env bash
# Combined-image entrypoint: starts the Naruon backend (:8000) and frontend
# (:3000) together in a single container. Validates required configuration up
# front and reports which service exits, so a failed start is diagnosable
# instead of silently taking both services down behind a raw stack trace.
set -uo pipefail

log() { printf '[naruon] %s\n' "$*"; }
fail() { printf '[naruon] ERROR: %s\n' "$*" >&2; exit 1; }

log "Starting Naruon combined image (backend :8000, frontend :3000)"

# 1. Validate required runtime configuration before doing any work. These are
#    supplied by the operator/orchestrator and are never generated at runtime.
missing=()
for var in DATABASE_URL AUTH_SESSION_HMAC_SECRET ENCRYPTION_KEY; do
  if [ -z "${!var:-}" ]; then
    missing+=("$var")
  fi
done
if [ "${#missing[@]}" -ne 0 ]; then
  fail "missing required environment: ${missing[*]}. ENCRYPTION_KEY must be a valid Fernet key (generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')."
fi

# 1b. Validate the Fernet key format up front. ENCRYPTION_KEY is otherwise only
#     validated lazily on the first encrypted write, which surfaces as a
#     confusing mid-runtime failure long after the container "came up".
if ! python -c "import os; from cryptography.fernet import Fernet; Fernet(os.environ['ENCRYPTION_KEY'].encode())" 2>/dev/null; then
  fail "ENCRYPTION_KEY is not a valid Fernet key. Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'."
fi

# 1c. Match the backend runtime preflight for the signed-session HMAC secret.
#     Without this, weak secrets fail during bootstrap imports and produce a
#     Pydantic traceback before the operator sees the actionable rule.
if ! python -c "import os; from core.runtime_secrets import validate_auth_session_hmac_secret_value; validate_auth_session_hmac_secret_value(os.environ['AUTH_SESSION_HMAC_SECRET'])" 2>/tmp/naruon-auth-secret-check.log; then
  auth_secret_error="$(tail -n 1 /tmp/naruon-auth-secret-check.log 2>/dev/null || true)"
  rm -f /tmp/naruon-auth-secret-check.log
  fail "${auth_secret_error:-AUTH_SESSION_HMAC_SECRET is invalid. It must be at least 32 bytes, contain at least 12 distinct characters, and use at least three character classes.}"
fi
rm -f /tmp/naruon-auth-secret-check.log

# 2. Bootstrap the database schema. A failure here must be reported with an
#    actionable message rather than just an asyncpg/SQLAlchemy traceback.
log "Bootstrapping database schema..."
if ! python scripts/bootstrap_db.py; then
  fail "database bootstrap failed. Common causes: DATABASE_URL unreachable; ENCRYPTION_KEY is not a valid Fernet key; or existing emails require NARUON_IMPORT_USER_ID and NARUON_IMPORT_ORGANIZATION_ID. Backend and frontend will not start."
fi

# 3. Start backend and frontend, tracking each PID.
log "Starting backend (uvicorn :8000)..."
python scripts/start_backend.py --host 0.0.0.0 --port 8000 &
backend_pid=$!

log "Starting frontend (next start :3000)..."
( cd frontend && exec ./node_modules/.bin/next start --hostname 0.0.0.0 --port 3000 ) &
frontend_pid=$!

terminate() {
  trap - EXIT INT TERM
  log "Shutting down (stopping backend ${backend_pid} and frontend ${frontend_pid})..."
  kill "$backend_pid" "$frontend_pid" 2>/dev/null || true
  wait "$backend_pid" "$frontend_pid" 2>/dev/null || true
}
trap terminate EXIT INT TERM

# 4. Wait for either service to exit and report which one. The container is meant
#    to stop if either critical service dies so an orchestrator can restart it.
wait -n "$backend_pid" "$frontend_pid"
exit_code=$?
if ! kill -0 "$backend_pid" 2>/dev/null; then
  log "Backend (:8000) exited with code ${exit_code}; stopping container."
elif ! kill -0 "$frontend_pid" 2>/dev/null; then
  log "Frontend (:3000) exited with code ${exit_code}; stopping container."
else
  log "A service exited with code ${exit_code}; stopping container."
fi
exit "$exit_code"
