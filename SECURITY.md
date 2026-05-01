# Security Policy

## Code Quality

- **Standard findings:** 0건
- **AI Findings:** 0건

## Dependabot

- **Malware:** 0건
- **Vulnerabilities:** 0건

## Code Scanning

- **Code scanning:** 0건

## Secret Scanning

- **Secret scanning:** 잠정적으로 0건으로 만들 것

## Strix Security Scan

- **Strix Security Scan:** Medium 이상 모두 수정 (Medium 까지는 한국 법령이 요구하는 강제 사항이 포함되어 있음)
- Pull request scans that need repository secrets must use trusted-base
  `pull_request_target` execution: workflow scripts and dependencies come from
  GitHub API-materialized base commit content, while pull request head files are
  fetched as Git objects and scanned only as copied data.
- If a changed pull request file cannot be read from the PR head, the Strix gate
  fails closed and must not substitute trusted-base file contents.

## CI/CD Enforcement

- Checks가 통과되어야 Merge 가능하도록 Branch Protection Rule에 의해 강제됩니다.
