import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    # Pass default headers for authentication
    with TestClient(app, headers={"X-User-Id": "testuser"}) as c:
        yield c

def test_runtime_config_returns_non_secret_data(client):
    response = client.get("/api/runtime-config")
    assert response.status_code == 200
    data = response.json()
    assert "product_name" in data
    assert "features" in data
    # Ensure no secrets leak
    assert "openai_api_key" not in data
    assert "encryption_key" not in data
