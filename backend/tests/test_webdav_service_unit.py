from services.webdav_service import safe_webdav_source_label


def test_safe_webdav_source_label():
    assert safe_webdav_source_label("my_source_123") == "WebDAV source my_source_123"
    assert safe_webdav_source_label(None) == "WebDAV source"
    assert safe_webdav_source_label("") == "WebDAV source"
