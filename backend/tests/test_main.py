from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "AI Email Client API"}


def test_root_response_has_security_headers():
    response = client.get("/")

    assert response.headers["strict-transport-security"] == (
        "max-age=31536000; includeSubDomains"
    )
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["content-security-policy"] == (
        "default-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )
    assert "x-xss-protection" not in response.headers


def test_cors_policy_is_restrictive():
    response = client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    allowed_methods = response.headers["access-control-allow-methods"]
    assert "GET" in allowed_methods
    assert "POST" in allowed_methods
    assert "PROPFIND" in allowed_methods
    assert "DELETE" in allowed_methods
    assert "OPTIONS" in allowed_methods
    assert "*" not in allowed_methods

    allowed_headers = response.headers["access-control-allow-headers"]
    assert "Accept" in allowed_headers
    assert "Content-Type" in allowed_headers
    assert "Authorization" in allowed_headers
    assert "*" not in allowed_headers


def test_state_changing_api_rejects_cross_site_fetch_metadata():
    response = client.put(
        "/api/accounts/config",
        headers={"Sec-Fetch-Site": "cross-site"},
        json={"smtp_server": "mail.example.com"},
    )

    assert response.status_code == 403
    assert response.json() == {"error_code": "csrf_fetch_site_rejected"}


def test_state_changing_api_rejects_untrusted_origin():
    response = client.put(
        "/api/accounts/config",
        headers={"Origin": "https://evil.example"},
        json={"smtp_server": "mail.example.com"},
    )

    assert response.status_code == 403
    assert response.json() == {"error_code": "csrf_origin_rejected"}


def test_state_changing_api_allows_trusted_origin_to_reach_auth_gate():
    response = client.put(
        "/api/accounts/config",
        headers={"Origin": "http://localhost:3000"},
        json={"smtp_server": "mail.example.com"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
