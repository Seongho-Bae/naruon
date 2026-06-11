## 2024-05-24 - SQLAlchemy batched testing mocks
**Learning:** When refactoring SQLAlchemy queries from scalar to batched results (using `.in_()`), custom mock classes in backend tests (like `_SequentialSession` and `_ScalarResult`) must be updated to implement `.all()` returning mock row objects.
**Action:** When doing database query optimizations, immediately check the test files for custom Session mocks and update them to mirror the new query's return structure.

## 2024-05-24 - Backend config validation during testing
**Learning:** Pydantic validation for `AUTH_SESSION_HMAC_SECRET` in `core.config` requires a valid base64-encoded string of sufficient length. Hardcoding simplistic values like "supersecret" will fail.
**Action:** Use a valid base64 string like `c29tZXJhbmRvbXNlY3JldHN0cmluZ3RoYXRpc2xvbmc=` when setting environment variables for local testing.
