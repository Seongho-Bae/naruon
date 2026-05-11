# AGENTS.md

## Release governance defaults

- GitHub Actions used by governed workflows must be pinned to full commit SHAs
  with a trailing version comment, for example `# v6`; major-only refs such as
  `@v6` are not allowed in release or security workflows.
- Security scanners are required gates. Do not use `continue-on-error: true` to
  hide Bandit, Strix, CodeQL, or dependency findings; preserve artifacts with
  explicit `if: ${{ always() }}` upload steps when needed.
- Prefer upgrading or removing vulnerable dependencies over downgrading patched
  packages unless compatibility evidence is recorded in the PR.
