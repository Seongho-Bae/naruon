#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <control-json-file> <failed-checks-file> <failed-check-evidence-file>" >&2
  exit 64
fi

CONTROL_JSON_FILE="$1"
FAILED_CHECKS_FILE="$2"
FAILED_CHECK_EVIDENCE_FILE="$3"

if [ ! -r "$CONTROL_JSON_FILE" ] || [ ! -r "$FAILED_CHECKS_FILE" ] || [ ! -r "$FAILED_CHECK_EVIDENCE_FILE" ]; then
  echo "FAILED_CHECK_EVIDENCE_NOT_REFERENCED"
  exit 4
fi

if [ ! -s "$FAILED_CHECKS_FILE" ]; then
  exit 0
fi

review_text="$(
  jq -r '
    [
      (.summary // ""),
      (.reason // ""),
      (
        .findings[]?
        | [
            (.path // ""),
            ((.line // "") | tostring),
            (.severity // ""),
            (.title // ""),
            (.problem // ""),
            (.root_cause // ""),
            (.fix_direction // ""),
            (.regression_test_direction // ""),
            (.suggested_diff // "")
          ]
        | join("\n")
      )
    ]
    | join("\n")
  ' "$CONTROL_JSON_FILE"
)"

contains_review_text() {
  local needle="$1"
  if [ -z "$needle" ]; then
    return 0
  fi
  grep -Fqi -- "$needle" <<<"$review_text"
}

extract_strix_required_markers() {
  perl -CS -ne '
    s/\r//g;
    s/\x1b\[[0-9;?]*[A-Za-z]//g;
    if (/│/) {
      s/^.*?│[[:space:]]*//;
      s/[[:space:]]*│.*$//;
    } else {
      s/^.*?[0-9]Z[[:space:]]+//;
    }
    s/[[:space:]]+/ /g;
    s/^[[:space:]]+|[[:space:]]+$//g;

    if (/^Title:[[:space:]]+(.+)/) {
      print "$1\n";
    }
    if (/^Severity:[[:space:]]+(CRITICAL|HIGH|MEDIUM|LOW)\b/) {
      print "Severity: $1\n";
    }
    if (/^Endpoint:[[:space:]]+(.+)/) {
      print "$1\n";
    }
    if (/^Method:[[:space:]]+(.+)/) {
      print "Method: $1\n";
    }
    if (/^Location[[:space:]]+[0-9]+:[[:space:]]+(.+:[0-9]+(?:-[0-9]+)?)/) {
      print "$1\n";
    }
  ' "$FAILED_CHECK_EVIDENCE_FILE"
}

extract_strix_title_markers() {
  perl -CS -ne '
    s/\r//g;
    s/\x1b\[[0-9;?]*[A-Za-z]//g;
    if (/│/) {
      s/^.*?│[[:space:]]*//;
      s/[[:space:]]*│.*$//;
    } else {
      s/^.*?[0-9]Z[[:space:]]+//;
    }
    s/[[:space:]]+/ /g;
    s/^[[:space:]]+|[[:space:]]+$//g;
    if (/^Title:[[:space:]]+(.+)/) {
      print "$1\n";
    }
  ' "$FAILED_CHECK_EVIDENCE_FILE"
}

count_strix_review_findings() {
  jq -r '
    [
      (.findings // [])[]
      | [
          .title,
          .problem,
          .root_cause,
          .fix_direction,
          .regression_test_direction,
          .suggested_diff
        ]
        | map(. // "")
        | join("\n")
      | select(test("strix|github[-_]models/|deepseek/|openai/gpt-|vertex_ai/|Vulnerability Report"; "i"))
    ]
    | length
  ' "$CONTROL_JSON_FILE"
}

while IFS= read -r failed_check_line; do
  case "$failed_check_line" in
    "- "*)
      failed_check_label="${failed_check_line#- }"
      failed_check_label="${failed_check_label%%:*}"
      if ! contains_review_text "$failed_check_label"; then
        echo "FAILED_CHECK_EVIDENCE_NOT_REFERENCED"
        exit 4
      fi
      ;;
  esac
done <"$FAILED_CHECKS_FILE"

while IFS= read -r fail_marker; do
  if ! contains_review_text "$fail_marker"; then
    echo "FAILED_CHECK_EVIDENCE_NOT_REFERENCED"
    exit 4
  fi
done < <(awk -F 'FAIL: ' 'NF > 1 { print $2 }' "$FAILED_CHECK_EVIDENCE_FILE" | sort -u)

for evidence_marker in \
  "Self-test Strix gate script" \
  "github.event.inputs.strix_llm" \
  "STRIX_LLM must select" \
  "MODEL: github-models/openai/gpt-5"
do
  if grep -Fq -- "$evidence_marker" "$FAILED_CHECK_EVIDENCE_FILE" &&
    ! contains_review_text "$evidence_marker"; then
    echo "FAILED_CHECK_EVIDENCE_NOT_REFERENCED"
    exit 4
  fi
done

if grep -Fq "Strix vulnerability report window" "$FAILED_CHECK_EVIDENCE_FILE"; then
  strix_title_count="$(extract_strix_title_markers | sed '/^[[:space:]]*$/d' | wc -l | tr -d '[:space:]')"
  finding_count="$(count_strix_review_findings)"
  if [ -n "$strix_title_count" ] && [ "$strix_title_count" -gt 0 ] &&
    [ "$finding_count" -lt "$strix_title_count" ]; then
    echo "FAILED_CHECK_EVIDENCE_NOT_REFERENCED"
    exit 4
  fi

  while IFS= read -r model_name; do
    if ! contains_review_text "$model_name"; then
      echo "FAILED_CHECK_EVIDENCE_NOT_REFERENCED"
      exit 4
    fi
  done < <(
    perl -ne 'while (m{(?:openai|deepseek|vertex_ai|github(?:_|-)models)/[A-Za-z0-9._/-]+}g) { print "$&\n" }' \
      "$FAILED_CHECK_EVIDENCE_FILE" | sort -u
  )

  while IFS= read -r strix_marker; do
    if ! contains_review_text "$strix_marker"; then
      echo "FAILED_CHECK_EVIDENCE_NOT_REFERENCED"
      exit 4
    fi
  done < <(extract_strix_required_markers)
fi

exit 0
