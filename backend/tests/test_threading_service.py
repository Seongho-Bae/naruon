import pytest

from services.threading_service import assign_thread_id


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _SequentialSession:
    def __init__(self, values):
        self._values = list(values)
        self.execute_count = 0

    async def execute(self, _query):
        self.execute_count += 1
        value = self._values.pop(0) if self._values else None
        return _ScalarResult(value)


class _RecordingSession(_SequentialSession):
    def __init__(self, values):
        super().__init__(values)
        self.executed_sql: list[str] = []

    async def execute(self, query):
        self.executed_sql.append(str(query).lower())
        return await super().execute(query)


@pytest.mark.asyncio
async def test_reply_before_root_uses_first_reference_as_deterministic_thread_id():
    session = _SequentialSession([None, None, None])

    thread_id = await assign_thread_id(
        session,
        {
            "message_id": "<reply@example.com>",
            "in_reply_to": "<parent@example.com>",
            "references": "<root@example.com> <parent@example.com>",
        },
    )

    assert thread_id == "root@example.com"


@pytest.mark.asyncio
async def test_reply_without_references_uses_in_reply_to_as_deterministic_thread_id():
    session = _SequentialSession([None, None])

    thread_id = await assign_thread_id(
        session,
        {
            "message_id": "<reply@example.com>",
            "in_reply_to": "<parent@example.com>",
            "references": None,
        },
    )

    assert thread_id == "parent@example.com"


@pytest.mark.asyncio
async def test_existing_parent_thread_id_wins_over_deterministic_fallback():
    session = _SequentialSession(["thread-123"])

    thread_id = await assign_thread_id(
        session,
        {
            "message_id": "<reply@example.com>",
            "in_reply_to": "<parent@example.com>",
            "references": "<root@example.com> <parent@example.com>",
        },
    )

    assert thread_id == "thread-123"


@pytest.mark.asyncio
async def test_existing_legacy_bracketed_thread_id_is_normalized():
    session = _SequentialSession(["<root@example.com>"])

    thread_id = await assign_thread_id(
        session,
        {
            "message_id": "<reply@example.com>",
            "in_reply_to": "<root@example.com>",
            "references": "<root@example.com>",
        },
    )

    assert thread_id == "root@example.com"


@pytest.mark.asyncio
async def test_existing_thread_lookup_is_scoped_to_owner():
    session = _RecordingSession(["thread-from-current-user"])

    thread_id = await assign_thread_id(
        session,
        {
            "message_id": "<reply@example.com>",
            "in_reply_to": "<parent@example.com>",
            "references": None,
        },
        user_id="alice",
    )

    assert thread_id == "thread-from-current-user"
    assert any("emails.user_id" in sql for sql in session.executed_sql)
