#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
script="$repo_root/scripts/ci/pr_governance_gate.sh"

make_fake_gh() {
  local bin_dir="$1"
  cat > "$bin_dir/gh" <<'FAKEGH'
#!/usr/bin/env bash
set -euo pipefail

printf '%s\n' "$*" >> "$GH_LOG"

head_sha="0123456789abcdef0123456789abcdef01234567"

if [ "$1" = "pr" ] && [ "$2" = "view" ]; then
  printf '{"number":42,"isDraft":false,"mergeable":"MERGEABLE","mergeStateStatus":"CLEAN","reviewDecision":"","statusCheckRollup":[]}'
  exit 0
fi

if [ "$1" = "api" ] && [[ "$2" == repos/*/pulls/42 ]]; then
  if printf '%s\n' "$*" | grep -q -- '.base.sha'; then
    printf 'abcdefabcdefabcdefabcdefabcdefabcdefabcd'
  else
    printf '%s' "$head_sha"
  fi
  exit 0
fi

if [ "$1" = "api" ] && [[ "$2" == repos/*/commits/* ]] && [[ "$2" != */check-runs ]]; then
  printf '2026-05-19T00:00:00Z'
  exit 0
fi

if [ "$1" = "api" ] && [ "$2" = "graphql" ]; then
  printf '{"data":{"repository":{"pullRequest":{"headRefOid":"%s","mergeStateStatus":"CLEAN","reviewThreads":{"nodes":[]}}}}}' "$head_sha"
  exit 0
fi

if [ "$1" = "pr" ] && [ "$2" = "checks" ]; then
  case "${GH_SCENARIO:-pass}" in
    pending)
      printf '[{"name":"Application CI","state":"IN_PROGRESS","link":"https://checks/app-ci"}]'
      ;;
    startup_failure)
      printf '[{"name":"Application CI","state":"STARTUP_FAILURE","link":"https://checks/app-ci"}]'
      ;;
    failed)
      printf '[{"name":"Application CI","state":"FAILED","link":"https://checks/app-ci"}]'
      ;;
    failure|failed_existing)
      printf '[{"name":"Application CI","state":"FAILURE","link":"https://checks/app-ci"}]'
      ;;
    *)
      printf '[{"name":"Application CI","state":"SUCCESS","link":"https://checks/app-ci"}]'
      ;;
  esac
  exit 0
fi

if [ "$1" = "api" ] && [[ "$2" == repos/*/commits/*/check-runs ]]; then
  case "${GH_SCENARIO:-pass}" in
    coderabbit_pending)
      printf '{"check_runs":[{"name":"CodeRabbit","app":{"slug":"coderabbitai"},"status":"in_progress","conclusion":null,"html_url":"https://checks/coderabbit"}]}'
      ;;
    missing_coderabbit)
      printf '{"check_runs":[]}'
      ;;
    coderabbit_failed)
      printf '{"check_runs":[{"name":"CodeRabbit","app":{"slug":"coderabbitai"},"status":"completed","conclusion":"failure","html_url":"https://checks/coderabbit"}]}'
      ;;
    coderabbit_neutral)
      printf '{"check_runs":[{"name":"CodeRabbit","app":{"slug":"coderabbitai"},"status":"completed","conclusion":"neutral","output":{"title":"CodeRabbit","summary":"Review completed","text":"No skip evidence"},"html_url":"https://checks/coderabbit"}]}'
      ;;
    coderabbit_review_skipped)
      printf '{"check_runs":[{"name":"CodeRabbit","app":{"slug":"coderabbitai"},"status":"completed","conclusion":"neutral","output":{"title":"CodeRabbit","summary":"Review skipped","text":"Review skipped"},"html_url":"https://checks/coderabbit"}]}'
      ;;
    *)
      printf '{"check_runs":[{"name":"CodeRabbit","app":{"slug":"coderabbitai"},"status":"completed","conclusion":"success","html_url":"https://checks/coderabbit"}]}'
      ;;
  esac
  exit 0
fi

if [ "$1" = "api" ] && printf '%s\n' "$*" | grep -q 'repos/.*/issues/42/comments'; then
  if printf '%s\n' "$*" | grep -q -- '--jq'; then
    if [ "${GH_SCENARIO:-pass}" = "failed_existing" ]; then
      printf '555\n'
    fi
    exit 0
  fi
  if printf '%s\n' "$*" | grep -q -- '--paginate'; then
    case "${GH_SCENARIO:-pass}" in
      coderabbit_blocking_comment)
        printf '[{"id":777,"user":{"login":"coderabbitai[bot]"},"created_at":"2026-05-19T00:01:00Z","body":"Pre-merge warning for 0123456789abcdef0123456789abcdef01234567"}]'
        ;;
      *)
        printf '[]'
        ;;
    esac
    exit 0
  fi
  printf 'posted\n'
  exit 0
fi

if [ "$1" = "api" ] && printf '%s\n' "$*" | grep -q 'repos/.*/pulls/42/comments'; then
  printf '[]'
  exit 0
fi

