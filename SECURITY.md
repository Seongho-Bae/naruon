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
- Bandit은 fail-closed로 실행되며 SARIF 업로드는 실패 시에도 evidence로 남깁니다.
- PR governance는 PR 코드를 checkout하거나 실행하지 않고 current-head required checks와 CodeRabbit/robot-review evidence만 평가합니다.
- 사내망 SMTP/IMAP smoke는 `mail-egress` self-hosted runner에서 `workflow_dispatch`로만 실행합니다.
- Kubernetes manifest에는 DB credential을 평문으로 적지 않고 Secret을 참조합니다.
- GitHub Security alert는 0건을 목표로 하되, 기능 훼손이나 무증거 downgrade로 닫지 않습니다.
