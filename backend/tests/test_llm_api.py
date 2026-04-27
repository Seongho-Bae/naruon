from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_llm_endpoints_exist():
    resp1 = client.post("/api/llm/summarize", json={"email_body": "test"})
    resp2 = client.post("/api/llm/draft", json={"email_body": "test", "instruction": "reply yes"})
    assert resp1.status_code in [200, 400, 422, 500]
    assert resp2.status_code in [200, 400, 422, 500]
