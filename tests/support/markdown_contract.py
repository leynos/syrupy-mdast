"""Load and validate corpus fixtures while preserving bytes and record order.

For example, ``load_corpus(Path("tests/fixtures/markdown_contract"))`` returns
the cases and relations for focused integrity assertions.
"""

import collections.abc as cabc
import dataclasses
import json
import typing as typ
from pathlib import Path, PurePosixPath, PureWindowsPath

type CaseKind = typ.Literal["markdown", "synthetic"]
type LineEndings = typ.Literal["lf", "crlf", "cr", "none"]
type RelationKind = typ.Literal["equal", "distinct"]
type JSONValue = str | int | bool | list[JSONValue] | dict[str, JSONValue] | None

RULE_IDS = frozenset(f"NF-{number}" for number in range(1, 14)) | frozenset({
    "remove-position",
    "remove-empty-data",
    "merge-plain-text",
    "normalize-line-endings",
    "order-members",
    "preserve-values",
    "writer-format",
})
MIN_RELATION_CASES = 2
_ASSERTIONS_PATH = (
    Path(__file__).parent.parent
    / "fixtures"
    / "markdown_contract"
    / "assertions"
    / "contract-assertions.json"
)
PREFERRED_MEMBER_ORDER = tuple(
    json.loads(_ASSERTIONS_PATH.read_bytes())["preferred_member_order"]
)


@dataclasses.dataclass(frozen=True, slots=True)
class CaseRecord:
    """One ordered source and its independently authored expected payload."""

    id: str
    rules: tuple[str, ...]
    reason: str
    witness: str
    kind: CaseKind
    input: Path
    expected: Path
    line_endings: LineEndings | None


