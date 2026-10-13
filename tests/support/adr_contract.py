r"""Typed public interfaces for snapshot-contract ADR test support.

Examples
--------
``adr_status('## Status\n\nAccepted')`` returns ``"Accepted"``.
"""

from __future__ import annotations

import dataclasses
import itertools
import json
import re
import typing as typ

from tests.support._adr_contract_support import (
    _MANIFEST_HEADING,
    _NORMALIZATION_RULES,
    _fence_bodies,
    _manifest_table,
    _wenmode_range,
    _writer_settings,
)
from tests.support._adr_contract_support import (
    section_body as section_body,
)

if typ.TYPE_CHECKING:
    import collections.abc as cabc

MANIFEST_HEADING: typ.Final[str] = _MANIFEST_HEADING


def _string(value: object, name: str) -> str:
    """Require a string field; e.g. parser construction remains text."""
    if not isinstance(value, str):
        message = f"{name} must be a string"
        raise TypeError(message)
    return value


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


@dataclasses.dataclass(frozen=True, slots=True)
class SnapshotContractManifest:
    """Typed view of a validated snapshot-contract manifest.

    Attributes
    ----------
    contract_version : int
        Positive payload-contract version.
    wenmode : str
        Bounded parser version requirement.
    parser : str
        Exact parser construction recorded by the ADR.
    file_extension : str
        Syrupy snapshot suffix without its leading dot.
    normalization : tuple of str
        Normalization rule identifiers in application order.
    key_order : tuple of str
        Preferred JSON member order.
    json_writer : Mapping[str, str | int | bool]
        Typed writer settings from the manifest table.

    Examples
    --------
    A parsed v1 record exposes ``manifest.contract_version == 1`` and an
    immutable ``manifest.key_order`` tuple.
    """

    contract_version: int
    wenmode: str
    parser: str
    file_extension: str
    normalization: tuple[str, ...]
    key_order: tuple[str, ...]
    json_writer: cabc.Mapping[str, str | int | bool]


def adr_status(markdown: str) -> str:
    """Return the status token from an ADR's Status section.

    Parameters
    ----------
    markdown : str
        ADR text with one unambiguous Status heading.

    Returns
    -------
    str
        Accepted, Proposed, Deprecated, or the complete Superseded status.

    Raises
    ------
    ValueError
        The section is missing, ambiguous, empty, or unsupported.

    Examples
    --------
    ``adr_status("## Status" + chr(10) * 2 + "Accepted")`` returns
    ``"Accepted"``.
    """
    body = section_body(markdown, "## Status")
    status_line = next((line.strip() for line in body.splitlines() if line.strip()), "")
    if not status_line:
        message = "ADR ## Status section is empty"
        raise ValueError(message)
    if re.match(r"^Superseded(?:\s|$)", status_line):
        return status_line
    for status in ("Accepted", "Proposed", "Deprecated"):
        if re.match(rf"^{status}(?:$|[\s:(.])", status_line):
            return status
    message = f"ADR ## Status section has unsupported value {status_line!r}"
    raise ValueError(message)


def read_manifest(markdown: str) -> SnapshotContractManifest:
    """Parse and validate the unique contract manifest.

    Parameters
    ----------
    markdown : str
        ADR text with a Contract manifest section and one TOML block.

    Returns
    -------
    SnapshotContractManifest
        Typed fields, immutable rule and member sequences, and writer settings.

    Raises
    ------
    ValueError
        The section, TOML, schema, field types, or version bounds are invalid.

    Examples
    --------
    Given the accepted ADR in ``markdown``,
    ``read_manifest(markdown).contract_version`` returns ``1``.
    """
    contract = _manifest_table(markdown)
    try:
        version = contract["contract-version"]
        if type(version) is not int or version < 1:
            message = "contract-version must be a positive integer"
            raise ValueError(message)
        normalization = _string_tuple(contract["normalization"], "normalization")
        if not set(normalization) <= _NORMALIZATION_RULES:
            message = "normalization contains an unknown rule identifier"
            raise ValueError(message)
        return SnapshotContractManifest(
            contract_version=version,
            wenmode=_wenmode_range(contract["wenmode"]),
            parser=_string(contract["parser"], "parser"),
            file_extension=_string(contract["file-extension"], "file-extension"),
            normalization=normalization,
            key_order=_string_tuple(contract["key-order"], "key-order"),
            json_writer=_writer_settings(contract["json-writer"]),
        )
    except TypeError as exc:
        message = f"contract manifest has an invalid field type: {exc}"
        raise ValueError(message) from exc


