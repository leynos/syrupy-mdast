r"""Private pure text operations for snapshot-contract ADR test support.

The public ``tests.support.adr_contract`` module owns the test-facing API.
These operations parse text and validate the manifest and JSON contract without
filesystem access; callers supply the document text.

Examples
--------
``section_body("## Status\n\nAccepted", "## Status")`` returns ``"\nAccepted"``.
"""

from __future__ import annotations

import json
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
    r"(?<!`)(`+)(?!`)[\s\S]*?(?<!`)\1(?!`)|<!--[\s\S]*?(?:-->|$)"
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
_RANGE_PATTERN: typ.Final[re.Pattern[str]] = re.compile(
    r">=(\d+)\.(\d+)\.(\d+),<(\d+)\.(\d+)\.(\d+)"
)


def _manifest_table(markdown: str) -> dict[str, object]:
    """Validate the fenced table shape; e.g. reject two TOML blocks."""
    blocks = fenced_blocks(section_body(markdown, _MANIFEST_HEADING), "toml")
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
    requirement = _string(value, "wenmode")
    match = _RANGE_PATTERN.fullmatch(requirement)
    if match is None:
        message = "wenmode must use >=MAJOR.MINOR.PATCH,<MAJOR.MINOR.PATCH"
        raise ValueError(message)
    parts = tuple(int(part) for part in match.groups())
    if parts[:3] >= parts[3:]:
        message = "wenmode lower bound must precede its upper bound"
        raise ValueError(message)
    return requirement


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


def _unfenced_lines(
    lines: cabc.Sequence[str],
) -> cabc.Iterator[tuple[int, str, bool]]:
    """Yield lines outside fences and comments; e.g. retain a multiline code span."""
    source = "".join(lines)
    code_spans = [
        (match.start(), match.end())
        for match in _INLINE_LITERAL_PATTERN.finditer(source)
        if match[1]
    ]
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
    offset, line_end = line_bounds
    code_spans, ignored = span_context
    active = _active_code_span_indexes(code_spans, ignored, offset, line_end)
    inside_code = any(code_spans[index][0] < offset for index in active)
    content = line.rstrip("\r\n")
    if state is None and _fence_opening(content):
        state, is_visible = _advance_unfenced_state(state, content)
        ignored.update(active)
        return state, is_visible, inside_code
    if state is None:
        content = _mask_code_spans(line, line_bounds, span_context, active)
    state, is_visible = _advance_unfenced_state(state, content)
    if state is not None:
        ignored.update(active)
    return state, is_visible, inside_code


def _active_code_span_indexes(
    code_spans: list[tuple[int, int]],
    ignored: set[int],
    line_start: int,
    line_end: int,
) -> list[int]:
    """Return active spans intersecting a line; e.g. find a cross-line span."""
    return [
        index
        for index, (start, end) in enumerate(code_spans)
        if index not in ignored and start < line_end and line_start < end
    ]


def _mask_code_spans(
    line: str,
    line_bounds: tuple[int, int],
    span_context: tuple[list[tuple[int, int]], set[int]],
    active: list[int],
) -> str:
    """Mask code-span text before comment parsing, preserving line endings."""
    offset, line_end = line_bounds
    code_spans, _ = span_context
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


def fenced_blocks(markdown: str, language: str) -> list[str]:
    """Extract fence bodies with the requested language.

    Parameters
    ----------
    markdown : str
        Markdown text with backtick or tilde fences.
    language : str
        Exact fence information string to select.

    Returns
    -------
    list of str
        Matching bodies in source order, retaining line endings.

    Examples
    --------
    ``fenced_blocks("ordinary text", "toml")`` returns an empty list.
    """
    return [body for info, body in _fence_bodies(markdown) if info == language]


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


def _render_json(value: object, writer: cabc.Mapping[str, str | int | bool]) -> str:
    """Apply validated settings; e.g. canonical output ends with one LF."""
    # _writer_settings checks exact types before these serialization casts.
    canonical = json.dumps(
        value,
        ensure_ascii=writer["ensure-ascii"] is True,
        indent=typ.cast("int", writer["indent"]),
        separators=(
            typ.cast("str", writer["item-separator"]),
            typ.cast("str", writer["key-separator"]),
        ),
        allow_nan=writer["allow-nan"] is True,
        sort_keys=writer["sort-keys"] is True,
    )
    return canonical + ("\n" if writer["trailing-newline"] is True else "")


def _strict_utf8(text: str) -> None:
    """Reject surrogate text; e.g. strict UTF-8 accepts ordinary Unicode."""
    try:
        text.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        message = "JSON document is not valid strict UTF-8"
        raise ValueError(message) from exc


def _string(value: object, name: str) -> str:
    """Require a string field; e.g. parser construction remains text."""
    if not isinstance(value, str):
        message = f"{name} must be a string"
        raise TypeError(message)
    return value


def _table(value: object, name: str) -> dict[str, object]:
    """Require string-keyed tables; e.g. accept a decoded TOML dictionary."""
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        # The aggregate key check narrows the container's otherwise unknown keys.
        return typ.cast("dict[str, object]", value)
    message = f"{name} must be a TOML table with string keys"
    raise TypeError(message)


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    """Validate string lists; e.g. ["type", "children"] becomes a tuple."""
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        # The aggregate element check establishes the tuple's string element type.
        return tuple(typ.cast("list[str]", value))
    message = f"{name} must be a list of strings"
    raise TypeError(message)


def _fence_opening(line: str) -> tuple[str, str] | None:
    """Find a fence; e.g. `````toml`` returns its marker and language."""
    match = _FENCE_PATTERN.match(line)
    if match is None:
        return None
    return match.group(1), match.group(2).strip()


def _is_fence_closing(line: str, marker: str) -> bool:
    """Match a closer; e.g. four ticks close a three-tick fence."""
    match = _FENCE_CLOSE_PATTERN.match(line)
    if match is None:
        return False
    return len(match.group(1)) >= len(marker) and set(match.group(1)) == {marker[0]}
