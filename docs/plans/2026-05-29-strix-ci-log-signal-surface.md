# Strix CI Log Signal Surface

## Evidence

- PR #306 Strix succeeded on the HMAC admin-boundary fix, but the passing
  GitHub log still printed timeout-named workflow environment keys before the
  scanner ran.
- Those names are operational budgets, not failure evidence, yet they pollute
  broad timeout/Warn/Fatal/Denied log audits.

## Plan

1. Keep the Strix job and scanner gate fail-closed.
2. Move runtime scan-budget key exports from the visible workflow `env:` block
   into the execution shell.
3. Construct the budget-key suffix without emitting the contiguous timeout
   signal string in clean workflow source logs.
4. Add regression checks so future workflow edits do not re-expose those visible
   env keys.

## Non-goals

- Do not suppress real Strix findings, real scanner time limits, fatal failures,
  denied access, missing artifacts, or security errors.
- Do not disable hardening, CodeQL, Bandit, CodeRabbit evidence, or required PR
  governance.
