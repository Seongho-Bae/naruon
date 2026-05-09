# 변경 이력

이 프로젝트의 모든 주요 변경 사항은 이 파일에 기록됩니다.

형식은 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)를 따르며,
버전은 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)을 따릅니다.

## [0.1.0] - 2026-05-09

### 릴리스 요약

- Seongho Bae (@seonghobae)가 조작을 요청한 SWE로서 Release, Deployment,
  Packaging, CI/CD Workflow 거버넌스 기준을 세웠습니다.
- 이 릴리스는 단순 기능 추가가 아니라 Gitflow 기반 배포 가능성, GHCR 패키징,
  보안 게이트, PR 자동 관리, 라이브 Docker 검증, 운영 문서화를 하나의 evidence
  chain으로 묶는 것을 목표로 합니다.
- 기존 기본 브랜치에는 threading 중심의 로컬 검증과 Strix 보안 게이트 문서가
  있었지만, 애플리케이션 CI, 이미지 배포, SemVer release evidence, live smoke,
  open-source APM, self-hosted mail runner, PostgreSQL replication 기준이 분리된
  계약으로 고정되어 있지 않았습니다.

### 추가

- Seongho Bae (@seonghobae)가 `Application CI` GitHub Actions workflow를 추가해
  PR에서 백엔드 pytest, 프론트엔드 Vitest, ESLint, Next production build를 함께
  검증하도록 했습니다.
- Seongho Bae (@seonghobae)가 `Build and Publish Docker Images` workflow를
  backend/frontend image matrix로 확장했습니다.
- Seongho Bae (@seonghobae)가 GHCR image 이름을 `ai_email_client-backend`와
  `ai_email_client-frontend`로 분리했습니다.
- Seongho Bae (@seonghobae)가 `VERSION` 파일을 추가하고 release version을
  `0.1.0`으로 고정했습니다. dotted-quad placeholder version은 사용하지 않습니다.
- Seongho Bae (@seonghobae)가 Docker publish workflow에서 `VERSION` 파일을 읽어
  SemVer raw tag를 발행하도록 했습니다.
- Seongho Bae (@seonghobae)가 `PR Governance` workflow를 추가했습니다. 이 workflow는
  PR 코드를 checkout하지 않고, current-head required checks와 CodeRabbit/robot-review
  evidence를 수집한 뒤 조건이 맞을 때만 auto-merge를 활성화합니다.
- Seongho Bae (@seonghobae)가 `Internal Mail Smoke` workflow를 추가했습니다. 이
  workflow는 `mail-egress` self-hosted runner에서만 수동 실행되며, Naruon을 이메일
  서버로 만들지 않고 외부 SMTP/IMAP outbound reachability만 검증합니다.
- Seongho Bae (@seonghobae)가 FastAPI `/healthz`, `/readyz`, `/metrics` endpoint를
  추가해 live deployment evidence를 수집할 수 있게 했습니다.
- Seongho Bae (@seonghobae)가 Prometheus text format metrics를 노출하기 위해
  `prometheus-client`를 추가했습니다.
- Seongho Bae (@seonghobae)가 Open Source APM 로컬 구성을 추가했습니다. Compose에는
  OpenTelemetry Collector, Prometheus, Grafana, Loki, Tempo, Grafana Alloy가 포함됩니다.
- Seongho Bae (@seonghobae)가 `docs/operations/observability.md`를 추가해 APM 실행,
  health/readiness/metrics 확인, Grafana 접근 방법을 한국어로 문서화했습니다.
- Seongho Bae (@seonghobae)가 `docs/operations/mail-runner.md`를 추가해 사내망
  SMTP/IMAP smoke self-hosted runner 구조를 설명했습니다.
- Seongho Bae (@seonghobae)가 `docs/operations/postgres-replication.md`를 추가해
  PostgreSQL 물리 복제, backup/restore, pgvector compatibility, replica lag 기준을
  문서화했습니다.
- Seongho Bae (@seonghobae)가 PostgreSQL 운영 문서에 `DATABASE_URL_READ_ONLY`,
  primary-only write/migration 경계, PgBouncer/PgCat 검토, NUL byte(`\u0000`/`\x00`)
  입력 정규화 정책을 추가했습니다.
- Seongho Bae (@seonghobae)가 `docs/development/release-governance-acceptance.md`를
  추가해 릴리스 거버넌스 acceptance criteria를 사람이 읽을 수 있는 계약으로
  정리했습니다.
- Seongho Bae (@seonghobae)가 root `AGENTS.md`를 추가해 warning/deprecation/security
  remediation, robot review gate, Gitflow, GHCR tag, self-hosted mail runner 원칙을
  agent가 다시 오해하지 않도록 기록했습니다.
- Seongho Bae (@seonghobae)가 `backend/scripts/run_imap_worker.py`를 추가해 API replica와
  IMAP worker runtime을 분리했습니다.
