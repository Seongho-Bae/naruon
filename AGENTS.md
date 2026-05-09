# AGENTS.md

## 프로젝트 운영 원칙

- 이 저장소는 Gitflow를 따른다. `master` 직접 작업 대신 별도 브랜치와 PR로 전달한다.
- 사람 리뷰를 기본 blocker로 기다리지 않는다. required checks와 current-head CodeRabbit/robot-review evidence를 기준으로 판단한다.
- Strix, Bandit, GitHub security alert는 blocker가 아니라 조치 대상이다. 단, Medium 이상 또는 required check 실패는 원인 해결 전 merge하지 않는다.
- warning, deprecated, notice, denied, fatal 로그는 실패로 간주한다. 억제하지 말고 원인을 추적한다.

## 필수 skill routing

- linter, dependency, security, merge-gate 실수: `.agents/skills/fix-development-mistakes/SKILL.md`
- privileged PR scan 또는 secret을 쓰는 GitHub Actions: `.agents/skills/github-actions-privileged-pr-scan/SKILL.md`
- robot review, CodeRabbit, ruleset, human-review 오해: `.agents/skills/github-robot-review-gate/SKILL.md`

## 릴리스 검증

- Backend: `cd backend && DISABLE_BACKGROUND_WORKERS=1 PYTHONWARNINGS=error python -m pytest -q`
- Frontend: `cd frontend && npm ci && npm test && npm run lint && npm run build`
- Docker/live: `POSTGRES_PASSWORD=change-me-local-only docker compose up -d --build`
- Governance: `cd backend && python -m pytest tests/test_release_governance.py tests/test_repo_hygiene.py -q`

## 배포/운영 주의

- Naruon은 이메일 서버가 아니다. SMTP/IMAP을 자체 제공하지 않고, 외부 메일 서버와 통신하는 웹 클라이언트 서버다.
- 사내망 SMTP/IMAP smoke는 `mail-egress` self-hosted runner에서 수동으로만 실행한다.
- GHCR 이미지는 `0.1.0` 같은 SemVer tag가 필요하다. `[0.0.0.1]` 또는 `latest`만으로 release를 증명하지 않는다.
- PostgreSQL 물리 복제는 backup/restore, pgvector extension, replica lag evidence가 없으면 follow-up으로 남긴다.
