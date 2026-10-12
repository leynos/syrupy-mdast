r"""Private pure text operations for snapshot-contract ADR test support.

The public ``tests.support.adr_contract`` module owns the test-facing API.
These operations parse text and validate the manifest and JSON contract without
filesystem access; callers supply the document text.

Examples
--------
``section_body("## Status\n\nAccepted", "## Status")`` returns ``"\nAccepted"``.
"""

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
    match = re.match(r"^ {0,3}([`~]+)[ \t]*$", line)
    if match is None:
        return False
    return len(match.group(1)) >= len(marker) and set(match.group(1)) == {marker[0]}


def _is_plain_text_node(value: object) -> bool:
    """Identify mergeable nodes; e.g. a text node with only type and value."""
    match value:
        case {"type": "text", "value": str(), **extra_fields} if not extra_fields:
            return True
        case _:
            return False


def _tree_problems(value: object, key_order: cabc.Sequence[str]) -> list[str]:
    """Check nested JSON; e.g. reversed keys receive a diagnostic."""
    preferred = {key: index for index, key in enumerate(key_order)}
    problems: list[str] = []

    def visit(item: object, path: str) -> None:
        """Visit a nested value; for example use `$.children[0]` for its path."""
        match item:
            case dict() as mapping:
                # json.loads guarantees string keys before this private walk.
                keys = list(typ.cast("dict[str, object]", mapping))
                problems.extend(_member_order_problems(keys, preferred, path))
                for key in keys:
                    visit(mapping[key], f"{path}.{key}")
            case list() as sequence:
                plain_nodes = map(_is_plain_text_node, sequence)
                if any(all(pair) for pair in itertools.pairwise(plain_nodes)):
                    problems.append(f"{path}: adjacent plain text nodes must be merged")
                for index, child in enumerate(sequence):
                    visit(child, f"{path}[{index}]")
            case float():
                problems.append(f"{path}: float is outside the contract value domain")

    visit(value, "$")
    return problems


def _member_order_problems(
    keys: cabc.Sequence[str], preferred: cabc.Mapping[str, int], path: str
) -> list[str]:
    """Check one mapping's order; e.g. unknown keys follow known keys."""
    expected = sorted(keys, key=lambda key: (preferred.get(key, len(preferred)), key))
    if list(keys) != expected:
        return [f"{path}: mapping keys are not in contract order"]
    return []


def _key_frame_problems(key_order: cabc.Sequence[str]) -> list[str]:
    """Check the outer members; e.g. type first and children last."""
    problems: list[str] = []
    if not key_order or key_order[0] != "type":
        problems.append("key-order must start with 'type'")
    if not key_order or key_order[-1] != "children":
        problems.append("key-order must end with 'children'")
    return problems


def _key_dependency_problems(key_order: cabc.Sequence[str]) -> list[str]:
    """Check required member dependencies; e.g. data follows value."""
    missing = {"value", "data", "children"} - set(key_order)
    if missing:
        return [f"key-order is missing required members: {sorted(missing)!r}"]
    if (
        not key_order.index("value")
        < key_order.index("data")
        < key_order.index("children")
    ):
        return ["key-order must place value before data before children"]
    return []
