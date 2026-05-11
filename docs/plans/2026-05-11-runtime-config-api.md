# Runtime Config API and Frontend Client Implementation Plan

## Overview
Remove build-time-only frontend API configuration assumptions and introduce a backend runtime config endpoint for non-secret app configuration (Task T-002).

## Issue/Task Reference
- Target Task: T-002

## Stepwise Tasks

### Task 1: Backend Endpoint Implementation
1. In `backend/api/tenant_config.py` (or a new router `runtime_config.py`), implement `GET /api/runtime-config`.
2. The endpoint should return non-secret info: `product_name`, `version`, `features` (e.g. `{"llm_enabled": True}`), etc.
3. Add a basic Pytest to assert it returns 200 OK and valid JSON without secrets.

### Task 2: Frontend Runtime Config Client
1. Create `frontend/src/lib/runtime-config.ts` which fetches from `/api/runtime-config`.
2. Create `frontend/src/lib/api-client.ts` to manage API URLs dynamically using the fetched config or a safe fallback.
3. Provide React context or a store for config state.

### Task 3: Refactor Frontend Components
1. Update `EmailList.tsx`, `EmailDetail.tsx`, and `NetworkGraph.tsx` to use the new `api-client.ts`.
2. Ensure they do not use `process.env.NEXT_PUBLIC_API_URL` directly in components.
3. Fallback gracefully if config is unavailable.

### Task 4: Verification
1. Run backend tests.
2. Run frontend tests and linter.
3. Verify live E2E behavior.