@dataclasses.dataclass(frozen=True, slots=True)
class RelationRecord:
    """An equality group or a pairwise distinction between named cases."""

    id: str
    relation: RelationKind
    cases: tuple[str, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class ContractCorpus:
    """The ordered case and relation records loaded from one corpus root."""

    cases: tuple[CaseRecord, ...]
    relations: tuple[RelationRecord, ...]


def load_corpus(root: Path) -> ContractCorpus:
    """Load a corpus manifest into ordered, validated records.

    Returns
    -------
    ContractCorpus
        Validated case and relation records with resolved file paths.

    Examples
    --------
    ``load_corpus(root)`` loads the manifest rooted at ``root``.
    """
    from .markdown_contract_loading import load_corpus as load_manifest

    return load_manifest(root)


def read_source(path: Path) -> str:
    r"""Decode one Markdown source without changing its newline bytes.

    Returns
    -------
    str
        The strictly decoded source with all original newline characters.

    Examples
    --------
    For a file containing ``b"first\\r\\nsecond\\r"``, the result keeps both
    the CRLF pair and the final bare CR in the decoded string.
    """
    return path.read_bytes().decode("utf-8")


def assert_source_witness(case: CaseRecord) -> None:
    """Require each declared source witness to occur in the exact input bytes."""
    witness_bytes = case.witness.encode("utf-8")
    assert witness_bytes in case.input.read_bytes(), (
        f"case {case.id!r} source no longer contains its declared witness"
    )


def json_mapping(value: JSONValue) -> dict[str, JSONValue]:
    """Narrow one decoded value to an object in a test assertion.

    Returns
    -------
    dict[str, JSONValue]
        The object mapping; ``json_mapping(payload)["type"]`` reads its root.
    """
    assert isinstance(value, dict), "expected a JSON object"
    return value


def json_array(value: JSONValue) -> list[JSONValue]:
    """Narrow one decoded value to an array in a test assertion.

    Returns
    -------
    list[JSONValue]
        The array; ``json_array(payload["children"])`` reads root children.
    """
    assert isinstance(value, list), "expected a JSON array"
    return value


def node_mappings(value: JSONValue) -> list[dict[str, JSONValue]]:
    """Collect typed node mappings in their authored depth-first order.

    Returns
    -------
    list[dict[str, JSONValue]]
        Typed nodes; ``node_mappings(payload)`` finds them in depth-first order.
    """
    match value:
        case dict() as mapping:
            current = [mapping] if isinstance(mapping.get("type"), str) else []
            return current + [
                nested
                for member in mapping.values()
                for nested in node_mappings(member)
            ]
        case list() as items:
            return [nested for item in items for nested in node_mappings(item)]
        case _:
            return []


def all_mappings(value: JSONValue) -> list[dict[str, JSONValue]]:
    """Collect mappings recursively, including data and unknown fields.

    Returns
    -------
    list[dict[str, JSONValue]]
        All objects; ``all_mappings(payload)`` includes non-node mappings.
    """
    match value:
        case dict() as mapping:
            return [mapping] + [
                nested for member in mapping.values() for nested in all_mappings(member)
            ]
        case list() as items:
            return [nested for item in items for nested in all_mappings(item)]
        case _:
            return []


def contains_node_mapping(value: JSONValue, marker: dict[str, JSONValue]) -> bool:
    """Find a node containing every member in one semantic marker.

    Returns
    -------
    bool
        Whether a node matches, e.g. ``contains_node_mapping(payload, marker)``.
    """
    sentinel = object()
    return any(
        all(mapping.get(key, sentinel) == member for key, member in marker.items())
        for mapping in node_mappings(value)
        if mapping.get("type") == marker.get("type")
    )


def assert_preferred_member_order(value: JSONValue) -> None:
    """Check ADR-004's preferred keys and code-point ordered remainder.

    Examples
    --------
    ``assert_preferred_member_order(payload)`` checks every object recursively.
    """
    match value:
        case dict():
            keys = list(value)
            preferred = [key for key in PREFERRED_MEMBER_ORDER if key in value]
            remainder = sorted(key for key in keys if key not in PREFERRED_MEMBER_ORDER)
            assert keys == preferred + remainder, (
                "golden object keys must follow the accepted writer order"
            )
            for member_value in value.values():
                assert_preferred_member_order(member_value)
        case list():
            for item in value:
                assert_preferred_member_order(item)
        case _:
            return


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject JSON objects that repeat a member instead of hiding duplicates."""
    members: dict[str, object] = {}
    for key, value in pairs:
        if key in members:
            message = f"duplicate JSON object member {key!r}"
            raise ValueError(message)
        members[key] = value
    return members


def _assert_json_scalars(value: object, location: str) -> None:
    """Reject unsupported JSON scalar values recursively."""
    match value:
        case list() as items:
            for index, item in enumerate(items):
                _assert_json_scalars(item, f"{location}[{index}]")
        case dict() as members:
            for key, member in members.items():
                _assert_json_scalars(key, f"{location} object key")
                _assert_json_scalars(member, f"{location}.{key}")
        case _:
            _assert_json_scalar(value, location)


def _assert_json_scalar(value: object, location: str) -> None:
    """Reject floats and invalid Unicode scalar strings."""
    match value:
        case None | bool() | int():
            return
        case float():
            message = f"{location} contains a forbidden floating-point value"
            raise TypeError(message)
        case str() as text:
            try:
                text.encode("utf-8")
            except UnicodeEncodeError as error:
                message = f"{location} contains an invalid Unicode scalar"
                raise ValueError(message) from error
            return
        case _:
            message = f"{location} contains an unsupported JSON value"
            raise TypeError(message)


def read_expected_payload(path: Path) -> JSONValue:
    """Decode one authored golden with strict text and scalar validation.

    Returns
    -------
    JSONValue
        The decoded root tree after duplicate-member and scalar checks.

    Examples
    --------
    A duplicate member raises ``ValueError``; a floating-point value raises
    ``TypeError``.
    """
    payload_text = path.read_bytes().decode("utf-8")
    payload = json.loads(payload_text, object_pairs_hook=_unique_json_object)
    _assert_json_scalars(payload, path.name)
    return typ.cast("JSONValue", payload)


def _table(value: object, location: str) -> dict[str, object]:
    """Return a string-keyed TOML table or identify its location.

    Returns
    -------
    dict[str, object]
        A plain dictionary containing the table's original keys and values.

    Raises
    ------
    ValueError
        If the value is not a string-keyed table.

    Examples
    --------
    ``_table({"id": "case"}, "case")`` returns the same mapping.
    """
    if not isinstance(value, cabc.Mapping) or any(
        not isinstance(key, str) for key in value
    ):
        message = f"{location} must be a TOML table"
        raise ValueError(message)
    return dict(value.items())


def _string(value: object, location: str) -> str:
    """Return a non-empty string field and name it when the type is wrong.

    Returns
    -------
    str
        The validated string value.

    Raises
    ------
    ValueError
        If the value is not a non-empty string.

    Examples
    --------
    ``_string("NF-1", "case rules")`` returns ``"NF-1"``.
    """
    if not isinstance(value, str) or not value:
        message = f"{location} must be a non-empty string"
        raise ValueError(message)
    return value


def _string_tuple(value: object, location: str) -> tuple[str, ...]:
    """Return a TOML string array as an immutable tuple.

    Returns
    -------
    tuple[str, ...]
        The array items in their original order.

    Raises
    ------
    TypeError
        If the value is not a list or contains a non-string item.

    Examples
    --------
    ``_string_tuple(["NF-1"], "case rules")`` returns ``("NF-1",)``.
    """
    if not isinstance(value, list):
        message = f"{location} must be an array of strings"
        raise TypeError(message)
    strings: list[str] = []
    for item in value:
        if not isinstance(item, str):
            message = f"{location} must contain only strings"
            raise TypeError(message)
        strings.append(item)
    return tuple(strings)


def _resolve_corpus_file(root: Path, value: object, location: str) -> Path:
    """Resolve an existing corpus file without permitting path escapes.

    Returns
    -------
    Path
        The absolute path of the validated corpus file.

    Raises
    ------
    ValueError
        If the path is absolute, escapes the root, or does not exist.

    Examples
    --------
    A path such as ``"../outside.txt"`` raises ``ValueError`` instead of
    resolving outside the supplied corpus directory.
    """
    relative_name = _string(value, f"{location} path")
    relative_path = PurePosixPath(relative_name)
    windows_path = PureWindowsPath(relative_name)
    if any((
        relative_path.is_absolute(),
        windows_path.is_absolute(),
        bool(windows_path.drive),
        "\\" in relative_name,
        ".." in relative_path.parts,
        not relative_path.parts,
    )):
        message = f"{location} path must be relative to the corpus root"
        raise ValueError(message)

    resolved_root = root.resolve()
    resolved_path = resolved_root.joinpath(*relative_path.parts).resolve()
    if not resolved_path.is_relative_to(resolved_root):
        message = f"{location} path escapes the corpus root"
        raise ValueError(message)
    if not resolved_path.is_file():
        message = f"{location} file does not exist: {relative_name!r}"
        raise ValueError(message)
    return resolved_path
