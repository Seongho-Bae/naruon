# PostgreSQL Physical Replication and WAL Plan

## 확인된 사실 / Confirmed

- `docker-compose.yml` runs a single `pgvector/pgvector:pg16` database service.
- `k8s/db-statefulset.yaml` has `replicas: 1`, so Kubernetes manifests are also
  single-primary only today.
- `docker-compose.postgres-ha.yml` has been added to model a primary-replica streaming configuration for evaluation.

## 물리 복제 및 WAL 백업 운영 (Issue #137)

- **Streaming Replication (HA 기반):** `db-primary` 노드에서 `wal_level=replica`로 동작하며 `db-replica`가 `pg_basebackup` 후 지속적으로 WAL 스트림을 수신하는 구조가 마련되었습니다.
- **Failover / RTO 경계:** 현재 구성은 읽기 전용 확장(Read Replica)을 위한 것으로, 자동 Failover(Patroni, Repmgr)까지는 도입되지 않은 원시 HA(Raw High Availability) 스택입니다.
- **백업(Backup):** 향후 pgBackRest 또는 WAL-G를 이용해 WAL 로그를 오브젝트 스토리지(S3 등)로 아카이빙(Archive)하는 것이 프로덕션 투입 전 블로커입니다.

## 검증 체크리스트

- Capture base backup and WAL archive location.
- Restore into an isolated environment and verify `CREATE EXTENSION vector` state.
- Check `pg_is_in_recovery()` on replicas.
- Record failover boundaries, RPO/RTO, and rollback steps.
