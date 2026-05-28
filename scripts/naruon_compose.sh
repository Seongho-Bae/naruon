#!/usr/bin/env bash
set -euo pipefail

if [ -n "${NARUON_ENV_FILE:-}" ]; then
  env_file="${NARUON_ENV_FILE}"
elif [ -f "${HOME}/.env" ]; then
  env_file="${HOME}/.env"
else
  env_file=".env"
fi

if [ ! -f "${env_file}" ]; then
  cat >&2 <<EOF
Error: Naruon compose env file not found: ${env_file}
Set NARUON_ENV_FILE=/path/to/env or create ${HOME}/.env.
EOF
  exit 1
fi

for arg in "$@"; do
  if [ "${arg}" = "--env-file" ]; then
    exec docker compose "$@"
  fi
done

exec docker compose --env-file "${env_file}" "$@"
