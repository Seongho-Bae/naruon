from fastapi.testclient import TestClient
from main import app

def test_dav_options():
    with TestClient(app) as client:
        response = client.options("/dav/user123/projects/")
        assert response.status_code == 200
        assert "calendar-access" in response.headers.get("DAV", "")

def test_dav_propfind():
    with TestClient(app) as client:
        response = client.request("PROPFIND", "/dav/user123/projects/")
        assert response.status_code == 207
        assert "<D:multistatus" in response.text
        assert "<D:collection/>" in response.text

def test_dav_put():
    with TestClient(app) as client:
        response = client.put("/dav/user123/projects/file.ics", content=b"BEGIN:VCALENDAR\r\nEND:VCALENDAR")
        assert response.status_code == 201
