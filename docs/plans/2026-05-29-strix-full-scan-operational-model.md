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
- PR #311 Strix run `26661237230` exceeded the earlier process budget before
  later surfacing a HIGH OIDC admin-claim issue. The next head run `26662731398`
  remained in `Run Strix (quick)` for more than one hour, showing that the
  Vertex-backed provider path itself needed clearer timeout evidence handling.
- PR #312 run `26669020785` used the old quarantine path and then failed after
  repeated `MidStreamFallbackError` and timeout-class provider failures while
  printing zero vulnerabilities. Under the no Timeout/Fatal/Warn/Denied policy,
  that is not clean PR evidence.
- PR #312 current-head Strix evidence then found two real hardening gaps:
  OIDC issuer/JWKS allowlisting still allowed trusted hostnames to resolve to
  private addresses, and the privileged PR scanner preserved PR-head executable
  bits when materializing scan data.
- PR #312 automatic Strix evidence then flagged session verifier authority as a
  token-claim trust issue. Even when a tampered JWT would fail HMAC validation,
  the safer contract is to derive `session_verifier` only from the server-side
  HMAC/OIDC verification path.
- PR #312 manual current-head run `26686952879` printed zero vulnerabilities but
  still timed out after `2400s`. That confirms zero-vulnerability text is not
  enough; timeout-class evidence remains failed evidence. PR scope must still be
  presented to Strix as one whole-context target rather than split into separate
  scanner runs.

## Plan

1. Keep the GitHub Models default route with
   `STRIX_LLM=openai/openai/gpt-4.1`, `models: read`, `github.token`, and
   `LLM_API_BASE_FILE` pointing at a trusted file containing
   `https://models.github.ai/inference`.
2. Keep legacy `STRIX_LLM` secrets from overriding PR, push, or scheduled
   defaults. Keep Vertex routes explicit through manual `workflow_dispatch`
   `strix_llm` selections plus `GCP_SA_KEY`, and keep direct OpenAI explicit
   through manual `strix_llm` selections plus `STRIX_OPENAI_API_KEY`.
3. Keep arbitrary Vertex model patterns disallowed; only exact approved Vertex
   models are accepted.
4. Preserve the narrow Pydantic serializer warning filter and gate child-process
   forwarding from PR #303.
5. Add regression assertions so later edits cannot accidentally quarantine the
   approved 3.1 route or pass after timeout/provider failure output.
6. Present the generated PR-head scope to Strix in one scanner invocation. Do not
   split changed files into separate scanner runs because Strix's whole-context
   review model expects all relevant files together.
7. Validate OIDC issuer/JWKS hostnames by resolving every address to a global IP
   before startup accepts the configuration, and make JWKS preload fetches
   connect to that validated pinned address while preserving TLS/SNI for the
   allowlisted hostname.
8. Copy PR-head blobs into privileged Strix scan scopes as non-executable data,
   even when the PR branch records the file as mode `100755`.
9. Use `STRIX_TARGET_PATH=__PR_SCOPE__` for PR evidence runs so workflow-level
   review and the gate script share the same contract: the scanner receives a
   generated PR-head scope, not the trusted base checkout.
10. Disable package-manager lifecycle scripts in the Strix child process
    environment while scanning untrusted PR-head scope data, covering npm, pnpm,
    yarn, and bun script execution knobs.
11. Validate PR base/head SHA inputs in the workflow shell before any trusted
    fetch or PR-scope evidence handoff so workflow_dispatch cannot pass
    shell-shaped data into the gate.
12. Keep JWT session authority outside user-controlled payload claims: HMAC and
    OIDC verification paths must pass `session_verifier` into auth-context
    construction instead of reading `_session_verifier` from the decoded payload.

## Non-Goals

- This does not reintroduce generic `LLM_API_KEY` or cross-provider credential
  forwarding.
- This does not suppress scanner findings, timeouts, denied access, fatal
  errors, or application warnings.
- This does not treat zero-vulnerability text as sufficient evidence after a
  timeout, denied, fatal, warning, or provider infrastructure failure.
