# Phase 11: Email Threading, DAG Ontology Pipeline, and CalDAV Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the previously defined schema and core logic (from Phase 10) into the actual background sync workers and API endpoints. Implement true email threading, DAG ontology persistence, reply tracking, and CalDAV/WebDAV integration.

**Architecture:** Use the existing `ImapSyncWorker` to trigger ontology and fingerprinting logic. Use `SenderRelationship` to store the DAG. Expose these via REST endpoints for the frontend.

**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL, Python

---

## Task 1: Email Threading and Deduplication Pipeline

**Files:**
- Modify: `backend/services/threading_service.py` (or create if needed)
- Modify: `backend/services/imap_worker.py` (or wherever email fetching happens)
- Test: `backend/tests/test_threading_pipeline.py`

- [ ] **Step 1: Write a test for threading/deduplication using `generate_email_fingerprint`**
- [ ] **Step 2: Update the worker to compute fingerprint before DB insertion**
- [ ] **Step 3: If fingerprint exists, update existing thread instead of inserting duplicate**
- [ ] **Step 4: Verify tests pass**

## Task 2: DAG Ontology & Self-to-Self Knowledge Extraction

**Files:**
- Modify: `backend/services/ontology_service.py`
- Modify: `backend/api/ontology.py` (or create if needed)
- Test: `backend/tests/test_ontology_pipeline.py`

- [x] **Step 1: Write a test that inserts a `SenderRelationship` to DB based on `analyze_sender_relationship`**
- [ ] **Step 2: Update `ontology_service.py` to accept DB session and save the relationship including explicit tenant_id and source_id/thread_id fields**
- [x] **Step 3: If `process_self_to_self` is true, trigger a knowledge extraction task passing tenant and source context**
- [ ] **Step 4: Create/Update `/api/ontology/relationships` to fetch the DAG for the frontend, filtering by tenant_id and source_id. Explicitly require the default signed-session authentication by registering the router with the `get_auth_context` dependency.**

2026-05-26 implementation note: IMAP import now triggers idempotent
`self_sent_knowledge` ticket-task capture for true self-to-self messages, and
ontology analysis/API responses include deterministic `next_action` metadata.
The remaining gap is durable source/thread graph fields plus source-id filtered
relationship reads.

## Task 3: Reply Tracking Background Job

**Files:**
- Modify: `backend/services/reply_tracking_service.py`
- Modify: `backend/api/emails.py`
- Test: `backend/tests/test_reply_tracking.py`

- [ ] **Step 1: Write a test for identifying sent emails awaiting replies**
- [ ] **Step 2: Implement a background task that runs daily (or periodically) to flag missing replies**
- [ ] **Step 3: Expose `requires_reply` and `schedule_conflict` in `/api/emails` response, verifying the router remains protected by `get_auth_context` and uses the authenticated context.**

## Task 4: CalDAV/WebDAV Background Sync

**Files:**
- Modify: `backend/services/caldav_service.py`
- Modify: `backend/services/webdav_service.py`
- Test: `backend/tests/test_dav_sync.py`

- [ ] **Step 1: Write tests for CalDAV event parsing and WebDAV file listing**
- [ ] **Step 2: Implement `sync_caldav_accounts` to fetch and store events locally**
- [ ] **Step 3: Implement `sync_webdav_folders` to fetch folder structures**
- [ ] **Step 4: Ensure it supports N-accounts and ties data back to the `user_id`**
