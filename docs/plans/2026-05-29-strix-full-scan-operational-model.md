# Strix Full-Scan Operational Model Roadmap

## Evidence

- PR #303 merged with the Strix workflow/gate warning filter, but the
  `pull_request_target` scan itself still used trusted base workflow code from
  the previous `master`.
- The first protected-branch Strix push run for merge commit `c3d4548`
  (`26635699207`) started `Run Strix (quick)` at `2026-05-29T11:56:22Z` and
  remained in progress past the 40-minute process budget.
- Pending checks are wait states, but a full-scan route that exceeds its process
  budget is not acceptable operating evidence under the no Timeout/Fatal/Warn/
  Denied policy.

## Plan

1. Keep PR-scoped Strix scans on the organization-secret `STRIX_LLM` route so
   `vertex_ai/gemini-3.1-pro-preview-customtools` can be used after secret
   visibility correction.
2. Route protected-branch full scans (`push`, `schedule`, and manual
   non-PR-scoped `workflow_dispatch`) to the previously validated exact Vertex
   model `vertex_ai/gemini-2.5-flash`.
3. Keep arbitrary Vertex model patterns disallowed; only the exact PR model and
   exact full-scan model are accepted.
4. Preserve the narrow Pydantic serializer warning filter and gate child-process
   forwarding from PR #303.
5. Add regression assertions so later edits cannot accidentally send full-repo
   scans through an unproven preview model.

## Non-Goals

- This does not reintroduce GitHub Models or generic `LLM_API_KEY`.
- This does not suppress scanner findings, timeouts, denied access, fatal
  errors, or application warnings.
- This does not remove the 3.1 org-secret path for PR-scoped evidence.
