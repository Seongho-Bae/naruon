import pytest

from services.threading_service import assign_thread_id


class _Row:
    def __init__(self, message_id, thread_id):
        self.message_id = message_id
        self.thread_id = thread_id

class _Result:
    def __init__(self, value):
        self._value = value

    def all(self):
        if self._value is None:
            return []
        # Support mocking rows for the IN query.
        # It's a bit hacky, but test logic expects to pull out the string 'value'
        # The query will select message_id and thread_id.
        # We can just mock a row with thread_id = value and message_id = "mock_message_id"
        # But wait, the thread_id lookup maps by message_id. We need to know which candidate the value corresponds to.
        # Actually, in the test the value is just the first thread_id it should find.
        # Let's map it to an arbitrary candidate. Since we only pop one value.
        # We will adjust how the mock works to support the all() call properly.
        # If there's a value, we just return a list with one mocked row.
        return [_Row("mock_id", self._value)]

    def scalar_one_or_none(self):
        return self._value


class _SequentialSession:
    def __init__(self, values):
        self._values = list(values)
        self.execute_count = 0

    async def execute(self, _query):
        self.execute_count += 1
        value = self._values.pop(0) if self._values else None

        # When `_query` has an IN clause, it tries to fetch multiple values
        # Let's see if we can extract the searched IDs from the query to mock it better.
        # But we don't have access to the compiled query values easily.
        # For our simple tests, we can just return the single mocked value for ALL requested IDs,
        # or just mock it so that the first requested ID has this value.

        # Let's inspect the query to see the IN clause elements? No, too complex.
        # We will just return a Result with the thread_id.
        # To make it work with `found_threads.get(candidate)`, we should return the candidate.
        # But we don't know the candidate.
        # Wait, the code does: `found_threads.get(candidate) or found_threads.get(f"<{candidate}>")`
        # We can mock `all()` to return a special object where ANY access works, or just a list of rows for the candidates?
        # Actually, if we just modify the mock... Wait.
        pass

        return _ResultMock(value, _query)

class _ResultMock:
    def __init__(self, value, query):
        self.value = value
        self.query = query

    def all(self):
        if self.value is None:
            return []

        # Determine which ids were queried based on compiling the query.
        # Since we don't need a full DB, we can just extract the parameters from the query's criteria
        # In SQLAlchemy, we can compile the statement.
        # But for simpler tests, `self.value` acts as a generic "found thread id" for whatever the code evaluates.
        # The code iterates existing_candidates and checks `found_threads.get(candidate)`.
        # So we can just create an object where .get() works for anything, or populate it with the IDs
        # present in the right-side of the IN clause.

        # To avoid hardcoding, we can use a custom dictionary in the production code if needed, but we can't change production code for tests.
        # The easiest way is to extract the IDs from the query string or parameters.
        try:
            params = self.query.compile().params

            # Find the parameter that is a list (this is the IN clause parameter)
            ids = []
            for k, v in params.items():
                if isinstance(v, list):
                    ids.extend(v)
            if not ids:
                # If we couldn't find a list, just fallback
                ids = ["<parent@example.com>", "parent@example.com", "<root@example.com>", "root@example.com"]
        except Exception:
            # Fallback if compile fails
            ids = ["<parent@example.com>", "parent@example.com", "<root@example.com>", "root@example.com"]

        return [_Row(m_id, self.value) for m_id in ids]


class _QueryCapturingSession(_SequentialSession):
    def __init__(self, values):
        super().__init__(values)
        self.queries = []

    async def execute(self, query):
        self.queries.append(query)
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
        user_id="testuser",
        organization_id="org-acme",
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
        user_id="testuser",
        organization_id="org-acme",
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
        user_id="testuser",
        organization_id="org-acme",
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
        user_id="testuser",
        organization_id="org-acme",
    )

    assert thread_id == "root@example.com"


@pytest.mark.asyncio
async def test_forwarded_subject_alone_does_not_merge_unrelated_thread():
    session = _SequentialSession(["unrelated-thread"])

    thread_id = await assign_thread_id(
        session,
        {
            "message_id": "<forwarded-copy@example.com>",
            "in_reply_to": None,
            "references": None,
            "subject": "Fwd: Q2 출시 계획",
        },
        user_id="testuser",
        organization_id="org-acme",
    )

    assert thread_id == "forwarded-copy@example.com"
    assert session.execute_count == 0


@pytest.mark.asyncio
async def test_existing_thread_lookup_is_scoped_to_owner_and_organization():
    session = _QueryCapturingSession(["thread-123"])

    thread_id = await assign_thread_id(
        session,
        {
            "message_id": "<reply@example.com>",
            "in_reply_to": "<parent@example.com>",
            "references": None,
        },
        user_id="testuser",
        organization_id="org-acme",
    )

    assert thread_id == "thread-123"
    query_text = str(session.queries[-1]).lower()
    assert "emails.user_id" in query_text
    assert "emails.organization_id" in query_text
