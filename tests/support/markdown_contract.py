"""Define corpus records and byte-level helpers for integrity tests.

For example, ``read_expected_payload(path)`` decodes an authored expected file
without generating output from a parser or canonicalizer.
"""

import dataclasses
import itertools
import json
import typing as typ
from pathlib import Path

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


def read_source(path: Path) -> str:
    r"""Decode one Markdown source without changing its newline bytes.

    Returns
    -------
    str
        The strictly decoded source with all original newline characters.

    Examples
    --------
    For ``b"first\\r\\nsecond\\r"``, ``read_source`` preserves both newline forms.
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


def _strict_json_equal(actual: JSONValue, expected: JSONValue) -> bool:
    """Compare nested JSON values without treating booleans as integers."""
    match expected:
        case dict() as expected_mapping:
            return (
                isinstance(actual, dict)
                and actual.keys() == expected_mapping.keys()
                and all(
                    _strict_json_equal(actual[key], member)
                    for key, member in expected_mapping.items()
                )
            )
        case list() as expected_items:
            return (
                isinstance(actual, list)
                and len(actual) == len(expected_items)
                and all(
                    itertools.starmap(
                        _strict_json_equal,
                        zip(actual, expected_items, strict=True),
                    )
                )
            )
        case _:
            return type(actual) is type(expected) and actual == expected


def contains_node_mapping(value: JSONValue, marker: dict[str, JSONValue]) -> bool:
    """Find a node containing every member in one semantic marker.

    Returns
    -------
    bool
        Whether a node matches, e.g. ``contains_node_mapping(payload, marker)``.
    """
    return any(
        all(
            key in mapping and _strict_json_equal(mapping[key], member)
            for key, member in marker.items()
        )
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
    Duplicate members raise ``ValueError``; floats raise ``TypeError``.
    """
    payload_text = path.read_bytes().decode("utf-8")
    payload = json.loads(payload_text, object_pairs_hook=_unique_json_object)
    _assert_json_scalars(payload, path.name)
    return typ.cast("JSONValue", payload)
