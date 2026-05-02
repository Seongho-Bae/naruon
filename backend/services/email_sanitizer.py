import re

import bleach

SCRIPT_OR_STYLE_BLOCK_RE = re.compile(
    r"<(script|style)\b[^>]*>.*?</\1\s*>",
    flags=re.IGNORECASE | re.DOTALL,
)


def sanitize_email_body(body: str | None) -> str:
    """Return an email body safe to store in and return from JSON APIs."""
    text = "" if body is None else str(body)
    without_active_blocks = SCRIPT_OR_STYLE_BLOCK_RE.sub("", text)
    return bleach.clean(
        without_active_blocks,
        tags=[],
        attributes={},
        protocols=[],
        strip=True,
    )
