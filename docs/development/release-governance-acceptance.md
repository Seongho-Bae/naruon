# 릴리스 거버넌스 Acceptance Criteria

## 북극성

릴리스는 기능 구현이 아니라 증거가 있는 배포 가능 상태다. PR은 이 문서의 항목을
통과하고, GitHub Checks와 current-head robot-review evidence가 같은 head SHA를
가리킬 때만 merge 후보가 된다.

## 필수 기준

- Gitflow: `master`는 보호된 기본 브랜치, 기능/릴리스 작업은 별도 브랜치와 PR로 진행한다.
- 중복 Checks: PR이 열린 branch push와 `pull_request`가 같은 빌드 체크를 중복 표시하지 않도록 push gate는 `master` 중심으로 제한한다.
- Security: Bandit, Strix, dependency audit, GitHub security alerts는 0건 목표다. 단순 억제가 아니라 원인과 호환성을 기록한다.
- Packaging: GHCR backend/frontend 이미지는 SemVer tag와 `linux/amd64`, `linux/arm64` evidence를 가진다.
- Live test: Docker image build부터 서비스 기동, API smoke, frontend reachability까지 이어져야 한다.
- Robot review: human approval을 기본 blocker로 기다리지 않는다. current-head CodeRabbit/robot-review evidence와 required checks를 본다.
- Warning policy: warning, deprecated, notice, denied, fatal은 실패로 보고 원인 추적 또는 명시적 blocker issue를 남긴다.

## 운영 확장 기준

- Open Source APM: `/healthz`, `/readyz`, `/metrics`, Prometheus, Grafana, Loki, Tempo, OTel Collector 구성이 문서와 Compose에 있어야 한다.
- Internal mail runner: Naruon은 이메일 서버가 아니며, 사내망 SMTP/IMAP smoke는 `mail-egress` self-hosted runner에서만 수동 실행한다.
- PostgreSQL: physical replication은 backup/restore, pgvector, replica lag, failover 문서 없이는 완료로 주장하지 않는다.
- 인증/게이트웨이: Keycloak 또는 Casdoor 같은 OIDC provider와 Traefik edge gateway는 운영 follow-up으로 추적한다. mailbox ownership migration 전에는 다중 사용자 production API로 주장하지 않는다.
