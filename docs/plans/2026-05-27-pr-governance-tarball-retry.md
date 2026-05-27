# PR Governance Trusted Tarball Retry Slice

<!-- markdownlint-disable MD013 -->

## Goal

Prevent transient GitHub API response truncation from leaving PR Governance in a
false failed state. The metadata gate must still fail closed when trusted-base
materialization cannot be proven, but it should retry bounded infrastructure
flakes before declaring failure.

## Evidence

- PR #239 saw `metadata-only gate evaluation` fail twice during
  `Materialize trusted governance gate` with `unexpected end of JSON input`.
- The same run succeeded after a delayed rerun without code changes, proving the
  failure was infrastructure/API truncation rather than a PR-head code issue.

## Implementation

- Add `gh_api_with_retry` for trusted PR/base metadata lookups.
- Add a four-attempt trusted tarball download loop that validates the archive
  with `tar -tzf` before extraction, using a candidate archive file until
  validation succeeds.
- Reject non-SHA trusted refs before requesting a tarball.
- Preserve fail-closed behavior after bounded retries. Do not use
  `continue-on-error`, do not execute PR-head code, and do not add admin merge
  behavior.
- Record the bug pattern in `AGENTS.md` so future agents rerun or harden the
  materialization path instead of reporting a stale CodeRabbit/review blocker.

## Verification

```bash
python3 -m pytest backend/tests/test_release_governance.py -q
bash scripts/ci/test_pr_governance_gate.sh
git diff --check
```

No browser screenshot is required for this CI-only governance slice.
