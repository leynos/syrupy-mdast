"""Parse and validate the authored Markdown contract corpus manifest.

The loader turns ``manifest.toml`` into ordered ``CaseRecord`` and
``RelationRecord`` tuples. It never parses Markdown or computes expected
payloads. Errors in metadata, paths, or relations identify their record.

For example, ``load_corpus(Path("tests/fixtures/markdown_contract"))``
returns a ``ContractCorpus`` whose ``cases`` follow manifest order.
"""

import collections.abc as cabc
import tomllib
from pathlib import Path, PurePosixPath, PureWindowsPath

from tests.support.markdown_contract import (
    RULE_IDS,
    CaseKind,
    CaseRecord,
    ContractCorpus,
    LineEndings,
    RelationRecord,
)

MIN_RELATION_CASES = 2


def _table(value: object, location: str) -> dict[str, object]:
    """Return a string-keyed table; ``_table({"id": "case"}, "case")`` copies it.

    Returns
    -------
    dict[str, object]

    Raises
    ------
    TypeError
    """
    if not isinstance(value, cabc.Mapping) or any(
        not isinstance(key, str) for key in value
    ):
        message = f"{location} must be a TOML table"
        raise TypeError(message)
    return dict(value.items())


def _string(value: object, location: str) -> str:
    """Require a non-empty string; ``_string("NF-1", "rules")`` returns that value.

    Returns
    -------
    str

    Raises
    ------
    TypeError
    ValueError
    """
    if not isinstance(value, str):
        message = f"{location} must be a string"
        raise TypeError(message)
    if not value:
        message = f"{location} must be a non-empty string"
        raise ValueError(message)
    return value


def _string_tuple(value: object, location: str) -> tuple[str, ...]:
    """Return a tuple of strings; ``_string_tuple(["NF-1"], "rules")`` preserves order.

    Returns
    -------
    tuple[str, ...]

    Raises
    ------
    TypeError
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
    """Resolve a safe corpus file; a relative ``manifest.toml`` stays under ``root``.

    Returns
    -------
    Path

    Raises
    ------
    ValueError
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


def load_corpus(root: Path) -> ContractCorpus:
    """Load validated records; ``load_corpus(root).cases`` follows manifest order.

    Returns
    -------
    ContractCorpus
    """
    manifest = _read_manifest(root)
    _validate_manifest_header(manifest)
    raw_cases = _manifest_records(manifest.get("cases"), "cases", allow_empty=False)
    cases = _load_cases(raw_cases, root.resolve())
    raw_relations = _manifest_records(
        manifest.get("relations"), "relations", allow_empty=True
    )
    relations = _load_relations(raw_relations, {case.id for case in cases})
    return ContractCorpus(cases=cases, relations=relations)


def _read_manifest(root: Path) -> dict[str, object]:
    """Decode TOML strictly; ``_read_manifest(root)`` returns its top-level table.

    Returns
    -------
    dict[str, object]

    Raises
    ------
    ValueError
    """
    manifest_path = root / "manifest.toml"
    try:
        manifest_text = manifest_path.read_bytes().decode("utf-8")
    except (FileNotFoundError, IsADirectoryError, PermissionError) as error:
        message = f"manifest.toml is not a readable file in corpus root {root}"
        raise ValueError(message) from error
    except UnicodeDecodeError as error:
        message = f"manifest.toml is not valid UTF-8: {error}"
        raise ValueError(message) from error
    try:
        return _table(tomllib.loads(manifest_text), "manifest.toml")
    except tomllib.TOMLDecodeError as error:
        message = f"manifest.toml is invalid TOML: {error}"
        raise ValueError(message) from error


def _validate_manifest_header(manifest: dict[str, object]) -> None:
    """Require supported versions; version ``1`` and evidence ``0.15.2`` pass.

    Raises
    ------
    ValueError
    """
    for field_name in ("corpus_version", "contract_version"):
        field_value = manifest.get(field_name)
        if type(field_value) is not int or field_value != 1:
            message = f"manifest.toml: {field_name} must be 1"
            raise ValueError(message)
    if manifest.get("wenmode_evidence_version") != "0.15.2":
        message = "manifest.toml: wenmode_evidence_version must be '0.15.2'"
        raise ValueError(message)


def _manifest_records(
    value: object, field_name: str, *, allow_empty: bool
) -> list[object]:
    """Return array items; an empty relations array is allowed.

    Returns
    -------
    list[object]

    Raises
    ------
    TypeError
    ValueError
    """
    if not isinstance(value, list):
        message = f"manifest.toml: {field_name} must be an array"
        raise TypeError(message)
    if not allow_empty and not value:
        message = f"manifest.toml: {field_name} must be a non-empty array"
        raise ValueError(message)
    return value


def _register_unique_identifier(
    identifier: str, seen_identifiers: set[str], record_kind: str
) -> None:
    """Register unique IDs; registering ``"intro"`` adds it to the ID set.

    Raises
    ------
    ValueError
    """
    if identifier in seen_identifiers:
        message = f"duplicate {record_kind} id {identifier!r}"
        raise ValueError(message)
    seen_identifiers.add(identifier)