if [ "$1" = "api" ] && [ "$2" = "--method" ] && [ "$3" = "PATCH" ] && [[ "$4" == repos/*/issues/comments/555 ]]; then
  printf 'patched\n'
  exit 0
fi

if [ "$1" = "pr" ] && [ "$2" = "merge" ]; then
  printf 'merge requested\n'
  exit 0
fi

printf 'unexpected gh invocation: %s\n' "$*" >&2
exit 99
FAKEGH
  chmod +x "$bin_dir/gh"
}

run_gate() {
  local scenario="$1"
  local temp_dir="$2"
  mkdir -p "$temp_dir/bin"
  make_fake_gh "$temp_dir/bin"
  GH_LOG="$temp_dir/gh.log" \
  GH_SCENARIO="$scenario" \
  PATH="$temp_dir/bin:$PATH" \
  GITHUB_REPOSITORY="owner/repo" \
  GH_TOKEN="fake" \
  EVENT_NAME="pull_request_target" \
  TARGET_PR_NUMBER="42" \
  DIRECT_PR_NUMBER="" \
  WORKFLOW_RUN_PR_NUMBER="" \
    bash "$script" > "$temp_dir/output.txt"
}

assert_no_comment_or_merge_for_pending_checks() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  run_gate pending "$temp_dir"

  grep -q 'Waiting for 1 required check' "$temp_dir/output.txt"
  ! grep -q 'issues/42/comments -f body' "$temp_dir/gh.log"
  ! grep -q '^pr merge' "$temp_dir/gh.log"
}

assert_startup_failure_creates_marker_comment() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  run_gate startup_failure "$temp_dir"

  grep -q 'Required check `Application CI` is STARTUP_FAILURE' "$temp_dir/gh.log"
  grep -q '<!-- pr-governance:metadata-gate -->' "$temp_dir/gh.log"
  ! grep -q '^pr merge' "$temp_dir/gh.log"
}

assert_failed_checks_create_marker_comment() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  run_gate failed "$temp_dir"

  grep -q 'PR governance metadata gate is not ready' "$temp_dir/gh.log"
  grep -q '<!-- pr-governance:metadata-gate -->' "$temp_dir/gh.log"
  grep -q 'Application CI' "$temp_dir/gh.log"
  ! grep -q '^pr merge' "$temp_dir/gh.log"
}

assert_existing_marker_comment_is_patched() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  run_gate failed_existing "$temp_dir"

  grep -q 'api --method PATCH repos/owner/repo/issues/comments/555' "$temp_dir/gh.log"
  ! grep -q 'repos/owner/repo/issues/42/comments -f body' "$temp_dir/gh.log"
}

assert_coderabbit_pending_waits_without_hard_comment() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  run_gate coderabbit_pending "$temp_dir"

  grep -q 'Waiting for current-head CodeRabbit evidence' "$temp_dir/output.txt"
  ! grep -q 'issues/42/comments -f body' "$temp_dir/gh.log"
  ! grep -q '^pr merge' "$temp_dir/gh.log"
}

assert_missing_coderabbit_waits_without_hard_comment() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  run_gate missing_coderabbit "$temp_dir"

  grep -q 'Waiting for current-head CodeRabbit evidence' "$temp_dir/output.txt"
  ! grep -q 'issues/42/comments -f body' "$temp_dir/gh.log"
  ! grep -q '^pr merge' "$temp_dir/gh.log"
}

assert_coderabbit_failure_creates_marker_comment() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  run_gate coderabbit_failed "$temp_dir"

  grep -q 'Current-head CodeRabbit check has a blocking conclusion' "$temp_dir/gh.log"
  grep -q '<!-- pr-governance:metadata-gate -->' "$temp_dir/gh.log"
  ! grep -q '^pr merge' "$temp_dir/gh.log"
}

assert_coderabbit_neutral_without_skip_evidence_blocks() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  run_gate coderabbit_neutral "$temp_dir"

  grep -q 'Current-head CodeRabbit check has a blocking conclusion' "$temp_dir/gh.log"
  ! grep -q '^pr merge' "$temp_dir/gh.log"
}

assert_coderabbit_review_skipped_neutral_can_merge() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  run_gate coderabbit_review_skipped "$temp_dir"

  grep -q '^pr merge 42 --repo owner/repo --auto --merge --match-head-commit 0123456789abcdef0123456789abcdef01234567$' "$temp_dir/gh.log"
  ! grep -q 'issues/42/comments -f body' "$temp_dir/gh.log"
}

assert_coderabbit_blocking_issue_comment_blocks() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  run_gate coderabbit_blocking_comment "$temp_dir"

  grep -q 'Current-head CodeRabbit issue comment has blocking warning/failure evidence' "$temp_dir/gh.log"
  ! grep -q '^pr merge' "$temp_dir/gh.log"
}

assert_passing_gate_enables_non_admin_auto_merge() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  run_gate pass "$temp_dir"

  grep -q '^pr merge 42 --repo owner/repo --auto --merge --match-head-commit 0123456789abcdef0123456789abcdef01234567$' "$temp_dir/gh.log"
  ! grep -q -- '--admin' "$temp_dir/gh.log"
}

assert_no_comment_or_merge_for_pending_checks
assert_startup_failure_creates_marker_comment
assert_failed_checks_create_marker_comment
assert_existing_marker_comment_is_patched
assert_coderabbit_pending_waits_without_hard_comment
assert_missing_coderabbit_waits_without_hard_comment
assert_coderabbit_failure_creates_marker_comment
assert_coderabbit_neutral_without_skip_evidence_blocks
assert_coderabbit_review_skipped_neutral_can_merge
assert_coderabbit_blocking_issue_comment_blocks
assert_passing_gate_enables_non_admin_auto_merge

printf 'test_pr_governance_gate: PASS\n'
