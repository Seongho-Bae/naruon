#!/usr/bin/env bash
set -euo pipefail

cat >>"${PGDATA}/pg_hba.conf" <<'EOF'
host replication all all scram-sha-256
EOF
