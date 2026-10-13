r"""Private pure text operations for snapshot-contract ADR test support.

The public ``tests.support.adr_contract`` module owns the test-facing API.
These operations parse text and validate the manifest and JSON contract without
filesystem access; callers supply the document text.

Examples
--------
``section_body("## Status\n\nAccepted", "## Status")`` returns ``"\nAccepted"``.
"""

from __future__ import annotations

import dataclasses
import pathlib
import posixpath
import re
import tomllib
import typing as typ

if typ.TYPE_CHECKING:
    import collections.abc as cabc

_MANIFEST_HEADING: typ.Final[str] = "### Contract manifest"
_LINK_PATTERN: typ.Final[re.Pattern[str]] = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)]+)\)")
_INLINE_LITERAL_PATTERN: typ.Final[re.Pattern[str]] = re.compile(
    r"(?<!`)(`+)(?!`)(?:(?!\x00)[\s\S])*?(?<!`)\1(?!`)|<!--(?:(?!\x00)[\s\S])*?(?:-->|$)"
)
_FENCE_CLOSE_PATTERN: typ.Final[re.Pattern[str]] = re.compile(r"^ {0,3}([`~]+)[ \t]*$")

_NORMALIZATION_RULES: typ.Final[frozenset[str]] = frozenset([
    "remove-position",
    "remove-empty-data",
    "merge-plain-text",
    "normalize-line-endings",
    "order-members",
])
_MANIFEST_KEYS: typ.Final[frozenset[str]] = frozenset([
    "contract-version",
    "wenmode",
    "parser",
    "file-extension",
    "normalization",
    "key-order",
    "json-writer",
])
_WRITER_TYPES: typ.Final[dict[str, type[object]]] = {
    "encoding": str,
    "byte-order-mark": bool,
    "ensure-ascii": bool,
    "indent": int,
    "item-separator": str,
    "key-separator": str,
    "allow-nan": bool,
    "sort-keys": bool,
    "trailing-newline": bool,
}

_HEADING_PATTERN: typ.Final[re.Pattern[str]] = re.compile(
    r"^ {0,3}(#{1,6})(?:[ \t]+.*)?$"
)
_FENCE_PATTERN: typ.Final[re.Pattern[str]] = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


@dataclasses.dataclass(slots=True)
class _SourceScanState:
    """Track Markdown literals; e.g. a comment can span multiple lines."""

    fence: str | None = None
    in_comment: bool = False
    code_end: int | None = None

    def resume_code_span(self, offset: int, line_end: int) -> int:
        """Resume code crossing a line; e.g. skip its literal comment marker."""
        cursor = offset
        if self.code_end is not None:
            cursor = min(self.code_end, line_end)
            self.code_end = self.code_end if self.code_end > line_end else None
        return cursor

    def resume_comment(self, source: str, cursor: int, line_end: int) -> int:
        """Resume a comment; e.g. skip text through its closing delimiter."""
        if self.in_comment:
            close = source.find("-->", cursor, line_end)
            self.in_comment = close < 0
            cursor = line_end if self.in_comment else close + 3
        return cursor

    def record_inline_literal(self, match: re.Match[str], line_end: int) -> None:
        """Record a cross-line literal; e.g. retain an open HTML comment."""
        continues = match.end() > line_end
        self.code_end = match.end() if continues and match.group(1) else None
        self.in_comment = continues and self.code_end is None


def _manifest_table(markdown: str) -> dict[str, object]:
    """Validate the fenced table shape; e.g. reject two TOML blocks."""
    blocks = [
        body
        for info, body in _fence_bodies(section_body(markdown, _MANIFEST_HEADING))
        if info == "toml"
    ]
    if len(blocks) != 1:
        message = "contract manifest must contain exactly one TOML block"
        raise ValueError(message)
    contract = _decode_contract(blocks[0])
    if contract.keys() != _MANIFEST_KEYS:
        message = "[snapshot-contract] keys do not match the schema"
        raise ValueError(message)
    return contract


def _decode_contract(text: str) -> dict[str, object]:
    """Translate TOML decoding errors; e.g. an invalid table raises ValueError."""
    try:
        return _contract_table(tomllib.loads(text))
    except (tomllib.TOMLDecodeError, TypeError) as exc:
        message = "contract manifest contains invalid TOML or table types"
        raise ValueError(message) from exc


def _contract_table(value: object) -> dict[str, object]:
    """Require the single root table; e.g. reject unrelated top-level keys."""
    document = _table(value, "manifest")
    if document.keys() != {"snapshot-contract"}:
        message = "manifest must contain only the [snapshot-contract] table"
        raise ValueError(message)
    return _table(document["snapshot-contract"], "[snapshot-contract]")


