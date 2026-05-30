# Strix Protected Branch Security Findings

## Trigger

Protected-branch Strix run `26648235234` on merge commit
`1675651709db94c9200f92ea0f8bcc94ca213fd8` reported three findings after PR
#308 merged:

- Medium: POP3 worker log text exposed the missing credential type.
- Medium: live smoke test used `urllib.request.urlopen`, which Bandit/Strix
  treats as a broad URL opener pattern.
- Critical: `.github/workflows/strix.yml` interpolated GitHub expression data
  directly inside a shell `if` condition.

## Plan

1. Replace POP3 missing-secret log and raised error text with generic
   account-configuration wording while keeping the sync path fail-closed.
2. Replace the live HTTP helper with explicit `http.client` HTTP/HTTPS
   connections and add a regression test that forbids the `urlopen` pattern.
3. Move Strix workflow expression values into step `env:` keys before shell
   usage and extend the Strix gate self-test to reject direct expression
   interpolation in shell conditions.
4. Record the repeated bug patterns in `AGENTS.md` and current README
   operational notes.

## Verification

- `scripts/ci/test_strix_quick_gate.sh`
- `python3 -m pytest backend/tests/test_pop3_worker.py backend/tests/live/test_live_api_sequence.py -q`
- `python3 -m bandit -r backend/ -x backend/tests/ -q`
- PR-scoped Strix evidence on the current head, then protected-branch Strix
  after merge.
