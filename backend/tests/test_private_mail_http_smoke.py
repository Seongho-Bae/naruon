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
