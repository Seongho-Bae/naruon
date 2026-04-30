---
name: github-actions-privileged-pr-scan
description: >-
  Use when a GitHub Actions pull request workflow needs repository secrets,
  cloud credentials, security scanners, SCA/SAST tools, or other privileged
  inputs while inspecting PR-authored code.
---

# GitHub Actions Privileged PR Scan

## Core rule

Treat PR code as untrusted whenever repository secrets are reachable. Run
trusted base workflow code, fetch PR head as data, and fail closed on
metadata/blob read errors.

## Checklist

- Use `pull_request_target` only when secrets are required; otherwise prefer
  `pull_request` with no secrets.
- Checkout the trusted base commit for scripts, dependencies, and scanner wrappers.
- Never checkout or execute the PR branch in the privileged job.
- Fetch PR head by immutable ref/SHA and verify the fetched commit matches `github.event.pull_request.head.sha`.
- Copy changed PR-head blobs into a temporary scope and scan that scope as data.
- Reject path traversal, pathspec-shaped, absolute, symlink, and non-regular
  file inputs.
- If PR-head lookup/read/copy/chmod fails, fail closed; do not substitute base
  content.
- Keep workflow permissions least-privilege and pin third-party actions.
- Add regression tests for trigger choice, base checkout, PR-head blob copy,
  lookup failure, and severity threshold behavior.

## Common mistake

Unsafe pattern:

```yaml
on: pull_request
steps:
  - uses: actions/checkout@...
  - run: ./scripts/security-scan.sh
    env:
      API_KEY: ${{ secrets.API_KEY }}
```

Safer privileged pattern:

```yaml
on: pull_request_target
steps:
  - uses: actions/checkout@...
    with:
      ref: ${{ github.event.pull_request.base.sha }}
      persist-credentials: false
  - run: git fetch origin "+refs/pull/${PR_NUMBER}/head:refs/remotes/pull/${PR_NUMBER}/head"
  - run: ./scripts/security-scan-pr-head-as-data.sh
```
