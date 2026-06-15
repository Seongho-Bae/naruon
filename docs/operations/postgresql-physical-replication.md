# PostgreSQL Physical Replication and WAL Plan

## 확인된 사실 / Confirmed

- `docker-compose.yml` runs a single `pgvector/pgvector:pg16` database service.
- `k8s/db-statefulset.yaml` has `replicas: 1`, so Kubernetes manifests are also
  single-primary only today.
- `docker-compose.postgres-ha.yml` has been added to model a primary-replica streaming configuration for evaluation.
- The backend accepts optional `READONLY_DATABASE_URL`. When it is blank or
  unset, read-only sessions fall back to `DATABASE_URL`; when it is set, the
  backend builds a separate read-only SQLAlchemy session factory for replica
  reads.

## 물리 복제 및 WAL 백업 운영 (Issue #137)

- **Streaming Replication (HA 기반):** `db-primary` 노드에서 `wal_level=replica`로 동작하며 `db-replica`가 `pg_basebackup` 후 지속적으로 WAL 스트림을 수신하는 구조가 마련되었습니다.
- **Failover / RTO 경계:** 현재 구성은 읽기 전용 확장(Read Replica)을 위한 것으로, 자동 Failover(Patroni, Repmgr)까지는 도입되지 않은 원시 HA(Raw High Availability) 스택입니다.
- **Read-only DSN 라우팅:** 로컬 단일-primary Compose는
  `READONLY_DATABASE_URL`을 빈 값으로 전달해 primary fallback을 사용합니다.
  HA 평가 환경에서는 예를 들어
  `postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@db-replica:5432/ai_email`
  처럼 replica DSN을 주입해 `get_readonly_db()` 경로를 replica로 분리할 수
  있습니다.
- **Drill script:** `scripts/postgres_ha_drill.sh` starts the HA Compose stack,
  verifies the primary accepts SQL, verifies the replica reports
  `pg_is_in_recovery()`, confirms the primary sees `pg_stat_replication`, writes
  a `naruon_ha_drill` marker row on the primary, waits until the replica replays
  the marker row and `vector` extension state, and prints the redacted
  `READONLY_DATABASE_URL` value to use for backend read-only routing. It does not
  use a default database password.
- **2026-06-15 drill evidence:** `docs/operations/postgresql-ha-drill-20260615.md`
  records a completed local drill with `pg_basebackup`, replica recovery,
  marker-row replay, `vector` extension replay, redacted `READONLY_DATABASE_URL`
  evidence, explicit replica promotion, and promoted-replica write validation.
- **백업(Backup):** 향후 pgBackRest 또는 WAL-G를 이용해 WAL 로그를 오브젝트 스토리지(S3 등)로 아카이빙(Archive)하는 것이 프로덕션 투입 전 블로커입니다.

## Drill command

```bash
POSTGRES_PASSWORD='<operator-secret>' ./scripts/postgres_ha_drill.sh
```

Set `POSTGRES_HA_PROMOTE_REPLICA=1` only for a destructive promotion drill. A
promotion drill verifies that the replica exits recovery and accepts writes, then
the stack must be rebuilt before it is reused as a primary/replica topology.

## 검증 체크리스트

- Capture base backup and WAL archive location.
- Restore into an isolated environment and verify `CREATE EXTENSION vector` state.
- Check `pg_is_in_recovery()` on replicas.
- Point `READONLY_DATABASE_URL` at the replica and verify read-only backend
  queries use the replica DSN while writes continue using `DATABASE_URL`.
- Record failover boundaries, RPO/RTO, and rollback steps.
- Attach the completed `scripts/postgres_ha_drill.sh` output to release
  evidence for every new HA topology change.
- Before claiming production automated HA, add and verify object-store WAL
  archive/restore drills and the selected failover coordinator policy.
