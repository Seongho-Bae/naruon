# AI Hub and Prompt Studio Implementation Plan

## Overview
Implement the AI Hub and Prompt Studio MVP for Naruon workspace (Task T-006).

## Objectives
1. Create a central AI Hub page that lists recent insights or saved prompts.
2. Build Prompt Studio functionality to create/edit/test prompts.
3. Ensure server-side RBAC and redaction of logs when testing prompts.

## Implementation Details
1. **Database:** Add `PromptTemplate` model in `backend/db/models.py`.
2. **Backend API:** `backend/api/prompts.py` for CRUD operations on prompts and an endpoint to test prompt execution using the provider-neutral LLM service.
3. **Frontend Routes:**
   - `/ai-hub`: Dashboard for AI activities.
   - `/prompt-studio`: Prompt management interface.
4. **Validation:** Write Pytest test to ensure prompt CRUD works and test endpoint executes safely without leaking secrets or failing.
