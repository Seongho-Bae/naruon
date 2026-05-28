# Strix Provider Governance Slice

<!-- markdownlint-disable MD013 -->

## Goal

Keep the required Strix security gate on, but make the provider contract
unambiguous. The active route is the organization-secret Vertex AI model
`vertex_ai/gemini-3.1-pro-preview-customtools` selected through `STRIX_LLM` with
`GCP_SA_KEY`. Direct OpenAI GPT-5.4-or-newer remains allowed only when explicitly
selected with `STRIX_OPENAI_API_KEY`. Strix must not route through GitHub Models,
`github.token`, GPT-4-era models, or a generic `LLM_API_KEY`.

## Evidence

- PR #237 showed `provider_mode=openai_direct` and `api.openai.com` egress, then
  failed because the OpenAI Platform credential hit quota. That is external
  provider exhaustion, not a GitHub Models path.
- On 2026-05-28 the operator selected the org-secret Vertex AI route instead of
  GitHub Models or direct OpenAI as the default. The workflow therefore keeps a
  narrow Vertex branch for the exact approved model and keeps direct OpenAI as
  an explicit alternate path.

## Implementation

- Keep GCP credential gating, Google Cloud authentication, and credential export
  only inside `provider_mode=vertex_ai`, and only for the exact approved Vertex
  model.
- Keep direct OpenAI isolated behind `provider_mode=openai_direct` and
  `STRIX_OPENAI_API_KEY`.
- Keep the privileged PR pattern: trusted-base workspace materialization,
  immutable PR-head fetch as data, self-test from trusted workspace, and pinned
  third-party actions.
- Keep `continue-on-error` out of Strix. Provider quota remains a failed scan,
  and any temporary merge-gate adjustment must capture evidence and restore the
  required `strix` context immediately after merge processing.
- Update self-tests so the workflow fails static verification if GitHub Models,
  generic `LLM_API_KEY`, arbitrary Vertex/Gemini models, or cross-provider
  credential forwarding is reintroduced.

## Verification

```bash
bash scripts/ci/test_strix_quick_gate.sh
bash scripts/ci/test_pr_governance_gate.sh
python3 -m pytest backend/tests/test_release_governance.py -q
```

No browser screenshot is required for this CI-only governance slice.
