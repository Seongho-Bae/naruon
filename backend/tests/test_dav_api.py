import xml.etree.ElementTree as ET
from urllib.parse import unquote

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


def test_dav_rejects_path_traversal(dev_auth_dependency_overrides):
    with TestClient(app) as client:
        response = client.request(
            "PROPFIND", "/dav/user123/..%2Fother-user/projects/", headers=AUTH_HEADERS
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "DAV path must include an owner user"


def test_dav_rejects_ownerless_path(dev_auth_dependency_overrides):
    with TestClient(app) as client:
        response = client.request("PROPFIND", "/dav/", headers=AUTH_HEADERS)
        assert response.status_code == 403
        assert response.json()["detail"] == "DAV path must include an owner user"


def test_dav_rejects_ownerless_options_before_capability_discovery(
    dev_auth_dependency_overrides,
):
    with TestClient(app) as client:
        response = client.options("/dav/", headers=AUTH_HEADERS)
        assert response.status_code == 403
        assert "dav" not in {header.lower() for header in response.headers}
        assert response.json()["detail"] == "DAV path must include an owner user"


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


def test_dav_log_injection_prevention(dev_auth_dependency_overrides, caplog):
    import asyncio
    import logging

    from fastapi import Request

    from api.auth import AuthContext
    from api.dav import dav_handler

    caplog.set_level(logging.INFO, logger="api.dav")
    malicious_path = "user123/projects/test%1B%5B31minjected%0A%0D"
    scope = {"type": "http", "method": "PROPFIND", "headers": []}

    async def run_handler():
        req = Request(scope)
        auth_context = AuthContext(
            user_id="user123",
            organization_id="org-acme",
            role="organization_admin",
            group_ids=[],
            workspace_id="workspace-org-acme",
        )
        await dav_handler(
            request=req,
            path=unquote(malicious_path),
            auth_context=auth_context,
        )

    asyncio.run(run_handler())

    dav_messages = [
        record.getMessage()
        for record in caplog.records
        if "DAV Request" in record.getMessage()
    ]

    assert dav_messages
    assert all("\x1b[31m" not in message for message in dav_messages)
    assert all("\n" not in message for message in dav_messages)
    assert any("\\x1b[31minjected\\n\\r" in message for message in dav_messages)
