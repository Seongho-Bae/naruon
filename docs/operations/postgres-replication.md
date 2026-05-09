# PostgreSQL 물리 복제와 백업 운영 기준

현재 로컬 Compose의 PostgreSQL은 개발용 단일 노드다. 운영 또는 AKS Dev에서
고가용성과 읽기 확장을 말하려면 백업, 복구, replica lag, failover, pgvector
호환성까지 함께 검증해야 한다.

## 권장 운영 경로

1. 운영 기본값은 Azure Database for PostgreSQL Flexible Server와 read replica다.
2. AKS에 PostgreSQL을 직접 올리는 경우에는 operator, PVC, backup, restore drill,
   replica monitoring을 모두 소유할 때만 허용한다.
3. read replica는 백업의 대체재가 아니다.

## 물리 복제 확인 SQL

```sql
select pg_is_in_recovery();
select client_addr, state, sync_state from pg_stat_replication;
select slot_name, active from pg_replication_slots;
```

기대값:

- primary: `pg_is_in_recovery()`가 `false`
- replica: `pg_is_in_recovery()`가 `true`
- replica write는 실패해야 한다.
- replication slot이 무한 WAL 보관으로 디스크를 채우지 않도록 경보가 있어야 한다.

## pgvector 주의 사항

- primary와 replica는 같은 PostgreSQL major version과 호환 pgvector binary를 써야 한다.
- restore 전에 `vector` extension 설치 가능 권한을 확인한다.
- 벡터 인덱스는 운영에서 `CREATE INDEX CONCURRENTLY` 전략으로 관리한다.
- zero-vector fixture는 threading smoke용이지 검색 품질 증거가 아니다.

## 라우팅과 pooler 정책

- `DATABASE_URL`은 primary 전용 DSN이다. migration, schema backfill, write API,
  tenant config, mailbox sync state, send state는 primary-only 경로로만 실행한다.
- `DATABASE_URL_READ_ONLY`는 읽기 전용 API에만 단계적으로 도입한다. 도입 전에는
  query별 tenant filter, stale-read 허용 여부, failover 동작을 테스트한다.
- PgBouncer는 connection pooling 후보지만 transaction pooling에서는 session state,
  prepared statement, advisory lock 사용 여부를 먼저 점검해야 한다.
- PgCat은 read/write split 후보지만 application-level tenant routing과 충돌하지
  않는지 검증해야 한다.
- managed PostgreSQL read replica를 쓰는 경우에도 application이 replica lag를
  감지하거나 stale-read 허용 endpoint를 명시하지 않으면 읽기 분산을 release-ready로
  주장하지 않는다.

## PostgreSQL text 입력 정책

PostgreSQL text/json 계열 값은 NUL byte를 저장할 수 없다. 외부 이메일 본문, header,
LLM 출력, fixture를 저장하기 전 `\u0000` 또는 `\x00` 문자는 제거하거나 U+FFFD 같은
대체 문자로 치환해야 한다. 이 정책은 숨은 데이터 손상이 아니라 DB write 실패를
명시적으로 방지하기 위한 입력 정규화다.

## 릴리스 완료 조건

- Kubernetes manifest는 DB credential을 Secret으로 참조한다.
- app image는 `:latest`가 아니라 검증된 SemVer tag 또는 digest를 쓴다.
- 복구 훈련 결과가 없는 경우 physical replication은 follow-up issue로 남긴다.
- `DATABASE_URL_READ_ONLY`를 도입하더라도 migration, write, tenant config, sync state는
  primary로만 간다.
