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
- Materialize only the trusted base commit for scripts, dependencies, and scanner
  wrappers.
- Avoid `actions/checkout` in privileged PR workflows when CodeQL treats any
  checkout as unsafe.
- Never checkout or execute the PR branch in the privileged job.
- Fetch PR head by immutable ref/SHA and verify the fetched commit matches `github.event.pull_request.head.sha`.
- Copy changed PR-head blobs into a temporary scope and scan that scope as data.
- Reject path traversal, pathspec-shaped, absolute, symlink, and non-regular
  file inputs.
- If PR-head lookup/read/copy/chmod fails, fail closed; do not substitute base
  content.
- Keep workflow permissions least-privilege and pin third-party actions.
- Add regression tests for trigger choice, trusted workspace materialization,
  absence of `actions/checkout`, PR-head blob copy, lookup failure, and severity
  threshold behavior.
- When publishing GitHub issue/PR evidence from shell, pass Markdown bodies via a
  single-quoted heredoc (`--body "$(cat <<'EOF' ... EOF)"`) so backticked text
  such as `actions/checkout` is not executed by the shell before `gh` receives it.

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
  - name: Materialize trusted workspace
    env:
      GH_TOKEN: ${{ github.token }}
      TRUSTED_WORKSPACE_SHA: ${{ github.event.pull_request.base.sha }}
    run: |
      gh api "/repos/${GITHUB_REPOSITORY}/tarball/${TRUSTED_WORKSPACE_SHA}" \
        | tar -xz --strip-components=1
  - run: git fetch origin "+refs/pull/${PR_NUMBER}/head:refs/remotes/pull/${PR_NUMBER}/head"
  - run: ./scripts/security-scan-pr-head-as-data.sh
```
