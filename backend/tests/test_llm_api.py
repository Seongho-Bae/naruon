from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@patch("api.llm.extract_todos_and_summary", new_callable=AsyncMock)
@patch("api.llm.draft_reply", new_callable=AsyncMock)
def test_llm_endpoints_exist(mock_draft, mock_extract):
    from services.llm_service import ExtractionResult
    mock_extract.return_value = ExtractionResult(summary="Test summary", todos=["Task 1"])
    mock_draft.return_value = "This is a draft reply."

    resp1 = client.post("/api/llm/summarize", json={"email_body": "test"})
    resp2 = client.post("/api/llm/draft", json={"email_body": "test", "instruction": "reply yes"})
    
    assert resp1.status_code in [200, 400, 422, 500]
    assert resp2.status_code in [200, 400, 422, 500]

@patch("api.llm.extract_todos_and_summary", new_callable=AsyncMock)
def test_summarize_endpoint(mock_extract):
    from services.llm_service import ExtractionResult
    mock_extract.return_value = ExtractionResult(summary="Test summary", todos=["Task 1"])
    
    resp = client.post("/api/llm/summarize", json={"email_body": "test email"})
    assert resp.status_code == 200
    assert resp.json() == {"summary": "Test summary", "todos": ["Task 1"]}

@patch("api.llm.draft_reply", new_callable=AsyncMock)
def test_draft_endpoint(mock_draft):
    mock_draft.return_value = "This is a draft reply."
    
    resp = client.post("/api/llm/draft", json={"email_body": "test email", "instruction": "reply nicely"})
    assert resp.status_code == 200
    assert resp.json() == {"draft": "This is a draft reply."}
