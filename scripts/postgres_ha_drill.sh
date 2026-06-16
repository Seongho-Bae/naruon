#!/usr/bin/env bash
set -euo pipefail

compose_file="${POSTGRES_HA_COMPOSE_FILE:-docker-compose.postgres-ha.yml}"
project_name="${COMPOSE_PROJECT_NAME:-naruon-postgres-ha-drill}"
postgres_db="${POSTGRES_DB:-ai_email}"
postgres_user="${POSTGRES_USER:-postgres}"
primary_port="${POSTGRES_HA_PRIMARY_PORT:-5432}"
replica_port="${POSTGRES_HA_REPLICA_PORT:-5433}"

export POSTGRES_DB="${postgres_db}"
export POSTGRES_USER="${postgres_user}"
export POSTGRES_HA_PRIMARY_PORT="${primary_port}"
export POSTGRES_HA_REPLICA_PORT="${replica_port}"

if [ -z "${POSTGRES_PASSWORD:-}" ]; then
  echo "POSTGRES_PASSWORD must be set before running the PostgreSQL HA drill." >&2
  exit 2
fi

if [ ! -f "${compose_file}" ]; then
  echo "Compose file not found: ${compose_file}" >&2
  exit 2
fi

compose=(docker compose -p "${project_name}" -f "${compose_file}")
marker="naruon_ha_drill_$(date -u +%Y%m%d%H%M%S)_$$"

cleanup() {
  if [ "${POSTGRES_HA_DRILL_KEEP_STACK:-0}" = "1" ]; then
    echo "Keeping PostgreSQL HA drill stack: ${project_name}"
    return
  fi
  "${compose[@]}" down -v >/dev/null
}
trap cleanup EXIT

run_sql() {
  local service="$1"
  local sql="$2"
  "${compose[@]}" exec -T -e "PGPASSWORD=${POSTGRES_PASSWORD}" "${service}" \
    psql -v ON_ERROR_STOP=1 -U "${postgres_user}" -d "${postgres_db}" -Atqc "${sql}"
}

wait_for_sql_result() {
  local service="$1"
  local sql="$2"
  local expected="$3"
  local label="$4"
  local attempt
  local result

  for attempt in $(seq 1 90); do
    result="$(run_sql "${service}" "${sql}" 2>/dev/null || true)"
    if [ "${result}" = "${expected}" ]; then
      echo "ok: ${label}"
      return 0
    fi
    sleep 1
  done

  echo "Timed out waiting for ${label}; last result: ${result:-<empty>}" >&2
  return 1
}

echo "Starting PostgreSQL HA drill stack: ${project_name}"
"${compose[@]}" up -d db-primary db-replica

wait_for_sql_result "db-primary" "SELECT 1" "1" "primary accepts SQL"
wait_for_sql_result "db-replica" "SELECT pg_is_in_recovery()" "t" "replica is in recovery"
wait_for_sql_result "db-primary" "SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END FROM pg_stat_replication" "1" "primary sees pg_stat_replication sender"

run_sql "db-primary" "CREATE EXTENSION IF NOT EXISTS vector;"
run_sql "db-primary" "CREATE TABLE IF NOT EXISTS naruon_ha_drill (drill_marker text PRIMARY KEY, created_at timestamptz NOT NULL DEFAULT now());"
run_sql "db-primary" "INSERT INTO naruon_ha_drill (drill_marker) VALUES ('${marker}') ON CONFLICT DO NOTHING;"

wait_for_sql_result "db-primary" "SELECT COUNT(*) FROM naruon_ha_drill WHERE drill_marker = '${marker}'" "1" "primary marker row exists"
wait_for_sql_result "db-replica" "SELECT COUNT(*) FROM naruon_ha_drill WHERE drill_marker = '${marker}'" "1" "replica replayed marker row"
wait_for_sql_result "db-replica" "SELECT extname FROM pg_extension WHERE extname = 'vector'" "vector" "replica has vector extension state"

readonly_database_url="postgresql+asyncpg://${postgres_user}:<redacted>@db-replica:5432/${postgres_db}"
echo "READONLY_DATABASE_URL=${readonly_database_url}"
echo "Primary DSN remains DATABASE_URL=postgresql+asyncpg://${postgres_user}:<redacted>@db-primary:5432/${postgres_db}"

if [ "${POSTGRES_HA_PROMOTE_REPLICA:-0}" = "1" ]; then
  echo "Promoting db-replica for explicit failover drill."
  "${compose[@]}" exec -T "db-replica" gosu postgres pg_ctl -D /var/lib/postgresql/data promote
  wait_for_sql_result "db-replica" "SELECT pg_is_in_recovery()" "f" "replica promoted out of recovery"
  run_sql "db-replica" "INSERT INTO naruon_ha_drill (drill_marker) VALUES ('${marker}_promoted') ON CONFLICT DO NOTHING;"
  wait_for_sql_result "db-replica" "SELECT COUNT(*) FROM naruon_ha_drill WHERE drill_marker = '${marker}_promoted'" "1" "promoted replica accepts writes"
  echo "Failover validation complete; rebuild a fresh replica before reusing the stack."
else
  echo "Failover promotion skipped. Set POSTGRES_HA_PROMOTE_REPLICA=1 for an explicit promotion drill."
fi
