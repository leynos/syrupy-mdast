"""Guard the accepted ADRs and normative documents with named negative examples."""

from __future__ import annotations

import pathlib
import posixpath
import re
import tomllib
import typing as typ

import pytest

from syrupy_mdast import MarkdownAstSnapshotExtension
from tests.support import adr_contract as contract
from tests.support.make_contract import REPO_ROOT

_DESIGN: typ.Final[str] = "docs/syrupy-mdast-design.md"
_NORMALIZATION_ADR: typ.Final[str] = "docs/adr-004-parser-profile-and-normalization.md"
_NORMATIVE_DOCUMENTS: typ.Final[tuple[str, ...]] = (
    _DESIGN,
    "docs/roadmap.md",
    "docs/users-guide.md",
    "docs/developers-guide.md",
)
_VERSIONING_REQUIREMENT: typ.Final[str] = ">=0.15.2,<0.16.0"
_ACCEPTANCE_SOURCE: typ.Final[str] = (
    "https://github.com/leynos/syrupy-mdast/pull/58#issuecomment-6113067258"
)
_RULE_IDENTIFIERS: typ.Final[frozenset[str]] = frozenset([
    "remove-position",
    "remove-empty-data",
    "merge-plain-text",
    "normalize-line-endings",
    "order-members",
])
_LINK_PATTERN: typ.Final[re.Pattern[str]] = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _read_repo_text(relative_path: str) -> str:
    """Read a UTF-8 document under REPO_ROOT; e.g. read ``docs/contents.md``."""
    path = REPO_ROOT / relative_path
    assert path.is_file(), f"{relative_path}: expected a repository document"
    return path.read_text(encoding="utf-8")


_EXAMPLES: typ.Final[dict[str, dict[str, object]]] = typ.cast(
    "dict[str, dict[str, object]]",
    tomllib.loads(_read_repo_text("tests/support/adr_contract_examples.toml")),
)


def _example(section: str, name: str) -> str:
    """Read one synthetic fixture; e.g. ``_example('manifest', 'body')``."""
    value = _EXAMPLES[section][name]
    assert isinstance(value, str), f"fixture {section}.{name} must be text"
    return value


def _normalization_documents() -> dict[str, str]:
    """Return manifest ADRs by path; ADR-004 appears in the result."""
    return {
        path: text
        for path, text in _adr_documents().items()
        if contract.MANIFEST_HEADING in text
    }


def _adr_documents() -> dict[str, str]:
    """Read ADR texts for link discovery; e.g. include ADR-003 without a manifest."""
    return {
        f"docs/{path.name}": _read_repo_text(f"docs/{path.name}")
        for path in sorted((REPO_ROOT / "docs").glob("adr-*.md"))
    }


def _current_normalization_record() -> tuple[str, str]:
    """Find the accepted manifest ADR; ADR-004 remains a discovery baseline."""
    documents = _normalization_documents()
    accepted = [
        (path, markdown)
        for path, markdown in documents.items()
        if _status_for_path(path, markdown) == "Accepted"
    ]
    assert len(accepted) == 1, f"expected one accepted normalization ADR: {accepted!r}"
    return accepted[0]


def _linked_versioning_record(
    normalization_path: str,
    normalization: str,
    adr_documents: dict[str, str],
) -> tuple[str, str]:
    """Find the accepted policy linked by a normalization ADR's section."""
    names = _link_targets(
        contract.section_body(normalization, "### Versioning policy"),
        normalization_path,
    )
    linked = [
        (path, markdown)
        for path, markdown in adr_documents.items()
        if path in names and _status_for_path(path, markdown) == "Accepted"
    ]
    assert len(linked) == 1, (
        f"{normalization_path}: expected one linked Accepted versioning ADR"
    )
    versioning_path, versioning = linked[0]
    assert normalization_path in _link_targets(
        contract.section_body(versioning, "### Normalization contract"), versioning_path
    ), f"{versioning_path}: link current normalization ADR {normalization_path}"
    return versioning_path, versioning


def _status_for_path(relative_path: str, markdown: str) -> str:
    """Add a document path to status errors; e.g. ``docs/adr-003.md``."""
    try:
        return contract.adr_status(markdown)
    except ValueError as exc:
        message = f"{relative_path}: {exc}"
        raise ValueError(message) from exc


