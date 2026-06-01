# Strix Warning Filter Log Surface Roadmap

## Evidence

- PR #303 moved the known third-party Pydantic serializer warning filter into
  the Strix workflow environment.
- GitHub Actions prints step environment names in the job log, so the literal
  `PYTHONWARNINGS` name can trip broad `WARNING` log searches even when no
  Python warning was emitted.
- The filter still needs to reach the actual Strix Python child process.

## Plan

1. Remove the warning filter from the workflow `env` block.
2. Set the same narrow `pydantic.main` serializer-warning filter inside
   `scripts/ci/strix_quick_gate.sh` when constructing the child process
   environment.
3. Do not inherit a caller-provided warning filter for Strix; use the fixed
   gate-owned value so CI cannot accidentally blanket-ignore warnings.
4. Keep tests proving the workflow does not expose `PYTHONWARNINGS:` while the
   gate still forwards the exact child filter.

## Non-Goals

- Do not suppress Strix findings, timeouts, fatal errors, denied access, or
  application warnings.
- Do not reintroduce GitHub Models or generic LLM credentials.
