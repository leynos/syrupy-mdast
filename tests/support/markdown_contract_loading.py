"""Manifest parsing for the authored Markdown contract corpus tests."""

import tomllib
from pathlib import Path

from tests.support.markdown_contract import (
    MIN_RELATION_CASES,
    RULE_IDS,
    CaseKind,
    CaseRecord,
    ContractCorpus,
    LineEndings,
    RelationRecord,
    _resolve_corpus_file,
    _string,
    _string_tuple,
    _table,
)


def load_corpus(root: Path) -> ContractCorpus:
    """Load ordered case records and paths from a corpus directory.

    Returns
    -------
    ContractCorpus
        Ordered case and relation metadata with validated file paths.

    Examples
    --------
    A checked-in corpus can be loaded without parsing Markdown or constructing
    expected output::

        corpus = load_corpus(Path("tests/fixtures/markdown_contract"))
        first_case = corpus.cases[0]
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
    """Decode the corpus manifest and report file or syntax errors.

    Returns
    -------
    dict[str, object]
        The decoded top-level TOML table.

    Raises
    ------
    ValueError
        If the file is missing, is a directory, or contains invalid UTF-8/TOML.

    Examples
    --------
    ``_read_manifest(root)`` returns its TOML table after UTF-8 decoding.
    """
    manifest_path = root / "manifest.toml"
    try:
        manifest_text = manifest_path.read_bytes().decode("utf-8")
    except (FileNotFoundError, IsADirectoryError) as error:
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
    """Require the corpus and source-evidence format versions.

    Raises
    ------
    ValueError
        If a declared format version does not match this loader.

    Examples
    --------
    A manifest declaring both version fields as ``1`` passes this check.
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
    """Return a TOML array field, optionally requiring at least one item.

    Returns
    -------
    list[object]
        The original array in its manifest order.

    Raises
    ------
    ValueError
        If an empty array is forbidden.
    TypeError
        If the field is not an array.

    Examples
    --------
    ``_manifest_records([], "relations", allow_empty=True)`` returns ``[]``.
    """
    if not isinstance(value, list):
        message = f"manifest.toml: {field_name} must be an array"
        raise TypeError(message)
    if not allow_empty and not value:
        message = f"manifest.toml: {field_name} must be a non-empty array"
        raise ValueError(message)
    return value


def _load_cases(raw_cases: list[object], root: Path) -> tuple[CaseRecord, ...]:
    """Build ordered case records and reject duplicate identifiers.

    Returns
    -------
    tuple[CaseRecord, ...]
        Validated case records in manifest order.

    Raises
    ------
    ValueError
        If a case is invalid or its identifier is duplicated.

    Examples
    --------
    A two-item manifest array produces two records in the same order.
    """
    cases: list[CaseRecord] = []
    case_ids: set[str] = set()
    for index, raw_case in enumerate(raw_cases):
        location = f"case at index {index}"
        case = _table(raw_case, location)
        case_id = _string(case.get("id"), f"{location} id")
        if case_id in case_ids:
            message = f"duplicate case id {case_id!r}"
            raise ValueError(message)
        case_ids.add(case_id)
        cases.append(_load_case(case, case_id, root))
    return tuple(cases)


def _load_case(case: dict[str, object], case_id: str, root: Path) -> CaseRecord:
    """Validate and resolve one case table.

    Returns
    -------
    CaseRecord
        The validated metadata and resolved paths for this case.

    Raises
    ------
    ValueError
        If a field is missing, invalid, or resolves outside the corpus.

    Examples
    --------
    A valid case table becomes a record with resolved input and expected paths.
    """
    raw_rules = _string_tuple(case.get("rules"), f"case {case_id!r} rules")
    rules = _validated_case_rules(raw_rules, case_id)
    reason = _string(case.get("reason"), f"case {case_id!r} reason")
    if not reason.strip():
        message = f"case {case_id!r} reason must not be empty"
        raise ValueError(message)
    kind, line_endings = _case_kind(case, case_id)
    return CaseRecord(
        id=case_id,
        rules=rules,
        reason=reason,
        kind=kind,
        input=_resolve_corpus_file(root, case.get("input"), f"case {case_id!r} input"),
        expected=_resolve_corpus_file(
            root, case.get("expected"), f"case {case_id!r} expected"
        ),
        line_endings=line_endings,
    )


def _validated_case_rules(raw_rules: tuple[str, ...], case_id: str) -> tuple[str, ...]:
    """Require one or more known normative rule identifiers.

    Returns
    -------
    tuple[str, ...]
        The supplied rule identifiers after validation.

    Raises
    ------
    ValueError
        If no rules are supplied or an identifier is unknown.

    Examples
    --------
    ``_validated_case_rules(("NF-1",), "intro")`` preserves that rule tuple.
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
    """Validate a case kind and its required newline declaration.

    Returns
    -------
    tuple[CaseKind, LineEndings | None]
        The kind and its newline declaration, or ``None`` for synthetic cases.

    Raises
    ------
    ValueError
        If the kind or declared line endings are invalid.

    Examples
    --------
    A synthetic record returns ``("synthetic", None)``.
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
    """Build ordered relation records and reject duplicate identifiers.

    Returns
    -------
    tuple[RelationRecord, ...]
        Validated relation records in manifest order.

    Raises
    ------
    ValueError
        If a relation is invalid or its identifier is duplicated.

    Examples
    --------
    Relation records preserve the order of their manifest array.
    """
    relations: list[RelationRecord] = []
    relation_ids: set[str] = set()
    for index, raw_relation in enumerate(raw_relations):
        location = f"relation at index {index}"
        relation = _table(raw_relation, location)
        relation_id = _string(relation.get("id"), f"{location} id")
        if relation_id in relation_ids:
            message = f"duplicate relation id {relation_id!r}"
            raise ValueError(message)
        relation_ids.add(relation_id)
        relations.append(_load_relation(relation, relation_id, case_ids))
    return tuple(relations)


def _load_relation(
    relation: dict[str, object], relation_id: str, case_ids: set[str]
) -> RelationRecord:
    """Validate relation kind and its ordered case references.

    Returns
    -------
    RelationRecord
        The validated relation and its ordered case IDs.

    Raises
    ------
    ValueError
        If the relation kind or case references are invalid.

    Examples
    --------
    A valid equality relation returns its named case IDs in manifest order.
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
    """Require a relation to name distinct, existing cases.

    Raises
    ------
    ValueError
        If fewer than two unique, known cases are named.

    Examples
    --------
    Two known case IDs pass validation in their supplied order.
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
