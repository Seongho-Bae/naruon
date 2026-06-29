import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

@patch("api.llm.extract_todos_and_summary", new_callable=AsyncMock)
def test_summarize_http_exception(mock_extract, client):
    from fastapi import HTTPException
    mock_extract.side_effect = HTTPException(status_code=400, detail="Bad request")

    resp = client.post(
        "/api/llm/summarize",
        json={"email_body": "test email"},
    )
    assert resp.status_code == 400

@patch("api.llm.draft_reply", new_callable=AsyncMock)
def test_draft_http_exception(mock_draft, client):
    from fastapi import HTTPException
    mock_draft.side_effect = HTTPException(status_code=400, detail="Bad request")

    resp = client.post(
        "/api/llm/draft",
        json={"email_body": "test email", "instruction": "test"},
    )
    assert resp.status_code == 400

@patch("api.llm.translate_email_body", new_callable=AsyncMock)
def test_translate_http_exception(mock_translate, client):
    from fastapi import HTTPException
    mock_translate.side_effect = HTTPException(status_code=400, detail="Bad request")

    resp = client.post(
        "/api/llm/translate",
        json={"email_body": "test email", "target_language": "Korean"},
    )
    assert resp.status_code == 400