def _wenmode_range(value: object) -> str:
    """Require ascending bounds; e.g. accept >=0.15.2,<0.16.0."""
    if not isinstance(value, str):
        message = "wenmode must be a string"
        raise TypeError(message)
    match = re.fullmatch(r">=(\d+)\.(\d+)\.(\d+),<(\d+)\.(\d+)\.(\d+)", value)
    if match is None:
        message = "wenmode must use >=MAJOR.MINOR.PATCH,<MAJOR.MINOR.PATCH"
        raise ValueError(message)
    parts = tuple(int(part) for part in match.groups())
    if parts[:3] >= parts[3:]:
        message = "wenmode lower bound must precede its upper bound"
        raise ValueError(message)
    return value


def _writer_settings(value: object) -> dict[str, str | int | bool]:
    """Validate writer fields; e.g. reject a boolean indent."""
    writer = _table(value, "[snapshot-contract.json-writer]")
    if writer.keys() != _WRITER_TYPES.keys():
        message = "[snapshot-contract.json-writer] keys do not match the schema"
        raise ValueError(message)
    for key, expected_type in _WRITER_TYPES.items():
        if type(writer[key]) is not expected_type:
            message = f"JSON writer field {key!r} has the wrong type"
            raise ValueError(message)
    # Exact key and value-type checks above establish this copy's type.
    return typ.cast("dict[str, str | int | bool]", dict(writer))


def section_body(markdown: str, heading: str) -> str:
    """Return a unique heading's body.

    Parameters
    ----------
    markdown : str
        Markdown text containing the section.
    heading : str
        Exact heading, including its leading hash markers.

    Returns
    -------
    str
        Body up to the next heading at the same or a higher level.

    Raises
    ------
    ValueError
        The heading is absent or ambiguous outside fenced blocks.

    Examples
    --------
    ``section_body("## A", "## A")`` returns an empty string.
    """
    lines = markdown.splitlines(keepends=True)
    headings = list(_headings(lines))
    targets = [(index, level) for index, title, level in headings if title == heading]
    if len(targets) != 1:
        problem = "was not found" if not targets else "is ambiguous"
        message = f"Markdown heading {heading!r} {problem}"
        raise ValueError(message)
    start, target_level = targets[0]
    end = next(
        (
            index
            for index, _, level in headings
            if index > start and level <= target_level
        ),
        len(lines),
    )
    return "".join(lines[start + 1 : end])


def _link_targets(markdown: str, source_path: str) -> set[str]:
    """Resolve visible links; ``[next](adr-004.md)`` yields its sibling path."""
    lines = markdown.splitlines(keepends=True)
    visible = "".join(line for _, line, _ in _unfenced_lines(lines))
    # One pass preserves whether a code span or HTML comment opened first.
    visible = _INLINE_LITERAL_PATTERN.sub(" ", visible)
    return {
        posixpath.normpath(
            str(pathlib.PurePosixPath(source_path).parent / target.split("#")[0])
        )
        for _, target in _LINK_PATTERN.findall(visible)
    }


def _mask_fenced_source(lines: cabc.Sequence[str]) -> str:
    """Mask real fences; e.g. a commented delimiter stays visible."""
    source = "".join(lines)
    masked = list(source)
    state = _SourceScanState()
    offset = 0
    while offset < len(source):
        line_end = (
            len(source) if (newline := source.find("\n", offset)) < 0 else newline + 1
        )
        content = source[offset:line_end].rstrip("\r\n")
        if _advance_fence_state(content, offset, state):
            masked[offset : offset + len(content)] = "\x00" * len(content)
        else:
            _scan_inline_literals(source, offset, line_end, state)
        offset = line_end
    return "".join(masked)


def _advance_fence_state(content: str, offset: int, state: _SourceScanState) -> bool:
    """Advance fence state; e.g. ignore a fence inside an open code span."""
    if state.fence is not None:
        state.fence = None if _is_fence_closing(content, state.fence) else state.fence
        return True
    code_span_is_open = state.code_end is not None and state.code_end > offset
    if state.in_comment or code_span_is_open:
        return False
    if opening := _fence_opening(content):
        state.fence = opening[0]
        return True
    return False


def _scan_inline_literals(
    source: str, offset: int, line_end: int, state: _SourceScanState
) -> None:
    """Scan comments and code spans; e.g. ignore comment markers inside ticks."""
    cursor = state.resume_code_span(offset, line_end)
    cursor = state.resume_comment(source, cursor, line_end)
    for match in _INLINE_LITERAL_PATTERN.finditer(source, cursor):
        if match.start() >= line_end:
            break
        state.record_inline_literal(match, line_end)


