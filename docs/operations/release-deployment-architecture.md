# Release and Deployment Architecture

## 확인된 사실 / Confirmed

- `ARCHITECTURE.md` defines the current runtime as Next.js frontend → FastAPI
  backend → PostgreSQL with pgvector, with OpenAI and SMTP used only when
  configured.
- `docker-compose.yml` is the local development stack for db/backend/frontend.
- `.github/workflows/app-ci.yml` runs backend pytest and frontend test/lint/build
  checks on pull requests without release-branch push duplication.
- `.github/workflows/docker-publish.yml` validates backend/frontend Docker images
  for PRs and publishes GHCR images only from `v*` tags whose value matches
  `VERSION`.
- `docker-compose.live-e2e.yml` is the live E2E stack: it uses pre-built images,
  seeds deterministic email data, scales backend replicas, and exposes the stack
  through nginx at `127.0.0.1:18080`.

## 가설 / Hypothesis

- The first release candidate should use tag `v0.1.0`, then verify backend and
  frontend GHCR manifests for `linux/amd64` and `linux/arm64` before production
  promotion.
- Deployment promotion should use image digests rather than mutable tags after
  the tag workflow produces digest evidence.

## 운영 절차 / Operating path

1. Build images locally or in CI from the release branch.
2. Run backend pytest and frontend test/lint/build checks.
3. Run live Docker E2E against built images.
4. Push `v$(cat VERSION)` only after checks and robot-review evidence are current.
5. Record GHCR digest, manifest platforms, and live E2E evidence in the PR or
   release evidence comment.
