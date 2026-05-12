# Provider-Neutral LLM Configuration Plan

## Overview
Replace the existing OpenAI-specific configuration assumptions with a provider-neutral registry backed by an encrypted secret store.

## Issue/Task
- Target Task: T-003

## Stepwise Tasks

### Task 1: Encrypted Storage & Models
1. In `backend/db/models.py`, add an `AuditLog` model to track secret changes.
2. Update or create an `LLMProvider` model to store `provider_name`, `base_url`, `is_active`, and an encrypted `api_key`.
3. Ensure `EncryptedString` does not silently fallback to a dummy key in production.

### Task 2: Provider-Neutral Domain & DTOs
1. Create `backend/api/llm_providers.py` router.
2. Define Pydantic models for request/response that hide raw secrets and only return `configured: bool`, `updated_at`, and `fingerprint`.

### Task 3: API Endpoints & RBAC
1. Implement `GET /api/llm-providers`
2. Implement `POST /api/llm-providers`
3. Implement `PUT /api/llm-providers/{provider_id}`
4. Add RBAC dependency ensuring only Admin (e.g., specific user header or role) can call these mutation endpoints.
5. In each mutation, append a record to the `AuditLog` table.

### Task 4: Backward Compatibility
1. Ensure the existing `services/llm_service.py` can fetch the OpenAI provider dynamically from the database using the new structure or fallback to ENV if in development.

### Task 5: Testing & Verification
1. Write TDD unit tests for provider CRUD, secret masking, and RBAC enforcement.
2. Run backend tests, ensuring no regressions.
3. Validate overall CI pipeline.
