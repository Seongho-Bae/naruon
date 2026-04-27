# O3: Implement Attachment Parsing and Hybrid Search Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement attachment parsing and hybrid search to allow querying attachment contents alongside email bodies.

**Architecture:** We will update `email_parser.py` to extract attachment text, add an `Attachment` model with an embedding column, create/update `import_fixtures.py` to process and save these embeddings, and update `search.py` to search both email bodies and attachments.

**Tech Stack:** Python, FastAPI, SQLAlchemy, pgvector

---

### Task 1: Update EmailData and Email Parser

**Files:**
- Modify: `backend/services/email_parser.py`

**Step 1: Update EmailData**
Add an `attachments` field to `EmailData` TypedDict. It should be a list of dictionaries with `filename` and `content`.

**Step 2: Update parse_eml**
Modify the attachment skipping logic in `parse_eml` to extract text from plain text attachments (e.g., `text/plain`). If it's another content type, try to extract it if simple (or just ignore for now if not easily parseable, focus on text/plain).

### Task 2: Create Attachment Database Model

**Files:**
- Modify: `backend/db/models.py`

**Step 1: Define Attachment Model**
Add `Attachment` model inheriting from `Base`.
Columns:
- `id`: Integer primary key
- `email_id`: Integer, ForeignKey to `emails.id`
- `filename`: String
- `content`: Text
- `embedding`: Vector(1536)

**Step 2: Add Relationship**
Update `Email` model to include `attachments = relationship("Attachment", back_populates="email")` and add `email = relationship("Email", back_populates="attachments")` to `Attachment`.

### Task 3: Create/Update import_fixtures.py

**Files:**
- Create/Modify: `backend/import_fixtures.py`

**Step 1: Write fixture importer**
Write a script that reads `.eml` files from a fixtures directory, parses them, generates embeddings for the email body and all attachments, and saves them to the database. (If it doesn't exist, create it. If it does, update it).

### Task 4: Update Search API

**Files:**
- Modify: `backend/api/search.py`

**Step 1: Update hybrid_search**
Modify the search query to check both `Email` and `Attachment` embeddings. Combine scores. If an attachment matches, return the corresponding `Email` with a combined or highest score.

### Task 5: Verify tests

**Files:**
- Modify: `backend/tests/test_email_parser.py` (if exists) or create it.
- Modify: `backend/tests/test_search.py`

**Step 1: Write tests for parser and search**
Verify attachments are parsed correctly and search returns emails based on attachment content.