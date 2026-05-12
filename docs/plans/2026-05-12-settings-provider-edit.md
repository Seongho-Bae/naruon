# Settings Provider Edit Implementation Plan

## Overview
The Settings UI currently only allows creating and viewing LLM Providers. We need to add Edit and Delete functionality.

## Tasks
1. **API Client Extension:** Add `put` and `delete` methods to `frontend/src/lib/api-client.ts`.
2. **Settings UI Update (`page.tsx`):**
   - Add Edit/Delete buttons to each provider item.
   - Implement `handleEdit` which populates the form and switches to edit mode.
   - Implement `handleDelete` which sends a DELETE request and refreshes.
   - Update form submission to use `PUT` when in edit mode, and `POST` when in create mode.
3. **Verification:**
   - Run tests and linters.
   - Ensure RBAC and error handling (403, 404) are still intact.
