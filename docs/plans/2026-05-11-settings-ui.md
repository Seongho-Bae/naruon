# Settings UI Implementation Plan

## Overview
Implement the Admin-facing configuration surfaces for LLM Providers and Workspace Settings.

## Issue/Task
- Target Task: T-005

## Stepwise Tasks

### Task 1: API Configuration Setup
1. Add `frontend/src/app/settings/page.tsx` for the settings page container.
2. Implement Provider List view fetching from `GET /api/llm-providers`.
3. Implement Provider Form view to `POST /api/llm-providers` or `PUT /api/llm-providers/{id}`.
4. Ensure the Provider UI shows `configured` status and `fingerprint` without echoing raw secrets.

### Task 2: Provider Form Validation & UX
1. Use `zod` and `react-hook-form` or simple state to validate forms (e.g. name is required, provider_type is required).
2. For secrets, use a password-type input. Show a placeholder like "****************" if `configured` is true.
3. Catch and display 409 Conflicts (duplicate names) or 403 Forbidden (not admin) with clear Korean messages.

### Task 3: Admin RBAC Enforcement in UI
1. Determine admin status (either hardcode via a dev header toggle or check role via context/API). For now, use the `apiClient` with the default testuser, but mock it as `admin` when needed or let it fail gracefully for non-admins.
2. Ensure the UI clearly shows "관리자 전용 설정입니다" if a 403 is encountered on settings load.

### Task 4: Testing & Verification
1. Add a Playwright test or React Testing Library test to verify the form handles inputs safely and does not echo secrets.
2. Ensure no linting errors.
