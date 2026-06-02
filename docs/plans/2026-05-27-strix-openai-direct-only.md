# Strix OpenAI Platform Direct-Only Governance Slice

<!-- markdownlint-disable MD013 -->

## Goal

Keep the required Strix security gate on, but make the provider contract
unambiguous: Strix uses an explicit `STRIX_OPENAI_API_KEY` OpenAI Platform
credential and an OpenAI GPT-5.4-or-newer model. It must not route through
GitHub Models, Google/Vertex/Gemini, `github.token`, or a generic `LLM_API_KEY`.

## Evidence

- PR #237 showed `provider_mode=openai_direct` and `api.openai.com` egress, then
  failed because the OpenAI Platform credential hit quota. That is external
  provider exhaustion, not a GitHub Models path.
- `origin/master` already rejects GitHub Models prefixes, but the Strix workflow
  still carried GCP/Vertex credential steps. Those steps were unreachable for
  valid OpenAI model input unless a GCP secret was present, yet their presence
  made the required scan contract ambiguous.

## Implementation

- Remove GCP credential gating, Google Cloud authentication, and relocated GCP
  credential export from `.github/workflows/strix.yml`.
- Keep the privileged PR pattern: trusted-base workspace materialization,
  immutable PR-head fetch as data, self-test from trusted workspace, and pinned
  third-party actions.
- Keep `continue-on-error` out of Strix. Provider quota remains a failed scan,
  and any temporary merge-gate adjustment must capture evidence and restore the
  required `strix` context immediately after merge processing.
- Update self-tests so the workflow fails static verification if GCP/Vertex
  authentication or GitHub Models routing is reintroduced.

## Verification

```bash
bash scripts/ci/test_strix_quick_gate.sh
bash scripts/ci/test_pr_governance_gate.sh
python3 -m pytest backend/tests/test_release_governance.py -q
```

No browser screenshot is required for this CI-only governance slice.
