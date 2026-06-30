from zipfile import ZipFile

import pytest

from scripts import private_mail_http_smoke as smoke


def test_selected_upload_files_reads_emlx_inside_zip(tmp_path, monkeypatch):
    raw = (
        b"Subject: Quarterly needle\r\n"
        b"From: sender@example.com\r\n"
        b"To: recipient@example.com\r\n"
        b"\r\n"
        b"body"
    )
    emlx = str(len(raw)).encode() + b"\n" + raw + b"\nmetadata"
    archive_path = tmp_path / "archive.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("nested/original.emlx", emlx)
    cache_dir = tmp_path / "cache"
    monkeypatch.setenv("NARUON_PRIVATE_MAIL_CACHE", str(cache_dir))

    selected = smoke._selected_upload_files(
        tmp_path,
        ["needle"],
        5,
        max_parse_bytes=1000,
        match_mode="exact",
        progress_every=0,
    )

    assert [path.name for path in selected] == ["hit_001.eml"]
    assert selected[0].read_bytes() == raw


def test_selected_upload_files_creates_default_cache_path(tmp_path, monkeypatch):
    raw = b"Subject: alpha query\r\n\r\nbody"
    mail_file = tmp_path / "message.eml"
    mail_file.write_bytes(raw)
    monkeypatch.delenv("NARUON_PRIVATE_MAIL_CACHE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    selected = smoke._selected_upload_files(
        tmp_path,
        ["query"],
        1,
        max_parse_bytes=1000,
        match_mode="exact",
        progress_every=0,
    )

    assert [p.name for p in selected] == ["hit_001.eml"]
    assert selected[0].exists()
    assert (tmp_path / "home" / ".cache" / "naruon" / "private-mail-upload-cache").exists()


def test_large_message_match_uses_header_probe_without_full_parse(monkeypatch):
    raw = b"Subject: needle\r\n\r\n" + (b"x" * 128)

    def fail_full_parse(*args, **kwargs):
        raise AssertionError("large message should not be fully parsed")

    monkeypatch.setattr(smoke, "message_from_bytes", fail_full_parse)

    assert smoke._matches_queries(
        raw,
        ["needle"],
        max_parse_bytes=16,
        match_mode="exact",
    )


def test_all_terms_match_mode_ignores_separators():
    raw = b"Subject: alpha beta PU minutes\r\n\r\nbody"

    assert smoke._matches_queries(
        raw,
        ["alpha betaPU minutes"],
        max_parse_bytes=1000,
        match_mode="all-terms",
    )


@pytest.mark.parametrize(
    "raw,expected",
    [
        (b"12\nhello world!metadata", b"hello world!"),
        (b"not-length\nhello world!", b"not-length\nhello world!"),
    ],
)
def test_strip_emlx_prefix(raw, expected):
    assert smoke._strip_emlx_prefix(raw) == expected


def test_post_json_with_retry_retries_transient_statuses(monkeypatch):
    calls: list[tuple[str, str]] = []

    def fake_request(base_url, token, method, path, *, body=None, content_type=None, timeout=120.0):
        calls.append((method, path))
        if len(calls) == 1:
            return 503, b"retry-later"
        if len(calls) == 2:
            return 502, b"retry-later"
        return 200, b'{"ok":true}'

    monkeypatch.setattr(smoke, "_request", fake_request)
    result = smoke._post_json_with_retry(
        "http://127.0.0.1:8000",
        "token",
        "/api/search",
        {"query": "ok"},
        attempts=3,
        delay_seconds=0.0,
        timeout=120.0,
    )

    assert result == {"ok": True}
    assert len(calls) == 3