def _link_targets(markdown: str, source_path: str) -> set[str]:
    """Resolve document links; a sibling ADR link yields its full repository path."""
    return {
        posixpath.normpath(
            str(pathlib.PurePosixPath(source_path).parent / target.split("#")[0])
        )
        for _, target in _LINK_PATTERN.findall(markdown)
    }


def test_link_targets_preserves_posix_keys_on_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep Markdown URL paths portable when the native Path uses backslashes."""
    with monkeypatch.context() as patch:
        patch.setattr(pathlib, "Path", pathlib.PureWindowsPath)
        targets = _link_targets(
            "[next](./adr-004-parser-profile-and-normalization.md)", "docs/adr-003.md"
        )
    assert targets == {_NORMALIZATION_ADR}, "Windows links must use repository keys"


def _manifest_block(toml: str, *, heading: str = contract.MANIFEST_HEADING) -> str:
    """Fence TOML for parser tests; e.g. place a table under ``heading``."""
    return f"{heading}\n\n```toml\n{toml}\n```\n"


def test_exactly_one_normalization_contract_adr_is_accepted() -> None:
    """Require one accepted manifest and a gapless normalization version history."""
    documents = _normalization_documents()
    assert documents, "docs/adr-*.md: expected a normalization contract record"
    assert _NORMALIZATION_ADR in documents, "historical ADR-004 baseline is missing"
    records = {
        path: (_status_for_path(path, text), contract.read_manifest(text))
        for path, text in documents.items()
    }
    accepted = [path for path, (status, _) in records.items() if status == "Accepted"]
    assert len(accepted) == 1, f"expected one Accepted ADR: {accepted!r}"

    record_names = set(documents)
    for path, (status, _) in records.items():
        if path in accepted:
            continue
        assert status.startswith("Superseded"), f"{path}: expected Superseded status"
        links = _link_targets(contract.section_body(documents[path], "## Status"), path)
        assert links & record_names, f"{path}: link an existing normalization ADR"

    versions = sorted(manifest.contract_version for _, manifest in records.values())
    assert versions == list(range(1, len(versions) + 1)), (
        f"versions are not gapless: {versions!r}"
    )
    assert records[accepted[0]][1].contract_version == len(versions), (
        f"{accepted[0]}: accepted ADR must hold the latest contract version"
    )


def test_manifest_has_the_contract_schema() -> None:
    """Require typed manifest fields, schema keys, and writer value types."""
    normalization_path, markdown = _current_normalization_record()
    manifest = contract.read_manifest(markdown)
    assert type(manifest.contract_version) is int, normalization_path
    assert manifest.contract_version > 0, (
        f"{normalization_path}: contract-version must be a positive integer"
    )
    assert re.fullmatch(r">=\d+\.\d+\.\d+,<\d+\.\d+\.\d+", manifest.wenmode), (
        f"{normalization_path}: invalid Wenmode range {manifest.wenmode!r}"
    )
    assert manifest.wenmode == _VERSIONING_REQUIREMENT, normalization_path
    assert isinstance(manifest.parser, str), normalization_path
    assert isinstance(manifest.file_extension, str), normalization_path
    assert isinstance(manifest.normalization, tuple), normalization_path
    assert all(rule in _RULE_IDENTIFIERS for rule in manifest.normalization), (
        normalization_path
    )
    assert isinstance(manifest.key_order, tuple), normalization_path
    assert all(isinstance(key, str) for key in manifest.key_order), normalization_path
    reference = tomllib.loads(_example("manifest", "body"))["snapshot-contract"]
    assert {key: type(value) for key, value in manifest.json_writer.items()} == {
        key: type(value) for key, value in reference["json-writer"].items()
    }, f"{normalization_path}: JSON writer keys or value types differ"
    assert manifest.json_writer["ensure-ascii"] is False, normalization_path


def test_manifest_file_extension_matches_the_extension() -> None:
    """Keep the ADR suffix aligned with the public Syrupy extension."""
    manifest = contract.read_manifest(_current_normalization_record()[1])
    assert manifest.file_extension == MarkdownAstSnapshotExtension.file_extension, (
        f"{_NORMALIZATION_ADR}: suffix must match MarkdownAstSnapshotExtension"
    )


def test_key_order_is_framed_and_duplicate_free() -> None:
    """Require framed keys and the dependency order of normalization rules."""
    manifest = contract.read_manifest(_current_normalization_record()[1])
    problems = contract.key_order_problems(manifest.key_order)
    assert not problems, f"normalization key-order: {problems!r}"
    problems = contract.rule_order_problems(manifest.normalization)
    assert not problems, f"normalization rule-order: {problems!r}"


def test_design_parser_construction_matches_manifest() -> None:
    """Require design section 7 to quote the accepted parser construction."""
    manifest = contract.read_manifest(_current_normalization_record()[1])
    design = _read_repo_text(_DESIGN)
    section = contract.section_body(
        design, "## 7. Parser profile and dependency policy"
    )
    blocks = contract.fenced_blocks(section, "python")
    assert blocks, f"{_DESIGN}: section 7 needs a fenced Python parser example"
    assert any(manifest.parser in block for block in blocks), (
        f"{_DESIGN}: section 7 must quote parser value {manifest.parser!r}"
    )


def test_no_normative_document_uses_the_uncalled_preset() -> None:
    """Reject uncalled ``github`` preset construction in the normative allowlist."""
    pattern = re.compile(r"Parser\(\s*github\s*[,)]")
    for relative_path in _NORMATIVE_DOCUMENTS:
        document = _read_repo_text(relative_path)
        assert document.strip(), f"{relative_path}: normative document is empty"
        for line_number, line in enumerate(document.splitlines(), start=1):
            if pattern.search(line):
                pytest.fail(
                    f"{relative_path}:{line_number}: uncalled preset {line.strip()!r}; "
                    "construct Parser(github(), ...)"
                )


def test_contract_adrs_are_indexed_and_cited_by_the_design() -> None:
    """Require both records in the index and their design-section references."""
    normalization_path, normalization = _current_normalization_record()
    adr_documents = _adr_documents()
    versioning_path, _ = _linked_versioning_record(
        normalization_path, normalization, adr_documents
    )
    contents = _read_repo_text("docs/contents.md")
    index_links = _link_targets(
        contract.section_body(contents, "## Decision records"), "docs/contents.md"
    )
    for path in (versioning_path, normalization_path):
        assert path in index_links, f"docs/contents.md: link {path}"

    design = _read_repo_text(_DESIGN)
    citations = (
        ("## 7. Parser profile and dependency policy", {normalization_path}),
        ("## 8. Canonicalization contract", {normalization_path}),
        ("## 11. Correctness and verification", {normalization_path, versioning_path}),
        ("## 13. Compatibility, distribution, and migration", {versioning_path}),
    )
    for heading, paths in citations:
        missing = paths - _link_targets(contract.section_body(design, heading), _DESIGN)
        assert not missing, (
            f"{_DESIGN} {heading}: missing ADR links {sorted(missing)!r}"
        )


def test_design_json_examples_are_writer_fixed_points() -> None:
    """Require design and normative-fixture JSON to follow the writer rules."""
    normalization_path, normalization = _current_normalization_record()
    manifest = contract.read_manifest(normalization)
    design = _read_repo_text(_DESIGN)
    design_examples = contract.fenced_blocks(
        contract.section_body(design, "## 8. Canonicalization contract"), "json"
    )
    assert design_examples, f"{_DESIGN}: section 8 needs a JSON example"
    fixture_section = contract.section_body(
        normalization, "### Normative fixture decisions"
    )
    examples = [(_DESIGN, example) for example in design_examples]
    examples.extend(
        (normalization_path, example)
        for example in contract.fenced_blocks(fixture_section, "json")
    )
    for relative_path, example in examples:
        problems = contract.writer_problems(example, manifest)
        assert not problems, f"{relative_path}: JSON writer problems: {problems!r}"


@pytest.mark.parametrize("case", _example("cases", "policy").split())
def test_version_policy_adr_is_accepted_and_linked(case: str) -> None:
    """Require accepted versioning and reciprocal normalization-record links."""
    normalization_path, normalization = _current_normalization_record()
    adr_documents = _adr_documents()
    versioning_path, versioning = _linked_versioning_record(
        normalization_path, normalization, adr_documents
    )
    if case == "accepted":
        for path, markdown, option in (
            (normalization_path, normalization, "G"),
            (versioning_path, versioning, "A"),
        ):
            note = contract.section_body(markdown, "## Outstanding decisions")
            assert f"selected Option {option}" in note, path
            assert "2026-10-11" in note, path
            assert _ACCEPTANCE_SOURCE in markdown, f"{path}: missing acceptance source"
        return

    adr_documents = adr_documents.copy()
    match case:
        case "proposed-policy":
            adr_documents[versioning_path] = "## Status\n\nProposed\n"
        case "removed-backlink":
            adr_documents[versioning_path] = versioning.replace(
                f"]({pathlib.Path(normalization_path).name})", "]()"
            )
        case "stale-backlink":
            adr_documents[versioning_path] = versioning.replace(
                f"]({pathlib.Path(normalization_path).name})", "](adr-999.md)"
            )
        case _:
            normalization = normalization.replace(
                f"]({pathlib.Path(versioning_path).name})", "](adr-999.md)"
            )
    with pytest.raises(AssertionError):
        _linked_versioning_record(normalization_path, normalization, adr_documents)


@pytest.mark.parametrize("case", _example("cases", "status").split())
def test_adr_status_parses_forms_and_rejects_missing_sections(case: str) -> None:
    """Parse the supported statuses and reject absent or empty sections."""
    markdown, expected = _example("status_examples", case).split("\t")
    if not expected:
        with pytest.raises(ValueError, match="Status"):
            contract.adr_status(markdown)
        return
    assert contract.adr_status(markdown) == expected, case


@pytest.mark.parametrize("closing", ["", "\n```\n"])
def test_read_manifest_returns_a_typed_manifest(closing: str) -> None:
    """Parse a valid TOML fence into tuples and a typed manifest."""
    body = _example("manifest", "body")
    manifest = contract.read_manifest(_manifest_block(body).removesuffix(closing))
    expected = typ.cast("dict[str, object]", tomllib.loads(body))
    reference = typ.cast("dict[str, object]", expected["snapshot-contract"])
    writer = typ.cast("dict[str, str | int | bool]", reference["json-writer"])
    assert manifest == contract.SnapshotContractManifest(
        1,
        _VERSIONING_REQUIREMENT,
        "Parser(github(), positions=False)",
        "mdast.json",
        ("remove-position", "order-members"),
        ("type", "children"),
        writer,
    ), "manifest fields must match the independent example"


@pytest.mark.parametrize("case", _example("cases", "manifest").split())
def test_read_manifest_rejects_invalid_manifest_shapes(case: str) -> None:
    """Reject absent, ambiguous, misplaced, malformed, and mistyped manifests."""
    with pytest.raises(
        ValueError, match=r"manifest|snapshot-contract|heading|contract-version"
    ):
        contract.read_manifest(_example("invalid_manifests", case))


@pytest.mark.parametrize("case", _example("cases", "key_order").split())
def test_key_order_problems_reports_invalid_sequences(case: str) -> None:
    """Report every prohibited key-order shape named by UNIT-3."""
    assert contract.key_order_problems(
        tuple(_example("key_order_examples", case).split())
    ), case


def test_rule_order_problems_reports_merge_after_line_endings() -> None:
    """Require text merging before line-ending normalization."""
    assert contract.rule_order_problems((
        "normalize-line-endings",
        "merge-plain-text",
    )), "merge-after-normalize must be diagnosed"


@pytest.mark.parametrize("case", _example("cases", "writer").split())
def test_writer_problems_reports_noncanonical_json(case: str) -> None:
    """Reject writer or plain-text merge defects while retaining text metadata."""
    manifest = contract.read_manifest(_manifest_block(_example("manifest", "body")))
    problems = contract.writer_problems(_example("writer_examples", case), manifest)
    is_invalid = case not in {"metadata-text", "scalar-values"}
    assert bool(problems) == is_invalid, f"{case}: {problems!r}"
