# Naruon North Star Master Specification & Phase 10+ Roadmap

이 문서는 사용자가 요청한 35가지 핵심 요구사항과 아키텍처 원칙을 바탕으로, 기존의 갭(Gap)을 식별하고 앞으로 나아갈 명확한 스펙(Specification) 및 구현 로드맵을 정의합니다.

## 1. Architecture & Infrastructure (아키텍처 스펙)

### 1.1. Self-hosted Runner & Relay Proxy 구조
Naruon은 자체 스토리지를 제공하는 이메일 호스트 서버가 아닙니다. 
- **역할**: 외부 SMTP/IMAP/POP3 연동 및 OAuth 로그인을 지원하는 웹 클라이언트이자 Relay Proxy.
- **폐쇄망 지원**: 사내망(Enterprise Private Network) 환경을 고려하여, 고객망 내부에 배포할 수 있는 **Self-hosted Connector(Runner)**를 제공. 이를 통해 내부망 이메일 서버와 Naruon SaaS 간 보안 연결(WebSocket/mTLS)을 확립.
- **도메인**: 프로덕션 및 서비스 기준 도메인은 `naruon.net`으로 통일.

### 1.2. Data Sovereignty (데이터 주권) 및 프로토콜 Write-back
모든 데이터(메모, 캘린더, 할일, 파일)는 Naruon 독자 시스템에만 갇혀(Lock-in) 있지 않고 고객의 원래 데이터소스에 동기화됩니다.
- **CalDAV / WebDAV 지원**: 사용자가 연동한 다중 계정의 캘린더와 스토리지를 Naruon이 읽고 AI로 종합·조직화.
- **Write-back 라우팅**: AI에 의해 새롭게 도출되거나 종합된 항목은, 연동된 여러 계정 중 **가장 문맥상 타당한 계정(예: 회사 메일 기반의 할일은 회사 CalDAV로)**을 추론하여 Write-back 처리.

### 1.3. Identity & Gateway
- **인증 솔루션**: 자체 로그인 및 엔터프라이즈 SAML/OIDC 연동 처리를 위해 **Keycloak** 또는 **Casdoor**와 같은 전문 Auth 솔루션을 도입.
- **게이트웨이**: Ingress 및 API 라우팅을 위해 **Traefik** 도입을 설계에 반영.

### 1.4. Universal RBAC / ABAC 권한 관리
아키텍처 레벨에서 권한 모델은 다음의 모든 주체를 포괄하는 유니버설 구조여야 합니다.
- 시스템 관리자 (SaaS 공급자)
- 기업 및 독립 법인/사업부/조직 (B2B2C)
- IT 운영자 및 보안팀
- 개인 이용자 (B2C) 및 SOHO

### 1.5. Observability (APM)
- 오픈소스 기반의 APM 체계(OpenTelemetry + Prometheus, Loki, Tempo, Grafana 등)를 구축하여 성능 및 안정성을 모니터링.

## 2. Product Features & UX/UI (제품 상세 기획)

### 2.1. 글로벌 네비게이션(GNB) 구조
기존 `frontend/branding` 에셋과 기성 베스트 프랙티스(Best Practices)를 분석하여 다음과 같이 메뉴 기획을 확정합니다.

| GNB (대메뉴) | 상세 화면 (Sub-views) |
| --- | --- |
| **홈** | 오늘의 판단 포인트, 대기 작업, 일정 충돌, 최근 메일 |
| **메일** | 받은편지함, 메일 상세, 새 메일, 답장 초안, 스레드 전체 |
| **일정** | 월간/주간 캘린더, 일정 상세, 회의 조율, 일정 후보 |
| **작업** | 내 작업, 위임한 작업, 칸반, 작업 상세 |
| **프로젝트** | 프로젝트 목록, 프로젝트 상세, 마일스톤, 의사결정 로그 |
| **맥락 검색** | 통합 검색, 결과 상세, 관계 그래프, 타임라인 |
| **데이터** | 문서 저장소, 수집 파이프라인, 임베딩, 품질 점검 |
| **AI 허브** | 프롬프트 스튜디오, 워크플로우, AI 에이전트, 평가, 실행 이력 |
| **보안** | 보안 대시보드, 접근 권한, 감사 로그, 외부 공유, 정책 |
| **설정** | 워크스페이스, 멤버, 연결 계정, 알림, 자동화, 결제, 개발자 |

### 2.2. 핵심 기능 요구사항
- **시작 화면 선택권 보장**: 로그인 직후 Dashboard, Email, Calendar 중 무엇을 띄울지 사용자 설정에서 완벽히 지원.
- **DAG 기반 사용자 관계 캡처(Ontology)**: 특정 발신자가 사용자에게 어떤 존재인지 관계 그래프를 형성. 이를 바탕으로 AI 에이전트가 다음 액션(분류, 알림 우선순위)을 결정.
- **양방향 Context Tracking**: 
  - 메일 ↔ 일정, 할일, 메모 간의 추적성(Tracking) 보장.
  - 작업(Task) 관리는 단순한 체크리스트가 아닌 티켓(Ticket) 기반으로 상태 추적을 지원.
  - 내게 쓴 메일(Self-to-self)은 자동으로 '지식/노트'로 조직화.
- **중복 이메일 Threading**: ZIP 임포트나 포워딩 과정에서 발생하는 중복 메일을 Unique ID 및 지문으로 판별하여 단일 스레드로 정리.
- **발신 메일 응답 추적**: 내가 보낸 메일에 대해 언제까지 응답이 와야 하는지 대기/추적하는 기능 추가.
- **UX 원칙 (No Dead Space)**: 기능이 없는 슬로건 공간을 최소화하고, 모든 영역은 실제 조작 및 실행이 가능하도록 구현.

## 3. Development, Testing & CI/CD Governance

### 3.1. 자동화된 PR 및 로봇 리뷰
- 개발 사이클은 1개 Phase 당 "개발 -> PR 생성 -> GitHub Actions 자동 실행 -> CodeRabbitAI 코드 리뷰 -> Merge -> 다음 Phase 진행"의 **Stepwise(단계별)** 방식을 엄격히 준수.
- 사람이 직접 Admin 권한으로 블로킹을 푸는 대신 CodeRabbitAI 등 로봇과 협업.
- 리뷰가 완료되지 않았더라도 대기(Blocking)하지 않고, 남은 스펙(`docs/plans`, `frontend/branding`)을 발굴해 선행 구현 로드맵을 작성.

### 3.2. 테스트 기준 및 퀄리티 컨트롤
- **Strict Error Handling**: 로그나 테스트에서 발생하는 `Timeout`, `Fatal`, `Warn`, `Denied`는 단순 경고가 아닌 **실패(Hard Block)**로 간주.
- **반응형 E2E**: 모바일 햄버거 메뉴 타당성, 데스크톱/태블릿 스크롤 여부 등 해상도별 Playwright 스크린샷 캡쳐 기반 시각적 테스트 통과 필수.
- **리소스 안정성**: Node 프로세스 증식 버그 등 리소스 누수가 발생하지 않도록 프로세스 생명주기를 주의 깊게 관리.
- **DB 스키마 네이밍**: 모든 신규 테이블/컬럼은 최소 두 단어 이상의 `snake_case` 형식으로 지정 (단일 단어 `id`, `title` 지양).

### 3.3. 지식화 및 문서 동기화
- 새로운 스킬이 필요할 경우 MCP 기반(`vooster-ai`, `find-skills` 등) 활용.
- 발견된 버그 패턴과 안티패턴은 즉시 `AGENTS.md` 와 `README.md` 에 업데이트하여 반복되지 않게 훈련화(Grounding).
