import html
import string
from html.parser import HTMLParser

_RAW_TEXT_TAGS = {"script", "style", "template"}
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
    "li",
    "main",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tr",
    "ul",
}
_LOCAL_PART_CHARACTERS = set(
    string.ascii_letters + string.digits + ".!#$%&*+-/=?^_`{|}~"
)
_DOMAIN_CHARACTERS = set(string.ascii_letters + string.digits + ".-")


def _decode_entities(value: str) -> str:
    decoded = value
    for _ in range(3):
        next_value = html.unescape(decoded)
        if next_value == decoded:
            break
        decoded = next_value
    return decoded


def _looks_like_angle_email(value: str) -> bool:
    if value.count("@") != 1 or any(character.isspace() for character in value):
        return False
    if any(character in value for character in "<>\"'"):
        return False

    local_part, domain = value.rsplit("@", 1)
    if not local_part or not domain or "." not in domain:
        return False
    if any(character not in _LOCAL_PART_CHARACTERS for character in local_part):
        return False
    if any(character not in _DOMAIN_CHARACTERS for character in domain):
        return False
    if domain.startswith((".", "-")) or domain.endswith((".", "-")):
        return False
    if ".." in domain:
        return False
    return True


def _mask_angle_emails(value: str) -> tuple[str, dict[str, str]]:
    placeholders: dict[str, str] = {}
    parts: list[str] = []
    cursor = 0

    while cursor < len(value):
        start = value.find("<", cursor)
        if start == -1:
            parts.append(value[cursor:])
            break

        end = value.find(">", start + 1)
        if end == -1:
            parts.append(value[cursor:])
            break

        candidate = value[start + 1 : end]
        before_is_boundary = start == 0 or value[start - 1].isspace()
        after_is_boundary = (
            end + 1 == len(value)
            or value[end + 1].isspace()
            or value[end + 1] in ",.;:)]}"
        )
        if (
            _looks_like_angle_email(candidate)
            and before_is_boundary
            and after_is_boundary
        ):
            token = f"\ue000email{len(placeholders)}\ue001"
            placeholders[token] = value[start : end + 1]
            parts.append(value[cursor:start])
            parts.append(token)
            cursor = end + 1
            continue

        parts.append(value[cursor : start + 1])
        cursor = start + 1

    return "".join(parts), placeholders


def contains_html_markup(value: str) -> bool:
    decoded = _decode_entities(value)
    cursor = 0
    while cursor < len(decoded):
        if decoded[cursor] != "<":
            cursor += 1
            continue

        tag_start = cursor + 1
        if tag_start >= len(decoded):
            return False

        if decoded.startswith("!--", tag_start):
            return decoded.find("-->", tag_start + 3) != -1

        if decoded[tag_start].isspace():
            space_cursor = tag_start
            while space_cursor < len(decoded) and decoded[space_cursor].isspace():
                space_cursor += 1
            if space_cursor >= len(decoded) or decoded[space_cursor] != "/":
                cursor += 1
                continue
            tag_start = space_cursor

        if decoded[tag_start] in {"!", "?"}:
            return decoded.find(">", tag_start + 1) != -1

        if decoded[tag_start] == "/":
            tag_start += 1
            while tag_start < len(decoded) and decoded[tag_start].isspace():
                tag_start += 1

        closing = decoded.find(">", tag_start + 1)
        if tag_start < len(decoded) and decoded[tag_start].isalpha() and closing != -1:
            tag_content = decoded[tag_start:closing].strip()
            if _looks_like_angle_email(tag_content):
                cursor = closing + 1
                continue
            return True
        cursor += 1
    return False


def _is_tag_like_segment(value: str) -> bool:
    candidate = value.strip()
    if not candidate:
        return False
    if candidate.startswith("!--") or candidate[0] in {"!", "?"}:
        return True
    if candidate[0] == "/":
        candidate = candidate[1:].lstrip()
    return bool(candidate and candidate[0].isalpha())


def _strip_tag_like_segments(value: str) -> str:
    parts: list[str] = []
    cursor = 0
    while cursor < len(value):
        start = value.find("<", cursor)
        if start == -1:
            parts.append(value[cursor:])
            break

        end = value.find(">", start + 1)
        if end == -1:
            parts.append(value[cursor:])
            break

        parts.append(value[cursor:start])
        candidate = value[start + 1 : end]
        if not _is_tag_like_segment(candidate):
            parts.append(value[start : end + 1])
        cursor = end + 1
    return "".join(parts)


class _PlainTextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._raw_text_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        normalized = tag.lower()
        if normalized in _RAW_TEXT_TAGS:
            self._raw_text_depth += 1
            return
        if normalized in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.lower()
        if normalized in _RAW_TEXT_TAGS:
            self._raw_text_depth = max(0, self._raw_text_depth - 1)
            return
        if normalized in _BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._raw_text_depth == 0:
            self._parts.append(_strip_tag_like_segments(data))

    def get_text(self) -> str:
        lines = []
        for line in "".join(self._parts).splitlines():
            normalized_line = " ".join(line.split())
            if normalized_line:
                lines.append(normalized_line)
        return "\n".join(lines).strip()


def strip_html_markup(value: str) -> str:
    decoded = _decode_entities(value)
    masked, placeholders = _mask_angle_emails(decoded)
    parser = _PlainTextHTMLParser()
    parser.feed(masked)
    parser.close()
    text = parser.get_text()
    for token, original in placeholders.items():
        text = text.replace(token, original)
    return text