def _unfenced_lines(
    lines: cabc.Sequence[str],
) -> cabc.Iterator[tuple[int, str, bool]]:
    """Yield lines outside fences and comments; e.g. retain a multiline code span."""
    source = _mask_fenced_source(lines)
    code_spans = _inline_code_spans(source)
    ignored: set[int] = set()
    state: str | None = None
    offset = 0
    span_context = (code_spans, ignored)
    for index, line in enumerate(lines):
        line_end = offset + len(line)
        state, is_visible, inside_code = _scan_unfenced_line(
            line, (offset, line_end), state, span_context
        )
        if is_visible:
            yield index, line, inside_code
        offset = line_end


def _scan_unfenced_line(
    line: str,
    line_bounds: tuple[int, int],
    state: str | None,
    span_context: tuple[list[tuple[int, int]], set[int]],
) -> tuple[str | None, bool, bool]:
    """Advance one line; e.g. mask a code-span opener before comment parsing."""
    code_spans, ignored = span_context
    active = _active_code_span_indexes(code_spans, ignored, line_bounds)
    inside_code = any(code_spans[index][0] < line_bounds[0] for index in active)
    content = line.rstrip("\r\n")
    if state is None:
        content = _mask_code_spans(line, line_bounds, code_spans, active)
    state, is_visible = _advance_unfenced_state(state, content)
    if state is not None:
        ignored.update(active)
    return state, is_visible, inside_code


def _inline_code_spans(source: str) -> list[tuple[int, int]]:
    """Collect code-span offsets; e.g. retain absolute source positions."""
    matches = _INLINE_LITERAL_PATTERN.finditer(source)
    return [(match.start(), match.end()) for match in matches if match[1]]


def _active_code_span_indexes(
    spans: list[tuple[int, int]], ignored: set[int], bounds: tuple[int, int]
) -> list[int]:
    """Return spans intersecting a line; e.g. find multiline code."""
    return [
        index
        for index, (start, end) in enumerate(spans)
        if index not in ignored and start < bounds[1] and bounds[0] < end
    ]


def _mask_code_spans(
    line: str,
    line_bounds: tuple[int, int],
    code_spans: list[tuple[int, int]],
    active: list[int],
) -> str:
    """Mask code-span text before comment parsing, preserving line endings."""
    content = line.rstrip("\r\n")
    if _fence_opening(content):
        return content
    offset, line_end = line_bounds
    characters = list(line)
    for index in active:
        start, end = code_spans[index]
        for absolute in range(max(start, offset), min(end, line_end)):
            if characters[absolute - offset] not in "\r\n":
                characters[absolute - offset] = " "
    return "".join(characters).rstrip("\r\n")


def _advance_unfenced_state(state: str | None, content: str) -> tuple[str | None, bool]:
    """Advance Markdown state; e.g. a comment's fence marker is inert."""
    if state == "comment":
        return (None, True) if "-->" in content else (state, False)
    if state is not None:
        return None if _is_fence_closing(content, state) else state, False
    if opening := _fence_opening(content):
        return opening[0], False
    content = _INLINE_LITERAL_PATTERN.sub(lambda m: " " if m[1] else m[0], content)
    return ("comment" if content.rfind("<!--") > content.rfind("-->") else None), True


def _headings(lines: cabc.Sequence[str]) -> cabc.Iterator[tuple[int, str, int]]:
    """Yield headings outside fences; e.g. ignore a fenced ``## Status``."""
    for index, line, inside_code in _unfenced_lines(lines):
        if inside_code:
            continue
        content = line.rstrip("\r\n")
        match = _HEADING_PATTERN.match(content)
        if match is not None:
            yield index, content.strip(), len(match.group(1))


def _fence_bodies(markdown: str) -> cabc.Iterator[tuple[str, str]]:
    """Yield fenced contents; e.g. EOF closes a terminal block as in CommonMark."""
    lines = markdown.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        opening = _fence_opening(lines[index].rstrip("\r\n"))
        if opening is None:
            index += 1
            continue
        marker, info = opening
        end = index + 1
        while end < len(lines) and not _is_fence_closing(
            lines[end].rstrip("\r\n"), marker
        ):
            end += 1
        yield info, "".join(lines[index + 1 : end])
        index = end + 1


def _table(value: object, name: str) -> dict[str, object]:
    """Require string-keyed tables; e.g. accept a decoded TOML dictionary."""
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        # The aggregate key check narrows the container's otherwise unknown keys.
        return typ.cast("dict[str, object]", value)
    message = f"{name} must be a TOML table with string keys"
    raise TypeError(message)


def _fence_opening(line: str) -> tuple[str, str] | None:
    """Find a fence; e.g. `````toml`` returns its marker and language."""
    match = _FENCE_PATTERN.match(line)
    return (match.group(1), match.group(2).strip()) if match else None


def _is_fence_closing(line: str, marker: str) -> bool:
    """Match a closer; e.g. four ticks close a three-tick fence."""
    match = _FENCE_CLOSE_PATTERN.match(line)
    fence = match.group(1) if match else ""
    return len(fence) >= len(marker) and set(fence) == {marker[0]}