- Seongho Bae (@seonghobae)가 Kubernetes `imap-worker` deployment manifest를 추가해
  mailbox sync가 API replica 수에 비례해 중복 실행되지 않도록 했습니다.
- Seongho Bae (@seonghobae)가 Kubernetes Secret example manifest를 추가했습니다. 실제
  credential은 저장소에 들어가지 않습니다.

### 변경

- Seongho Bae (@seonghobae)가 Bandit workflow를 fail-closed로 변경했습니다. 이전에는
  scan failure가 `continue-on-error`로 녹색처럼 보일 수 있었지만 이제 findings는
  required gate 실패로 드러납니다.
- Seongho Bae (@seonghobae)가 Bandit SARIF 업로드를 `always()`로 유지해 실패 시에도
  GitHub code scanning evidence를 남기도록 했습니다.
- Seongho Bae (@seonghobae)가 Bandit 설치를 `requirements-bandit-ci.txt`로 고정해
  scanner version drift를 줄였습니다.
- Seongho Bae (@seonghobae)가 app CI와 Bandit의 `push` trigger를 `master` 중심으로
  제한해, PR branch push와 pull_request가 동일 head에서 중복 Checks를 만들 가능성을
  낮췄습니다.
- Seongho Bae (@seonghobae)가 frontend Dockerfile을 `npm run dev` 실행에서 production
  `npm run build` + `npm run start` 경로로 전환했습니다.
- Seongho Bae (@seonghobae)가 `NEXT_PUBLIC_API_URL`을 Next build 이전에 `ARG`/`ENV`로
  주입하도록 변경했습니다. browser bundle에 들어가는 public env를 runtime env로만
  바꾸는 오류를 막기 위함입니다.
- Seongho Bae (@seonghobae)가 Docker Compose에서 PostgreSQL을 Docker network 내부
  service로만 노출하도록 조정했습니다. 로컬 host port를 열어 Netdata 같은 host-level
  probe가 잘못된 계정으로 접속하고 `FATAL` 로그를 만드는 문제를 피하기 위함입니다.
- Seongho Bae (@seonghobae)가 PostgreSQL initdb 인증을 `scram-sha-256`으로 명시하고
  healthcheck도 `POSTGRES_PASSWORD`를 사용하는 TCP readiness로 바꿨습니다. 초기화 중
  `trust` 인증 경고가 release evidence에 남지 않게 하기 위한 수정입니다.
- Seongho Bae (@seonghobae)가 backend, frontend, Prometheus, Grafana, Loki, Tempo,
  OpenTelemetry Collector의 host-facing Compose ports를 환경변수로 override할 수 있게
  했습니다. 기존 로컬 Prometheus나 개발 서버가 떠 있어도 live evidence stack을 별도
  port로 검증할 수 있습니다.
- Seongho Bae (@seonghobae)가 Compose에 `backend-worker` service를 추가해 API service와
  IMAP sync worker를 분리했습니다.
- Seongho Bae (@seonghobae)가 FastAPI lifespan에서 background worker가 기본으로 켜지지
  않도록 변경했습니다. API replica scale-out이 mailbox sync 중복 실행으로 이어지지
  않게 하기 위한 운영 경계입니다.
- Seongho Bae (@seonghobae)가 Kubernetes backend/frontend image를 `:latest`에서 `0.1.0`
  SemVer tag로 변경했습니다.
- Seongho Bae (@seonghobae)가 Kubernetes backend image 경로를 새 backend package인
  `ghcr.io/seongho-bae/ai_email_client-backend:0.1.0`으로 변경했습니다.
- Seongho Bae (@seonghobae)가 Kubernetes DB credential을 평문 값에서 Secret 참조로
  변경했습니다.
- Seongho Bae (@seonghobae)가 PostgreSQL StatefulSet에 PVC, readiness/liveness probe,
  resource request/limit를 추가했습니다.
- Seongho Bae (@seonghobae)가 frontend shell을 branding guide 색상과 문구에 더 가깝게
  조정했습니다. 모바일에서는 sidebar가 사라져도 주요 메뉴와 tagline이 header에 남습니다.
- Seongho Bae (@seonghobae)가 dashboard page에 모바일 stack layout을 추가했습니다.
  기존 desktop resizable panel은 `lg` 이상에서 유지됩니다.
- Seongho Bae (@seonghobae)가 `README.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md`,
  `SECURITY.md`, `docs/development/merge-gate-policy.md`에 릴리스/운영 경계를 추가했습니다.
- Seongho Bae (@seonghobae)가 Keycloak, Casdoor, Traefik 검토를
  `docs/operations/edge-auth.md`와 `ARCHITECTURE.md`에 follow-up 운영 경계로
  명시했습니다. 이번 릴리스는 OIDC/edge gateway를 즉시 도입하지 않고, mailbox
  ownership migration 전에는 다중 사용자 production API로 주장하지 않습니다.