def key_order_problems(key_order: cabc.Sequence[str]) -> list[str]:
    """Report prohibited key-order shapes.

    Parameters
    ----------
    key_order : Sequence[str]
        Preferred JSON member names.

    Returns
    -------
    list of str
        Diagnostics for duplicates, framing, removed positions, or dependencies.

    Examples
    --------
    ``key_order_problems(["type", "value", "data", "children"])``
    returns an empty list.
    """
    problems: list[str] = []
    if len(set(key_order)) != len(key_order):
        problems.append("key-order contains duplicate members")
    problems.extend(_key_frame_problems(key_order))
    if "position" in key_order:
        problems.append("key-order must omit 'position'")
    problems.extend(_key_dependency_problems(key_order))
    return problems


def rule_order_problems(normalization: cabc.Sequence[str]) -> list[str]:
    """Report duplicate rules and reversed merge dependencies.

    Parameters
    ----------
    normalization : Sequence[str]
        Normalization identifiers in application order.

    Returns
    -------
    list of str
        Ordering diagnostics, or an empty list for an acceptable sequence.

    Examples
    --------
    ``rule_order_problems(["merge-plain-text", "normalize-line-endings"])``
    returns an empty list.
    """
    problems: list[str] = []
    if len(set(normalization)) != len(normalization):
        problems.append("normalization contains duplicate rules")
    if {"merge-plain-text", "normalize-line-endings"} <= set(
        normalization
    ) and normalization.index("merge-plain-text") > normalization.index(
        "normalize-line-endings"
    ):
        problems.append("merge-plain-text must precede normalize-line-endings")
    return problems


def _is_plain_text_node(value: object) -> bool:
    """Identify mergeable nodes; e.g. a text node with only type and value."""
    match value:
        case {"type": "text", "value": str(), **extra_fields} if not extra_fields:
            return True
        case _:
            return False


def _root_shape_problems(value: object) -> list[str]:
    """Require the root envelope; e.g. a scalar is not a Markdown tree."""
    match value:
        case {"type": "root", "children": list()}:
            return []
        case _:
            return ["JSON root must have type 'root' and a children array"]


def _tree_problems(value: object, key_order: cabc.Sequence[str]) -> list[str]:
    """Check nested JSON; e.g. reversed keys receive a diagnostic."""
    preferred = {key: index for index, key in enumerate(key_order)}
    problems = _root_shape_problems(value)

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


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    """Validate string lists; e.g. ["type", "children"] becomes a tuple."""
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        # The aggregate element check establishes the tuple's string element type.
        return tuple(typ.cast("list[str]", value))
    message = f"{name} must be a list of strings"
    raise TypeError(message)


def writer_problems(document: str, manifest: SnapshotContractManifest) -> list[str]:
    r"""Check JSON tree ordering and the writer fixed point.

    Parameters
    ----------
    document : str
        Candidate JSON text, including its trailing newline.
    manifest : SnapshotContractManifest
        Validated member order and writer settings.

    Returns
    -------
    list of str
        Encoding, root-shape, ordering, text-merge, or serialization diagnostics.
        Invalid input is reported through this list.

    Examples
    --------
    With the accepted v1 manifest, ``writer_problems("{}\n", manifest)``
    reports that the document lacks the required root envelope.
    """
    problems: list[str] = []
    writer = manifest.json_writer
    if writer.get("encoding") != "utf-8" or writer.get("byte-order-mark") is not False:
        problems.append("JSON writer must use UTF-8 without a byte-order mark")
    if document.startswith("\ufeff"):
        return [*problems, "JSON document begins with a byte-order mark"]
    try:
        _strict_utf8(document)
        value: object = json.loads(document)
        problems.extend(_tree_problems(value, manifest.key_order))
        canonical = _render_json(value, _writer_settings(dict(writer)))
        _strict_utf8(canonical)
    except (ValueError, TypeError) as exc:
        return [*problems, str(exc)]
    if canonical != document:
        problems.append("JSON document is not a writer fixed point")
    return problems
