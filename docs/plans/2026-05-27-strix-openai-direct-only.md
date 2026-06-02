# Strix Provider Governance Slice

<!-- markdownlint-disable MD013 -->

## Goal

Keep the required Strix security gate on, but make the provider contract
unambiguous. The active default route is GitHub Models selected through
`STRIX_LLM=openai/openai/gpt-4.1`, `models: read`, `github.token`, and
`LLM_API_BASE_FILE` pointing at a trusted file containing
`https://models.github.ai/inference`. Legacy `STRIX_LLM` secrets must not
override PR, push, or scheduled Strix defaults. Vertex AI remains available only
for manual `workflow_dispatch` evidence when `strix_llm`
explicitly selects an approved Vertex model with `GCP_SA_KEY`, and direct OpenAI
GPT-5.4-or-newer remains allowed only for manual `strix_llm` selections with
`STRIX_OPENAI_API_KEY`. Strix must not route through a generic `LLM_API_KEY` or
silently fall back across providers.

## Evidence

- PR #237 showed `provider_mode=openai_direct` and `api.openai.com` egress, then
  failed because the OpenAI Platform credential hit quota. That is external
  provider exhaustion, not a GitHub Models path.
- On 2026-06-02 the operator selected GitHub Models as the default route for
  Strix failures. The workflow therefore keeps GitHub Models as the default,
  using the highest GitHub Models OpenAI route verified by organization Actions
  evidence at the time, while retaining narrow manual Vertex branches, higher
  GitHub Models overrides, and direct OpenAI as explicit alternate paths.

## Implementation

- Keep GitHub Models credential handling inside `provider_mode=github_models`
  with `github.token` passed through the trusted child-process key file and
  `LLM_API_BASE_FILE` pointing at a trusted temp file.
- Keep GCP credential gating, Google Cloud authentication, and credential export
  only inside manual `provider_mode=vertex_ai`, and only for approved Vertex
  model names.
- Keep direct OpenAI isolated behind manual `provider_mode=openai_direct` and
  `STRIX_OPENAI_API_KEY`.
- Keep the privileged PR pattern: trusted-base workspace materialization,
  immutable PR-head fetch as data, self-test from trusted workspace, and pinned
  third-party actions.
- Keep `continue-on-error` out of Strix. Provider quota remains a failed scan,
  and any temporary merge-gate adjustment must capture evidence and restore the
  required `strix` context immediately after merge processing.
- Update self-tests so the workflow fails static verification if the GitHub
  Models default, generic `LLM_API_KEY`, arbitrary Vertex/Gemini models, or
  cross-provider credential forwarding regresses.

## Verification

```bash
bash scripts/ci/test_strix_quick_gate.sh
bash scripts/ci/test_pr_governance_gate.sh
python3 -m pytest backend/tests/test_release_governance.py -q
```

No browser screenshot is required for this CI-only governance slice.
