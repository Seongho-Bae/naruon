from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_get_tools_returns_valid_data():
    response = client.get("/tools")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5

    first_tool = data[0]
    assert "name" in first_tool
    assert "description" in first_tool
    assert "category" in first_tool
    assert first_tool["category"] == "이메일 분석"
