import xml.etree.ElementTree as ET

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from api.auth import get_auth_context
from main import app

AUTH_HEADERS = {
    "X-User-Id": "user123",
    "X-User-Role": "organization_admin",
    "X-Organization-Id": "org-acme",
}


def test_dav_rejects_missing_auth():
    with TestClient(app) as client:
        response = client.request("PROPFIND", "/dav/user123/projects/")
        assert response.status_code == 401


def test_dav_route_uses_signed_session_dependency():
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == "/dav/{path:path}":
            dependencies = {dependency.dependency for dependency in route.dependencies}
            assert get_auth_context in dependencies
            return

    raise AssertionError("DAV route is not registered")


def test_dav_options(dev_auth_dependency_overrides):
    with TestClient(app) as client:
        response = client.options("/dav/user123/projects/", headers=AUTH_HEADERS)
        assert response.status_code == 200
        assert "calendar-access" in response.headers.get("DAV", "")


def test_dav_rejects_different_user_path(dev_auth_dependency_overrides):
    with TestClient(app) as client:
        response = client.request(
            "PROPFIND", "/dav/other-user/projects/", headers=AUTH_HEADERS
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "DAV path belongs to a different user"


def test_dav_propfind(dev_auth_dependency_overrides):
    with TestClient(app) as client:
        response = client.request(
            "PROPFIND", "/dav/user123/projects/", headers=AUTH_HEADERS
        )
        assert response.status_code == 207
        assert "<D:multistatus" in response.text
        root = ET.fromstring(response.text)
        assert root.find(".//{DAV:}collection") is not None


def test_dav_propfind_escapes_path_values(dev_auth_dependency_overrides):
    with TestClient(app) as client:
        response = client.request(
            "PROPFIND", "/dav/user123/projects/x%26y%3Cz%3E", headers=AUTH_HEADERS
        )
        assert response.status_code == 207
        assert "x&amp;y&lt;z&gt;" in response.text
        assert "x&y<z>" not in response.text
        ET.fromstring(response.text)


def test_dav_put(dev_auth_dependency_overrides):
    with TestClient(app) as client:
        response = client.put(
            "/dav/user123/projects/file.ics",
            content=b"BEGIN:VCALENDAR\r\nEND:VCALENDAR",
            headers=AUTH_HEADERS,
        )
        assert response.status_code == 501
        assert "Provider-backed DAV writeback is not implemented" in response.text
        assert "etag" not in {header.lower() for header in response.headers}
