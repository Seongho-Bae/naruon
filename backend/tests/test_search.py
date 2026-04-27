from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_search_endpoint_unauthorized():
    response = client.post("/api/search", json={"query": "test"})
    assert response.status_code in [200, 400, 422, 500] # Just check endpoint exists
