import html
import re
from html.parser import HTMLParser

_WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")
_BLANK_LINE_RE = re.compile(r"\n{3,}")
_BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "div",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "p",
    "section",
    "table",
    "td",
    "th",
    "tr",
}
_DANGEROUS_CONTENT_TAGS = {
    "script",
    "style",
    "iframe",
    "object",
    "embed",
    "svg",
    "math",
}


class _TextOnlyHTMLParser(HTMLParser):
    """Extract inert text from HTML without preserving tags or attributes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._dangerous_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        normalized_tag = tag.lower()
        if normalized_tag in _DANGEROUS_CONTENT_TAGS:
            self._dangerous_depth += 1
            return
        if normalized_tag in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if normalized_tag in _DANGEROUS_CONTENT_TAGS:
            if self._dangerous_depth:
                self._dangerous_depth -= 1
            return
        if normalized_tag in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._dangerous_depth:
            self._parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if not self._dangerous_depth:
            self._parts.append(html.unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        if not self._dangerous_depth:
            self._parts.append(html.unescape(f"&#{name};"))

    def text(self) -> str:
        return "".join(self._parts)


def sanitize_email_body_text(value: str | None) -> str:
    """Return email body text with active HTML content and markup removed."""
    if value is None:
        return ""

    parser = _TextOnlyHTMLParser()
    parser.feed(str(value))
    parser.close()
    text = html.unescape(parser.text())
    text = _WHITESPACE_RE.sub(" ", text)
    text = _BLANK_LINE_RE.sub("\n\n", text)
    return text.strip()
