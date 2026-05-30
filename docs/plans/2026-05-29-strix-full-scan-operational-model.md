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

1. Keep the organization-secret `STRIX_LLM` route, but quarantine the exact
   `vertex_ai/gemini-3.1-pro-preview-customtools` value to
   `vertex_ai/gemini-2.5-flash` until it has no-timeout evidence.
2. Route PR-scoped and protected-branch scans to the previously validated exact
   Vertex model `vertex_ai/gemini-2.5-flash` when the 3.1 preview value is
   configured.
3. Keep arbitrary Vertex model patterns disallowed; only the exact operational
   Vertex model is accepted.
4. Preserve the narrow Pydantic serializer warning filter and gate child-process
   forwarding from PR #303.
5. Add regression assertions so later edits cannot accidentally send full-repo
   scans through an unproven preview model.

## Non-Goals

- This does not reintroduce GitHub Models or generic `LLM_API_KEY`.
- This does not suppress scanner findings, timeouts, denied access, fatal
  errors, or application warnings.
- This does not claim the 3.1 org-secret value is operational without evidence.