def test_post_json_with_retry_stops_on_non_transient_status(monkeypatch):
    calls = []

    def fake_request(base_url, token, method, path, *, body=None, content_type=None, timeout=120.0):
        calls.append((method, path))
        return 401, b"unauthorized"

    monkeypatch.setattr(smoke, "_request", fake_request)
    with pytest.raises(smoke._RequestFailed) as exc:
        smoke._post_json_with_retry(
            "http://127.0.0.1:8000",
            "token",
            "/api/search",
            {"query": "ok"},
            attempts=3,
            delay_seconds=0.0,
            timeout=120.0,
        )
    assert exc.value.status == 401
    assert len(calls) == 1


def test_json_or_empty_raises_bad_response_for_html_payload():
    with pytest.raises(smoke._BadResponse):
        smoke._json_or_empty(200, b"<html></html>")


def test_request_json_with_retry_no_retry_after_bad_response(monkeypatch):
    calls: list[tuple[str, str]] = []

    def fake_request(base_url, token, method, path, *, body=None, content_type=None, timeout=120.0):
        calls.append((method, path))
        return 200, b"<html></html>"

    monkeypatch.setattr(smoke, "_request", fake_request)

    with pytest.raises(smoke._BadResponse):
        smoke._post_json_with_retry(
            "http://127.0.0.1:8000",
            "token",
            "/api/test",
            {"query": "ok"},
            attempts=3,
            delay_seconds=0.0,
            timeout=120.0,
        )
    assert len(calls) == 1


def test_post_json_with_retry_retries_network_error(monkeypatch):
    calls: list[tuple[str, str]] = []

    def fake_request(base_url, token, method, path, *, body=None, content_type=None, timeout=120.0):
        calls.append((method, path))
        if len(calls) == 1:
            raise smoke._RequestNetworkError("connection refused")
        return 200, b'{"ok":true}'

    monkeypatch.setattr(smoke, "_request", fake_request)

    result = smoke._post_json_with_retry(
        "http://127.0.0.1:8000",
        "token",
        "/api/search",
        {"query": "ok"},
        attempts=2,
        delay_seconds=0.0,
        timeout=120.0,
    )

    assert result == {"ok": True}
    assert len(calls) == 2


def test_post_json_with_retry_raises_network_error_after_retries(monkeypatch):
    calls: list[tuple[str, str]] = []

    def fake_request(base_url, token, method, path, *, body=None, content_type=None, timeout=120.0):
        calls.append((method, path))
        raise smoke._RequestNetworkError("connection refused")

    monkeypatch.setattr(smoke, "_request", fake_request)

    with pytest.raises(smoke._RequestNetworkError):
        smoke._post_json_with_retry(
            "http://127.0.0.1:8000",
            "token",
            "/api/search",
            {"query": "ok"},
            attempts=2,
            delay_seconds=0.0,
            timeout=120.0,
        )

    assert len(calls) == 2


def test_check_frontend_session_skips_on_missing_frontend(monkeypatch):
    monkeypatch.setattr(
        smoke,
        "_post_json_with_retry",
        lambda *_a, **_k: (_ for _ in ()).throw(smoke._RequestFailed(404, b"not found")),
    )
    assert smoke._check_frontend_session("http://127.0.0.1:8000", "token") is None


def test_check_frontend_session_parses_claims(monkeypatch):
    monkeypatch.setattr(
        smoke,
        "_post_json_with_retry",
        lambda *_a, **_k: {
            "authenticated": True,
            "claims": {"userId": "user-1", "organizationId": "org-1", "workspaceId": "ws-1"},
        },
    )

    claims = smoke._check_frontend_session("http://127.0.0.1:8000", "token")
    assert claims["claims"]["userId"] == "user-1"
    assert claims["claims"]["organizationId"] == "org-1"
    assert claims["claims"]["workspaceId"] == "ws-1"


def test_check_frontend_session_rejects_unauthenticated(monkeypatch):
    monkeypatch.setattr(
        smoke,
        "_post_json_with_retry",
        lambda *_a, **_k: {"authenticated": False},
    )
    with pytest.raises(SystemExit):
        smoke._check_frontend_session("http://127.0.0.1:8000", "token")
