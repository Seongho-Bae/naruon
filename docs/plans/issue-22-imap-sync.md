# Issue 22: Implement Background IMAP Email Sync Worker

## Objective
이메일 클라이언트의 핵심 기능인 IMAP 백그라운드 동기화 워커를 구현합니다. `aioimaplib`를 사용하여 주기적으로 이메일을 가져오고 DB에 저장하는 루프를 만들며, FastAPI 앱 생명주기에 연동합니다.

## Tasks

### Task 1: Create `imap_worker.py`
**Context**: We need a background task that runs continuously to fetch emails from the configured IMAP server using `aioimaplib` and saves them using the existing DB and parsing utilities.
**Requirements**:
- Create `backend/services/imap_worker.py`.
- Implement `ImapSyncWorker` class.
- Provide `start()` and `stop()` methods.
- The `start()` method should run an `asyncio` task that loops every minute (or a configurable interval).
- Inside the loop, connect to `settings.IMAP_SERVER` via `aioimaplib`, fetch recent emails (or mock fetching by printing "Fetching emails..." if the full DB flow is too complex to wire up immediately, but ideally integrate with `archive.py`).
- Implement basic error handling and reconnection logic.

### Task 2: Integrate with FastAPI Lifecycle
**Context**: The worker needs to start when the FastAPI server starts and stop gracefully when it shuts down.
**Requirements**:
- Update `backend/main.py`.
- Import `ImapSyncWorker`.
- Create a global instance of the worker.
- Use FastAPI's lifespan events (or startup/shutdown events) to call `worker.start()` and `worker.stop()`.
- Add a simple healthcheck or status endpoint `/api/sync/status` to verify if the worker is running.