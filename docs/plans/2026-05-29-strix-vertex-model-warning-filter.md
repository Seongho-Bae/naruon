# Strix Vertex Model and Warning Filter Roadmap

## Evidence

- PR #302 Strix run `26633823390` completed successfully, but the job log
  emitted a third-party `pydantic.main` `UserWarning` with the message
  `Pydantic serializer warnings`.
- Project policy treats `Timeout`, `Fatal`, `Warn`, and `Denied` output as
  failure evidence even when the GitHub job conclusion is success.
- The organization secret `STRIX_LLM` is expected to select
  `vertex_ai/gemini-3.1-pro-preview-customtools`; GitHub Models must not be used
  for this route.

## Plan

1. Keep the Strix workflow on trusted `pull_request_target` materialization with
   no PR-head checkout and no GitHub Models permission.
2. Allow only exact organization-approved Vertex model names:
   `vertex_ai/gemini-3.1-pro-preview-customtools` and
   `vertex_ai/gemini-2.5-flash`.
3. Default missing `STRIX_LLM` to the configured organization Vertex model so
   org-secret visibility issues do not silently route to GitHub Models.
4. Suppress only the known third-party `pydantic.main` serializer warning via
   `PYTHONWARNINGS`; do not blanket-ignore all `UserWarning` output.
5. Forward that warning contract through the Strix gate to the Python child
   process so the setting affects the actual scanner, not only the shell wrapper.
6. Lock the contract in shell and backend release-governance tests.

## Non-Goals

- Naruon application warnings remain failures in CI.
- Strix findings, failed auth, timeout, denial, or security scanner errors are
  not suppressed.
- GitHub Models, `github.token`, generic `LLM_API_KEY`, and arbitrary Vertex
  model patterns remain disallowed.
