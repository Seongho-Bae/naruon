#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd -P)"

log() {
  printf '[verify-threading] %s\n' "$*" >&2
}

run_backend_checks() {
  log "running backend threading checks"
  (
    cd "${REPO_ROOT}/backend"
    python3 -m pytest \
      tests/test_threading_service.py \
      tests/test_import_fixtures.py \
      tests/test_email_parser.py \
      tests/test_emails_api.py \
      tests/test_email_client.py \
      tests/test_search.py \
      -q
  )
}

ensure_frontend_dependencies() {
  if [[ ! -d "${REPO_ROOT}/frontend/node_modules" ]]; then
    log "frontend dependencies missing; running npm install"
    (
      cd "${REPO_ROOT}/frontend"
      npm install
    )
  fi
}

run_frontend_checks() {
  log "running frontend threading checks"
  ensure_frontend_dependencies
  (
    cd "${REPO_ROOT}/frontend"
    npm test
    npm run lint
    npm run build
  )
}

run_backend_checks
run_frontend_checks
log "threading verification complete"
