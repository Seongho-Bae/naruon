# AI Insight Cards Implementation Plan

## Overview
Implement reusable AI insight cards in the email workspace and route summarization/action extraction through provider-neutral services.

## Issue/Task
- Target Task: T-004

## Stepwise Tasks

### Task 1: Reusable Frontend InsightCard Component
1. Create `frontend/src/components/InsightCard.tsx`.
2. Implement states: loading, success, empty, error, action, retry, provenance/source.

### Task 2: Refactor EmailDetail
1. Update `frontend/src/components/EmailDetail.tsx` to use the new `InsightCard`.
2. Wrap summary, action items, suggested reply, calendar/task actions in `InsightCard`.
3. Require explicit user action (e.g. clicking "Extract Action Items") or automatically run with clear loading states.
4. Require user confirmation before destructive actions (sync calendar, send reply).

### Task 3: Backend Insight Service & Provider-Neutral Routing
1. In `backend/services/llm_service.py` (or similar), ensure the service routes through a provider abstraction instead of hardcoding OpenAI if feasible, or prepare the payload shape so it returns structured card payloads.
2. Return provenance/source basis with the results.
3. Catch provider errors and return safe user-actionable Korean messages (e.g., "AI 요약을 생성하지 못했습니다. 다시 시도해주세요.") without exposing stack traces.

### Task 4: Verification
1. Run frontend lint and tests to ensure no regressions.
2. Run backend tests to ensure payload shapes are maintained.
3. Live E2E smoke tests.
