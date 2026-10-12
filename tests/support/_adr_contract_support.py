"""Private pure text operations for snapshot-contract ADR test support."""

from __future__ import annotations

import itertools
import json
import re
import tomllib
import typing as typ

if typ.TYPE_CHECKING:
    import collections.abc as cabc

_MANIFEST_HEADING: typ.Final[str] = "### Contract manifest"

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
    try:
        document = _table(tomllib.loads(blocks[0]), "manifest")
        if document.keys() != {"snapshot-contract"}:
            message = "manifest must contain only the [snapshot-contract] table"
            raise ValueError(message)
        contract = _table(document["snapshot-contract"], "[snapshot-contract]")
    except (tomllib.TOMLDecodeError, TypeError) as exc:
        message = "contract manifest contains invalid TOML or table types"
        raise ValueError(message) from exc
    if contract.keys() != _MANIFEST_KEYS:
        message = "[snapshot-contract] keys do not match the schema"
        raise ValueError(message)
    return contract


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
    return {
        key: item for key, item in writer.items() if isinstance(item, (str, int, bool))
    }


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


def _headings(lines: cabc.Sequence[str]) -> cabc.Iterator[tuple[int, str, int]]:
    """Yield headings outside fences; e.g. ignore a fenced ``## Status``."""
    fence: str | None = None
    for index, line in enumerate(lines):
        content = line.rstrip("\r\n")
        if fence is not None:
            if _is_fence_closing(content, fence):
                fence = None
            continue
        opening = _fence_opening(content)
        if opening is not None:
            fence = opening[0]
            continue
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
    lines = markdown.splitlines(keepends=True)
    blocks: list[str] = []
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
        if info == language:
            blocks.append("".join(lines[index + 1 : end]))
        index = end + 1
    return blocks


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
    """Require a TOML table; e.g. ``[snapshot-contract]`` parses as one."""
    if not isinstance(value, dict):
        message = f"{name} must be a TOML table"
        raise TypeError(message)
    table: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            message = f"{name} keys must be strings"
            raise TypeError(message)
        table[key] = item
    return table


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    """Validate string lists; e.g. ``["type", "children"]`` becomes a tuple."""
    if not isinstance(value, list):
        message = f"{name} must be a list of strings"
        raise TypeError(message)
    values: list[str] = []
    for item in value:
        if not isinstance(item, str):
            message = f"{name} must be a list of strings"
            raise TypeError(message)
        values.append(item)
    return tuple(values)


def _fence_opening(line: str) -> tuple[str, str] | None:
    """Find a fence; e.g. `````toml`` returns its marker and language."""
    match = _FENCE_PATTERN.match(line)
    if match is None:
        return None
    return match.group(1), match.group(2).strip()


def _is_fence_closing(line: str, marker: str) -> bool:
    """Match a closer; e.g. four ticks close a three-tick fence."""
    match = re.match(r"^ {0,3}([`~]+)[ \t]*$", line)
    if match is None:
        return False
    return len(match.group(1)) >= len(marker) and set(match.group(1)) == {marker[0]}


def _is_plain_text_node(value: object) -> bool:
    """Identify mergeable nodes; e.g. a text node with only type and value."""
    if not isinstance(value, dict) or value.keys() != {"type", "value"}:
        return False
    return value["type"] == "text" and isinstance(value["value"], str)


def _tree_problems(value: object, key_order: cabc.Sequence[str]) -> list[str]:
    """Check nested JSON; e.g. reversed keys receive a diagnostic."""
    preferred = {key: index for index, key in enumerate(key_order)}
    problems: list[str] = []

    def visit(item: object, path: str) -> None:
        """Visit a nested value; for example use `$.children[0]` for its path."""
        match item:
            case dict() as mapping:
                keys = [key for key in mapping if isinstance(key, str)]
                expected = sorted(
                    keys, key=lambda key: (preferred.get(key, len(preferred)), key)
                )
                if keys != expected:
                    problems.append(f"{path}: mapping keys are not in contract order")
                for key in keys:
                    visit(mapping[key], f"{path}.{key}")
            case list() as sequence:
                if any(
                    _is_plain_text_node(left) and _is_plain_text_node(right)
                    for left, right in itertools.pairwise(sequence)
                ):
                    problems.append(f"{path}: adjacent plain text nodes must be merged")
                for index, child in enumerate(sequence):
                    visit(child, f"{path}[{index}]")

    visit(value, "$")
    return problems
