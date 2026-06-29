import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

@patch("api.llm.extract_todos_and_summary", new_callable=AsyncMock)
def test_summarize_generic_error_returns_500(mock_extract, client):
    mock_extract.side_effect = Exception("Generic Error")

    resp = client.post(
        "/api/llm/summarize",
        json={"email_body": "test email"},
    )
    assert resp.status_code == 500
    assert resp.json() == {"detail": "An internal server error occurred while processing the request."}

@patch("api.llm.draft_reply", new_callable=AsyncMock)
def test_draft_generic_error_returns_500(mock_draft, client):
    mock_draft.side_effect = Exception("Generic Error")

    resp = client.post(
        "/api/llm/draft",
        json={"email_body": "test email", "instruction": "reply nicely"},
    )
    assert resp.status_code == 500
    assert resp.json() == {"detail": "An internal server error occurred while processing the request."}
