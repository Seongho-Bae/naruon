# Phase 13: CI Stabilization, Strix Configuration, and Remaining Core Logic

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure CI is robust by replacing `github_models/gpt-4o` properly across all required CI setups for Strix, verifying the application CI node setup is fast, and implementing any leftover architectural requirements like "Email sent to myself becomes a knowledge node" full pipeline.

**Architecture:** 
- Finalize Strix model fallback mechanisms correctly handling the LiteLLM spec for Github provider (`github/gpt-4o`).
- Implement the knowledge node processing worker for `process_self_to_self` detection.
- Clean up Node process leaks during testing.

**Tech Stack:** GitHub Actions, Python, Pytest.

---

## Task 1: Strix & GitHub Actions Stability

**Files:**
- Modify: `.github/workflows/strix.yml`
- Modify: `.github/workflows/app-ci.yml` (or similar)

- [ ] **Step 1: Check `.github/workflows/strix.yml` to ensure `STRIX_LLM_DEFAULT_PROVIDER` and the model name align with LiteLLM's `github/` prefix (not `github_models/`).**
- [ ] **Step 2: Ensure Node CI steps cache effectively so postcss doesn't spawn hundreds of processes (add Turbopack lock exclusions or adjust next config if needed).**
- [ ] **Step 3: Commit and push to verify.**

## Task 2: Self-to-Self Knowledge Extraction

**Files:**
- Modify: `backend/services/knowledge_extractor.py` (or create if needed)
- Modify: `backend/tests/test_knowledge_extractor.py`

- [ ] **Step 1: Write a test asserting that a `process_self_to_self` email stringifies into a specific Knowledge Node object.**
- [ ] **Step 2: Implement the knowledge node generation, ideally hitting an LLM endpoint or a mock extractor.**
- [ ] **Step 3: Verify the tests pass.**

## Task 3: Node Process Fix

**Files:**
- Modify: `package.json` or `.gitignore` (for lock files)

- [ ] **Step 1: Identify if `package-lock.json` is causing Turbopack leaks in CI.**
- [ ] **Step 2: Ignore or lock it appropriately as dictated in `AGENTS.md`.**