def _load_cases(raw_cases: list[object], root: Path) -> tuple[CaseRecord, ...]:
    """Build records in order; a two-case array stays in its supplied order.

    Returns
    -------
    tuple[CaseRecord, ...]
    """
    cases: list[CaseRecord] = []
    case_ids: set[str] = set()
    for index, raw_case in enumerate(raw_cases):
        location = f"case at index {index}"
        case = _table(raw_case, location)
        case_id = _string(case.get("id"), f"{location} id")
        _register_unique_identifier(case_id, case_ids, "case")
        cases.append(_load_case(case, case_id, root))
    return tuple(cases)


def _load_case(case: dict[str, object], case_id: str, root: Path) -> CaseRecord:
    """Validate fields; ``_load_case(record, "intro", root)`` returns a record.

    Returns
    -------
    CaseRecord

    Raises
    ------
    ValueError
    """
    raw_rules = _string_tuple(case.get("rules"), f"case {case_id!r} rules")
    rules = _validated_case_rules(raw_rules, case_id)
    reason = _string(case.get("reason"), f"case {case_id!r} reason")
    if not reason.strip():
        message = f"case {case_id!r} reason must not be empty"
        raise ValueError(message)
    witness = _string(case.get("witness"), f"case {case_id!r} witness")
    kind, line_endings = _case_kind(case, case_id)
    return CaseRecord(
        id=case_id,
        rules=rules,
        reason=reason,
        witness=witness,
        kind=kind,
        input=_resolve_corpus_file(root, case.get("input"), f"case {case_id!r} input"),
        expected=_resolve_corpus_file(
            root, case.get("expected"), f"case {case_id!r} expected"
        ),
        line_endings=line_endings,
    )


def _validated_case_rules(raw_rules: tuple[str, ...], case_id: str) -> tuple[str, ...]:
    """Require known rules; ``("NF-1",)`` remains unchanged for a valid case.

    Returns
    -------
    tuple[str, ...]

    Raises
    ------
    ValueError
    """
    if not raw_rules:
        message = f"case {case_id!r} rules must not be empty"
        raise ValueError(message)
    unknown_rules = tuple(rule for rule in raw_rules if rule not in RULE_IDS)
    if unknown_rules:
        message = f"case {case_id!r} has unknown rule ids {unknown_rules!r}"
        raise ValueError(message)
    return raw_rules


def _case_kind(
    case: dict[str, object], case_id: str
) -> tuple[CaseKind, LineEndings | None]:
    """Validate case metadata; synthetic cases return ``("synthetic", None)``.

    Returns
    -------
    tuple[CaseKind, LineEndings | None]

    Raises
    ------
    ValueError
    """
    raw_kind = _string(case.get("kind"), f"case {case_id!r} kind")
    if raw_kind not in {"markdown", "synthetic"}:
        message = f"case {case_id!r} has unknown kind {raw_kind!r}"
        raise ValueError(message)
    kind = raw_kind
    if kind == "synthetic":
        if "line_endings" in case:
            message = f"synthetic case {case_id!r} must omit line_endings"
            raise ValueError(message)
        return kind, None
    raw_line_endings = _string(
        case.get("line_endings"), f"case {case_id!r} line_endings"
    )
    if raw_line_endings not in {"lf", "crlf", "cr", "none"}:
        message = f"case {case_id!r} has unknown line_endings {raw_line_endings!r}"
        raise ValueError(message)
    return kind, raw_line_endings


def _load_relations(
    raw_relations: list[object], case_ids: set[str]
) -> tuple[RelationRecord, ...]:
    """Build relation records in order; a two-relation array retains that order.

    Returns
    -------
    tuple[RelationRecord, ...]
    """
    relations: list[RelationRecord] = []
    relation_ids: set[str] = set()
    for index, raw_relation in enumerate(raw_relations):
        location = f"relation at index {index}"
        relation = _table(raw_relation, location)
        relation_id = _string(relation.get("id"), f"{location} id")
        _register_unique_identifier(relation_id, relation_ids, "relation")
        relations.append(_load_relation(relation, relation_id, case_ids))
    return tuple(relations)


def _load_relation(
    relation: dict[str, object], relation_id: str, case_ids: set[str]
) -> RelationRecord:
    """Validate relation fields; equality keeps supplied case IDs in order.

    Returns
    -------
    RelationRecord

    Raises
    ------
    ValueError
    """
    raw_kind = _string(relation.get("relation"), f"relation {relation_id!r} kind")
    if raw_kind not in {"equal", "distinct"}:
        message = f"relation {relation_id!r} has unknown kind {raw_kind!r}"
        raise ValueError(message)
    related_cases = _string_tuple(
        relation.get("cases"), f"relation {relation_id!r} cases"
    )
    _validate_relation_cases(related_cases, relation_id, case_ids)
    return RelationRecord(
        id=relation_id,
        relation=raw_kind,
        cases=related_cases,
    )


def _validate_relation_cases(
    related_cases: tuple[str, ...], relation_id: str, case_ids: set[str]
) -> None:
    """Require distinct known cases; two known IDs pass in supplied order.

    Raises
    ------
    ValueError
    """
    if len(related_cases) < MIN_RELATION_CASES:
        message = f"relation {relation_id!r} must name at least two cases"
        raise ValueError(message)
    if len(set(related_cases)) != len(related_cases):
        message = f"relation {relation_id!r} repeats a case id"
        raise ValueError(message)
    dangling_cases = tuple(
        case_id for case_id in related_cases if case_id not in case_ids
    )
    if dangling_cases:
        message = f"relation {relation_id!r} names unknown cases {dangling_cases!r}"
        raise ValueError(message)
