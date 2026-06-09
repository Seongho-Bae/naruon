# Naruon UI/UX Definition & Mapping

## 1. Overview
Naruon is an **Evidence-based AI Email Workspace**. The core objective of the UI/UX is not to simply act as an email client or AI summarization tool, but to synthesize email, attachments, images, calendars, relations, and project contexts based on evidence to assist users in judgment and execution.

## 2. Core Philosophy & UI Terminology
Naruon's UX strictly follows three principles:
1. **Do not just shorten emails. Connect the context.**
2. **AI does not just state conclusions. It presents evidence and confidence.**
3. **Judgments must lead to execution.**

### Terminology Rules
The UI must use specific terminology to reflect this philosophy:
* ❌ AI Summary -> ⭕ 맥락 종합 (Context Synthesis)
* ❌ Summary -> ⭕ 종합, 핵심 맥락 (Synthesis, Core Context)
* ❌ Insight -> ⭕ 판단 포인트 (Decision Point)
* ❌ Todo -> ⭕ 실행 항목 (Action Item)
* ❌ Smart Reply -> ⭕ 답장 초안 (Draft Reply)
* ❌ Search -> ⭕ 맥락 검색 (Context Search)
* ❌ Network Graph -> ⭕ 관계 맥락 (Relation Context)
* ❌ Calendar Sync -> ⭕ 일정 반영 (Reflect Calendar)
* ❌ AI Assistant -> ⭕ 판단 보조 (Judgment Assist)

## 3. Core GNB & UI Organization
The application is structured into 10 Main Global Navigation Bar (GNB) areas:

### 3.1 홈 (Home)
* **Key Sections:** 오늘의 판단 포인트 (Today's Decision Points), 대기 작업 (Pending Tasks), 일정 충돌 (Calendar Conflicts), 최근 메일 (Recent Emails).
* **Key Actions:** 열기 (Open), 보류 (Hold), 실행 항목 만들기 (Create Action Item), 일정 조율하기 (Coordinate Calendar).

### 3.2 메일 (Mail)
* **Key Sections:** 받은편지함 (Inbox), 메일 상세 (Mail Detail), 새 메일 (Compose), 답장 초안 (Draft Reply), 스레드 전체 (Thread Entire View).
* **Key Actions:** AI 답장 초안 (AI Draft Reply), 맥락 종합 (Context Synthesis), 판단 포인트 (Decision Points), 실행 항목 생성 (Create Action Item), 일정 후보 보기 (View Calendar Candidates), 첨부 분석 (Analyze Attachments), 스레드 병합/분리 (Merge/Split Thread).
* **UI Focus:** Show probability confidence, allow users to merge/split threads, provide source bindings for AI outputs.

### 3.3 일정 (Calendar)
* **Key Sections:** 월간/주간 캘린더 (Monthly/Weekly Calendar), 일정 상세 (Calendar Detail), 회의 조율 (Coordinate Meeting), 일정 후보 (Calendar Candidates).
* **Key Actions:** 새 일정 (New Event), 회의 조율 (Coordinate Meeting), 일정 반영 (Reflect Calendar), 후보 확정 (Confirm Candidate), 메일 열기 (Open Related Mail).

### 3.4 작업 (Task)
* **Key Sections:** 내 작업 (My Tasks), 위임한 작업 (Delegated Tasks), 칸반 (Kanban), 작업 상세 (Task Detail).
* **Key Actions:** 작업 생성 (Create Task), 담당자 변경 (Change Assignee), 상태 변경 (Change Status), 마감일 변경 (Change Due Date), 관련 메일 연결 (Link Related Mail).

### 3.5 프로젝트 (Project)
* **Key Sections:** 프로젝트 목록 (Project List), 프로젝트 상세 (Project Detail), 마일스톤 (Milestone), 의사결정 로그 (Decision Log).
* **Key Actions:** 새 프로젝트 (New Project), 프로젝트 열기 (Open Project), 마일스톤 추가 (Add Milestone), 의사결정 추가 (Add Decision), 관련 문서/메일 연결 (Link Context Graph Edge).

### 3.6 맥락 검색 (Context Search)
* **Key Sections:** 통합 검색 (Unified Search), 결과 상세 (Result Detail), 관계 그래프 (Relation Graph), 타임라인 (Timeline).
* **Key Actions:** 검색 (Search), 필터 적용 (Apply Filter), 맥락 종합 (Selected Result Synthesis), 그래프 확장 (Expand Graph), 타임라인 항목 열기 (Open Source Detail).

### 3.7 데이터 (Data)
* **Key Sections:** 문서 저장소 (Document Store), 수집 파이프라인 (Ingestion Pipeline), 임베딩 (Embedding Job Status), 품질 점검 (Quality Check).
* **Key Actions:** 업로드 (Upload), 재파싱 (Reparse), 임베딩 재생성 (Re-embed), 품질 점검 (Run Quality Suite), 격리 (Quarantine), HWP 변환 (HWP Convert).

### 3.8 AI 허브 (AI Hub)
* **Key Sections:** 프롬프트 스튜디오 (Prompt Studio), 워크플로우 (Workflow), AI 에이전트 (AI Agent), 평가 (Evaluation), 실행 이력 (Execution History).
* **Key Actions:** 테스트 실행 (Run Sandbox Test), 게시 (Publish), 워크플로우 실행 (Run Automation), 에이전트 실행 (Run Agent), 평가 시작 (Start Evaluation), 로그 보기 (View Run Log).

### 3.9 보안 (Security)
* **Key Sections:** 보안 대시보드 (Security Dashboard), 접근 권한 (Access Control), 감사 로그 (Audit Log), 외부 공유 (External Share), 정책 (Policies).
* **Key Actions:** 권한 변경 (Update RBAC/ABAC), 사용자 차단 (Revoke Access), 공유 승인/거절 (Approve/Reject Share), 감사 로그 상세 (View Event Detail), 정책 배포 (Publish Policy), 보고서 내보내기 (Export Report).

### 3.10 설정 (Settings)
* **Key Sections:** 워크스페이스 (Workspace), 멤버 (Members), 연결 계정 (Connected Accounts), 알림 (Notifications), 자동화 (Automations), 결제 (Billing), 개발자 (Developer).
* **Key Actions:** 저장 (Save), 멤버 초대 (Invite Member), 계정 연결 (Connect OAuth), 연결 해제 (Revoke Integration), 규칙 추가 (Add Automation Rule), API 키 생성 (Generate API Key), Webhook 추가 (Add Webhook).

## 4. UI Design Mockups (Phase 1 & 2)
The original UI design mockups defining these screens and workflows have been preserved and stored in the repository. They will serve as the primary reference for front-end implementation and PR reviews.

**Mockup Storage Path:** `docs/ui-ux/mockups/`

*Note: The mockups contain design definitions for the components above and must be translated into the Naruon Design System following the Evidence-based UI principles (confidence intervals, citation binding, and human correction UI).*
