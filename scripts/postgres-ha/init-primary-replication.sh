#!/usr/bin/env bash
set -euo pipefail

cat >>"${PGDATA}/pg_hba.conf" <<'EOF'
# Local HA drill only. Production replication must restrict this rule to a
# dedicated replication role and explicit replica CIDR ranges.
host replication all all scram-sha-256
EOF
