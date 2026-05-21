import pytest

from services.text_safety import contains_html_markup, strip_html_markup


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ("<img/src=x onerror=alert(1)>", ""),
        ("<svg/onload=alert(1)>", ""),
        ('<a href="javascript:alert(1)">click me</a>', "click me"),
        ("<!--><script>alert(1)</script>-->", ""),
        ("<script@x.y>alert(1)</script@x.y>", "alert(1)"),
    ],
)
def test_strip_html_markup_never_returns_raw_tag_like_payloads(payload, expected):
    assert strip_html_markup(payload) == expected


@pytest.mark.parametrize(
    "safe_text",
    [
        "Alice <alice@example.com>",
        'AT&T: 2 < 3 and Tom "T"',
    ],
)
def test_strip_html_markup_preserves_safe_angle_bracket_display_text(safe_text):
    assert strip_html_markup(safe_text) == safe_text


@pytest.mark.parametrize(
    "payload",
    [
        "&lt;img src=x onerror=alert(document.domain)&gt;",
        "<img/src=x onerror=alert(1)>",
        "<svg/onload=alert(1)>",
        "<math/href=javascript:alert(1)@x>",
    ],
)
def test_contains_html_markup_flags_browser_tolerated_active_markup(payload):
    assert contains_html_markup(payload) is True
