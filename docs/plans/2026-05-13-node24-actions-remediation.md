# Node24 Actions Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove GitHub Actions Node 20 deprecation warnings from the Docker publish pipeline by explicitly opting the affected JavaScript actions into Node 24.

**Architecture:** Add the documented `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` environment variable at workflow scope for the Docker-image workflow so every JavaScript action in that pipeline runs on Node 24. Lock the expectation with a release-governance regression test so the warning cannot silently return.

**Tech Stack:** GitHub Actions YAML, pytest-based repository governance tests.

---

## Task 1: Add failing governance test

**Files:**
- Modify: `backend/tests/test_release_governance.py`
- Test: `backend/tests/test_release_governance.py`

**Step 1: Write the failing test**
Add an assertion that `.github/workflows/docker-publish.yml` contains `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true`.

**Step 2: Run test to verify it fails**
Run: `cd backend && python3 -m pytest tests/test_release_governance.py -q`
Expected: FAIL because the workflow does not contain the new env var yet.

**Step 3: Commit after green later**
Deferred until workflow fix is applied.

## Task 2: Implement workflow Node24 opt-in

**Files:**
- Modify: `.github/workflows/docker-publish.yml`

**Step 1: Add minimal implementation**
At workflow `env:` scope, add:
```yaml
FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true
```
so the Docker JavaScript actions run on Node 24 and stop emitting the GitHub deprecation warning.

**Step 2: Run test to verify it passes**
Run: `cd backend && python3 -m pytest tests/test_release_governance.py -q`
Expected: PASS.

**Step 3: Run workflow hygiene verification**
Run: `git diff --check`
Expected: PASS.

**Step 4: Commit**
`git add .github/workflows/docker-publish.yml backend/tests/test_release_governance.py && git commit -m "fix(ci): opt docker publish actions into Node 24"`

## Task 3: Review, merge, release sync

**Files:**
- Modify as needed based on review feedback

**Step 1: Open PR referencing #193**
Create a PR that resolves #193.

**Step 2: Request CodeRabbit approval**
Use the CodeRabbit approval flow on the current head.

**Step 3: Merge and release sync**
If merged cleanly, create the next version/tag sync PR and publish the matching release tag so GHCR reflects the warning-free workflow state.