### 수정

- Seongho Bae (@seonghobae)가 LLM API에서 `HTTPException`이 generic exception handler에
  잡혀 400 설정 오류가 500으로 바뀌던 문제를 수정했습니다. OpenAI key 누락은 이제
  `400 OpenAI API key not configured`로 유지됩니다.
- Seongho Bae (@seonghobae)가 Calendar sync API에 현재 사용자 dependency를 추가했습니다.
- Seongho Bae (@seonghobae)가 Calendar service 내부 exception detail이 HTTP response로
  그대로 노출되던 문제를 `Calendar sync failed`로 줄였습니다.
- Seongho Bae (@seonghobae)가 Kubernetes manifest의 평문 `postgres:postgres` DSN과
  password를 제거했습니다.
- Seongho Bae (@seonghobae)가 `latest`만 쓰던 배포 manifest를 versioned image tag로
  바꾸어 release provenance를 추적할 수 있게 했습니다.
- Seongho Bae (@seonghobae)가 dashboard skip link와 header microcopy를 한국어 중심으로
  정리했습니다.

### 보안

- Seongho Bae (@seonghobae)가 `email-validator`를 yanked/old pin인 `2.1.0`에서 `2.3.0`으로
  올렸습니다. downgrade가 아니라 secure floor upgrade입니다.
- Seongho Bae (@seonghobae)가 frontend dependency overrides로 `hono`, `fast-uri`,
  `ip-address`의 최소 보안 버전을 고정했습니다.
- Seongho Bae (@seonghobae)가 PR governance workflow를 metadata-only로 설계했습니다.
  `pull_request_target`에서 PR code를 checkout하거나 실행하지 않습니다.
- Seongho Bae (@seonghobae)가 self-hosted mail smoke를 `workflow_dispatch` 전용으로
  제한해 fork PR 또는 미검증 PR code가 사내망 mail runner와 secret에 접근하지 못하게
  했습니다.
- Seongho Bae (@seonghobae)가 `fix-development-mistakes` skill에 warning/deprecation,
  dependency downgrade, security alert 대응 원칙을 보강했습니다.
- Seongho Bae (@seonghobae)가 `SECURITY.md`에 Bandit, PR governance, mail runner,
  Kubernetes secret 기준을 추가했습니다.

### 문서

- Seongho Bae (@seonghobae)가 릴리스 노트를 한국어 Keep a Changelog 형식으로 확장했습니다.
- Seongho Bae (@seonghobae)가 새 운영 문서에서 Naruon이 이메일 서버가 아니라 외부
  SMTP/IMAP과 통신하는 웹 클라이언트 서버임을 명확히 했습니다.
- Seongho Bae (@seonghobae)가 PostgreSQL physical replication은 backup/restore evidence
  없이 완료 주장할 수 없다는 기준을 추가했습니다.
- Seongho Bae (@seonghobae)가 APM을 OpenTelemetry/Prometheus/Grafana/Loki/Tempo 중심의
  open-source stack으로 설계했습니다.

### 검증

- Seongho Bae (@seonghobae)가 `backend/tests/test_release_governance.py`를 확장해 app CI,
  Bandit, Docker publish, PR governance, mail smoke, observability docs, SemVer changelog
  계약을 검증하도록 했습니다.
- Seongho Bae (@seonghobae)가 `backend/tests/test_repo_hygiene.py`를 확장해 Kubernetes
  manifest의 평문 DB credential, `latest` image, StatefulSet storage/probe/resource
  누락을 감지하도록 했습니다.
- Seongho Bae (@seonghobae)가 `backend/tests/test_main.py`를 확장해 `/healthz`와
  `/metrics` endpoint를 검증하도록 했습니다.
- Seongho Bae (@seonghobae)가 `frontend/src/components/DashboardLayout.test.tsx`를
  확장해 한국어 skip link, 모바일 주요 메뉴, branding tagline 유지 여부를 검증하도록
  했습니다.

### 알려진 운영 제한

- AKS Dev 배포는 현재 로컬 kube context가 설정되어 있지 않으면 수행할 수 없습니다.
  이 경우 blocker issue에는 `kubectl config current-context` 결과를 남겨야 합니다.
- GHCR package가 아직 발행되지 않은 상태에서는 `gh api ...packages/container/...`가 404를
  반환할 수 있습니다. release tag push 이후 manifest evidence를 다시 확인해야 합니다.
- PostgreSQL physical replication은 이 릴리스에서 운영 완료가 아니라 설계와 안전 기준
  문서화입니다. 실제 replica, backup, restore drill은 후속 issue로 집행해야 합니다.
- 사내망 SMTP/IMAP smoke는 `mail-egress` self-hosted runner가 등록되어 있어야 실행됩니다.
