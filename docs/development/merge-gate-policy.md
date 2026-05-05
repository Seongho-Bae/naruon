# Merge Gate Policy

This repository's merge gate is evidence-based: required checks must pass,
review threads must be resolved, and the current PR head must have current-head
CodeRabbit/robot-review evidence. Human review is not awaited by default.

## Required gate contract

- Required status checks must pass on the current head SHA.
- The CodeRabbit robot-review gate is satisfied by current-head CodeRabbit
  evidence only when current-head blocking findings, warnings, and failures are
  fixed, rebutted with evidence, or superseded. Authoritative current-head
  `Review skipped` evidence satisfies the robot-review gate when applicable.
- GitHub rulesets must use `required_approving_review_count=0` so GitHub does
  not require a human `APPROVED` review when robot-review policy applies.
- GitHub rulesets must keep `required_review_thread_resolution=true`.
- Bypass actors must not be configured for routine delivery.
- Security workflows and scanners are required gates, not optional paths.

## Evidence commands

Use the same head SHA across all checks:

```bash
gh pr view <pr> \
  --json number,headRefOid,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup
gh pr checks <pr> --required
gh api repos/<owner>/<repo>/pulls/<pr>/reviews
gh api repos/<owner>/<repo>/commits/<sha>/check-runs
gh api repos/<owner>/<repo>/rulesets --jq '.[] | {name, enforcement, rules}'
```

## Robot review versus GitHub approval

CodeRabbit review/check evidence satisfies this repo's robot-review policy only
after current-head CodeRabbit blocking comments, pre-merge warnings, and failure
findings are resolved or superseded. It is not the same object as a GitHub
`APPROVED` review. If GitHub reports a missing approving review, inspect the
ruleset before waiting for a human review. The expected setting is
`required_approving_review_count=0`.

## Stale required contexts

A required context can become stale when the PR is fixing the workflow that
emits it. For example, PRs that fix Strix may be blocked by a required `strix`
context before the hardened Strix workflow can emit a valid result.

Handling policy:

1. Prefer branch update or rerun first.
2. If the required context cannot be emitted until the PR lands, document the
   stale context and use only a temporary, reversible ruleset adjustment.
   Capture equivalent temporary evidence before merge, such as a trusted-base
   rerun, scanner artifact, SARIF output, or manual security review evidence
   tied to the current head SHA.
3. Restore the `strix` required context after the hardened workflow emits it
   successfully on the protected branch.
4. Re-run required-check evidence after restore.

## PR #108/#109 evidence summary

- PR #108 exposed the merge-gate ambiguity: CodeRabbit/robot-review evidence was
  conflated with a GitHub `APPROVED` review, while ruleset configuration could
  still require human approval despite repo policy.
- Issue #109 documents the durable fix: distinguish robot-review evidence from
  GitHub approval objects, keep human approval count at zero, preserve review
  thread resolution, and handle stale `strix` required contexts with explicit
  rollback.
- The root cause was policy/evidence mismatch, not lack of human review.

## Rollback and recovery

- Do not add bypass actors, disable security checks, dismiss reviews, or use admin
  merge for normal delivery.
- Any temporary ruleset change must have captured before/after JSON, owner,
  expiry, head SHA, equivalent temporary evidence, and a named restore
  condition.
- Restore required contexts immediately after the repaired workflow emits them.
- If the platform still rejects merge after policy-aligned settings and passing
  checks, record the rejection as an external blocker with the exact command
  output and head SHA.
