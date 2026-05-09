---
name: fix-development-mistakes
description: >-
  Use when linter errors, dependency downgrades, security vulnerabilities, file
  overwrites, merge conflicts, or merge-gate misdiagnoses occur during
  development and need root-cause repair.
---

# Fix Development Mistakes

## Overview

Fix linter errors, dependency downgrades, security vulnerabilities, file
overwrites, and other mistakes that occur during development. The goal is to
trace the root cause and fix it properly without waiting for human intervention.

## When to use

Use this skill when:

- Dependabot or code scanning alerts report a vulnerability.
- A subagent overwrites a file instead of appending to it, such as
  `exceptions.py` or `requirements.txt`.
- A linter or static analyzer throws an error, such as `mypy`, `flake8`, or
  `ruff`.
- Merge conflicts result in accidental loss of code or unintended dependency
  downgrades.
- Merge gates, CodeRabbit/robot review, GitHub approval, or stale required
  status contexts are misdiagnosed; use `github-robot-review-gate`.
- CI or test output contains warning, deprecated, notice, denied, or fatal
  messages. Treat these as failures until the root cause is fixed or captured as
  a blocker with evidence.
- A dependency version is lowered. Require compatibility evidence and security
  evidence before accepting the downgrade.

## Workflow

### 1. Root cause analysis

- Identify the exact error, warning, or security alert.
- Trace back through git history or `git diff` to see what introduced it.
- Understand whether the source is a prompt misunderstanding, package conflict,
  reverted security patch, stale ruleset, or environment mismatch.

### 2. Formulate the fix

- File overwrites: restore the original content from the correct base, then add
  the intended changes narrowly.
- Dependency issues: pin secure versions and resolve conflicts by upgrading the
  conflicting package rather than downgrading a patched package.
- Linter errors: add missing type hints, fix indentation, add docstrings, or use
  a narrow documented suppression only when the rule is intentionally violated.
- Merge-gate issues: collect ruleset/check/review evidence before changing code
  or repository settings.
- Warning/deprecation issues: identify whether the source is code, dependency,
  runtime, workflow syntax, or environment precondition. Fix the cause instead of
  hiding the log with `--quiet` or blanket filters.
- Dependency issues: prefer secure upgrades and package overrides with lockfile
  evidence. Do not downgrade a library just to make a scanner quiet.

### 3. Execute and verify

- Apply the smallest targeted fix.
- Run the relevant test suite and linter locally.
- Confirm the warning, error, vulnerability, or gate blocker is resolved.

### 4. Commit and push

- Commit with a descriptive message starting with the `fix:` prefix.
- Example: `fix: restore exceptions.py overwritten by subagent`.
- Example: `fix: upgrade pytest to resolve CVE-2025-71176`.
- Push to the feature branch only after verification and PR-continuity checks,
  or create a PR if on `master`.
