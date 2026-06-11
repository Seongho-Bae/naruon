import pytest
from services.threading_service import assign_thread_id

class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def all(self):
        return self._value

class _SequentialSession:
    def __init__(self, values):
        self._values = list(values)
        self.execute_count = 0

    async def execute(self, _query):
        self.execute_count += 1
        value = self._values.pop(0) if self._values else []
        return _ScalarResult(value)

@pytest.mark.asyncio
async def test_assign_thread_id_many_candidates():
    # Provide an empty list for the bulk query
    session = _SequentialSession([[]])

    # Create 100 references.
    refs = " ".join([f"<ref{i}@example.com>" for i in range(100)])

    _thread_id = await assign_thread_id(
        session,
        {
            "message_id": "<reply@example.com>",
            "in_reply_to": "<parent@example.com>",
            "references": refs,
        },
        user_id="testuser",
        organization_id="org-acme",
    )

    # Verify that only a single bulk query was executed instead of one per candidate
    assert session.execute_count == 1, f"Expected 1 query, but executed {session.execute_count}"
    print(f"Executed queries: {session.execute_count}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_assign_thread_id_many_candidates())
