# PostgreSQL Physical Replication and WAL Plan

## 확인된 사실 / Confirmed

- `docker-compose.yml` runs a single `pgvector/pgvector:pg16` database service.
- `k8s/db-statefulset.yaml` has `replicas: 1`, so Kubernetes manifests are also
  single-primary only today.
- There is no WAL archive, replica slot, backup restore drill, PgBouncer, or
  PgCat configuration in the repository yet.

## 가설 / Hypothesis

- Production should use physical streaming replication plus WAL archive/restore
  drills before claiming HA or disaster recovery readiness.
- Writes, migrations, and DDL should remain primary-only. Read-only traffic can
  be routed to replicas only after `DATABASE_URL_READ_ONLY` or equivalent DSN
  evidence exists.
- Backup drills must prove pgvector extension restore, schema compatibility, and
  replica lag monitoring.

## 검증 체크리스트

- Capture base backup and WAL archive location.
- Restore into an isolated environment and verify `CREATE EXTENSION vector` state.
- Check `pg_is_in_recovery()` on replicas.
- Record failover boundaries, RPO/RTO, and rollback steps.
