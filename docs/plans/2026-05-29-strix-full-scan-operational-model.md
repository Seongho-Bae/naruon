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
- PR #311 Strix run `26661237230` timed out the first PR-scope batch after
  `1200s`, then found a HIGH OIDC admin-claim issue only after rebatching. The
  next head run `26662731398` remained in `Run Strix (quick)` for more than one
  hour, showing that a 12-file first batch is not operationally bounded enough
  for current Vertex-backed PR evidence.
- PR #312 run `26669020785` used the old quarantine path and then failed after
  repeated `MidStreamFallbackError` and timeout-class provider failures while
  printing zero vulnerabilities. Under the no Timeout/Fatal/Warn/Denied policy,
  that is not clean PR evidence.
- PR #312 current-head Strix evidence then found two real hardening gaps:
  OIDC issuer/JWKS allowlisting still allowed trusted hostnames to resolve to
  private addresses, and the privileged PR scanner preserved PR-head executable
  bits when materializing scan data.

## Plan

1. Keep the organization-secret `STRIX_LLM` route and honor the exact
   `vertex_ai/gemini-3.1-pro-preview-customtools` value now that organization
   secret visibility is available.
2. Default missing `STRIX_LLM` to
   `vertex_ai/gemini-3.1-pro-preview-customtools` rather than silently routing
   to GitHub Models or a downgraded Vertex fallback.
3. Keep arbitrary Vertex model patterns disallowed; only exact approved Vertex
   models are accepted.
4. Preserve the narrow Pydantic serializer warning filter and gate child-process
   forwarding from PR #303.
5. Add regression assertions so later edits cannot accidentally quarantine the
   approved 3.1 route or pass after timeout/provider failure output.
6. Start PR-scope evidence with single-file deterministic batches instead of
   waiting for a 12-file batch to hit the process budget and rebalance after the
   timeout.
7. Validate OIDC issuer/JWKS hostnames by resolving every address to a global IP
   before startup accepts the configuration, and make JWKS preload fetches
   connect to that validated pinned address while preserving TLS/SNI for the
   allowlisted hostname.
8. Copy PR-head blobs into privileged Strix scan scopes as non-executable data,
   even when the PR branch records the file as mode `100755`.

## Non-Goals

- This does not reintroduce GitHub Models or generic `LLM_API_KEY`.
- This does not suppress scanner findings, timeouts, denied access, fatal
  errors, or application warnings.
- This does not treat zero-vulnerability text as sufficient evidence after a
  timeout, denied, fatal, warning, or provider infrastructure failure.
