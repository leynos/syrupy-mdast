"""Test corpus loading, contextual errors, order, and byte-preserving reads.

Run ``uv run pytest -v tests/test_markdown_contract_loading.py``.
"""

import collections.abc as cabc
import dataclasses
import shutil
from pathlib import Path
from unittest import mock

import pytest

from tests.support import markdown_contract
from tests.support.markdown_contract import CaseRecord
from tests.support.markdown_contract_loading import load_corpus

VALID_MINIMAL_MANIFEST = """corpus_version = 1
contract_version = 1
wenmode_evidence_version = "0.15.2"
[[cases]]
id = "first"
rules = ["NF-1"]
reason = "First source."
witness = "text"
kind = "markdown"
input = "sources/first.txt"
expected = "expected/first.json"
line_endings = "lf"

[[cases]]
id = "second"
rules = ["NF-1"]
reason = "Second source."
witness = "text"
kind = "markdown"
input = "sources/second.txt"
expected = "expected/second.json"
line_endings = "lf"
[[relations]]
id = "first-relation"
relation = "equal"
cases = ["first", "second"]
"""


def _write_minimal_corpus(root: Path, manifest: str) -> None:
    """Write two harmless source and golden files for loader boundary tests."""
    source_directory, expected_directory = root / "sources", root / "expected"
    source_directory.mkdir(parents=True)
    expected_directory.mkdir(parents=True)
    for case_id in ("first", "second"):
        (source_directory / f"{case_id}.txt").write_bytes(b"text\n")
        (expected_directory / f"{case_id}.json").write_bytes(b'{"type":"root"}\n')
    (root / "manifest.toml").write_text(manifest, encoding="utf-8")


def _assert_source_round_trip(path: Path, reader: cabc.Callable[[Path], str]) -> None:
    """Require the test reader to reproduce the file's exact UTF-8 bytes."""
    actual_bytes = reader(path).encode("utf-8")
    assert actual_bytes == path.read_bytes(), f"source bytes changed for {path}"


def _read_text_with_newline_normalization(path: Path) -> str:
    """Model universal-newline decoding for the committed negative control."""
    return path.read_text(encoding="utf-8")


def _assert_declared_line_endings(case: CaseRecord) -> None:
    """Require the source's actual CR and LF bytes to match its declaration."""
    source_bytes = case.input.read_bytes()
    line_endings = case.line_endings
    message = f"case {case.id!r} does not match line_endings {line_endings!r}"

    match line_endings:
        case "lf":
            assert b"\n" in source_bytes, message
            assert b"\r" not in source_bytes, message
        case "crlf":
            unpaired_bytes = source_bytes.replace(b"\r\n", b"")
            assert b"\r\n" in source_bytes, message
            assert b"\r" not in unpaired_bytes, message
            assert b"\n" not in unpaired_bytes, message
        case "cr":
            assert b"\r" in source_bytes, message
            assert b"\n" not in source_bytes, message
        case "none":
            assert b"\r" not in source_bytes, message
            assert b"\n" not in source_bytes, message
        case _:
            pytest.fail(f"Markdown case {case.id!r} has no line_endings declaration")


@pytest.mark.parametrize("manifest_state", ["missing", "directory", "permission"])
def test_unusable_manifest_rejected(
    tmp_path: Path, manifest_state: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Manifest read failures report the contextual error."""
    match manifest_state:
        case "directory":
            (tmp_path / "manifest.toml").mkdir()
        case "permission":
            read_error = mock.Mock(side_effect=PermissionError)
            monkeypatch.setattr(Path, "read_bytes", read_error)

    with pytest.raises(ValueError, match=r"manifest.toml"):
        load_corpus(tmp_path)


def test_load_corpus_rejects_an_unknown_relation(tmp_path: Path) -> None:
    """Relation metadata accepts only the two normative relation kinds."""
    _write_minimal_corpus(
        tmp_path,
        VALID_MINIMAL_MANIFEST.replace('relation = "equal"', 'relation = "similar"'),
    )

    with pytest.raises(ValueError, match=r"first-relation"):
        load_corpus(tmp_path)


def test_load_corpus_preserves_case_and_relation_order(tmp_path: Path) -> None:
    """Metadata order remains visible in the test-only corpus records."""
    _write_minimal_corpus(tmp_path, VALID_MINIMAL_MANIFEST)
    corpus = load_corpus(tmp_path)

    assert tuple(case.id for case in corpus.cases) == ("first", "second"), (
        "case records must preserve their manifest order"
    )
    assert tuple(relation.id for relation in corpus.relations) == ("first-relation",), (
        "relation records must preserve their manifest order"
    )


def test_corpus_sources_match_declared_line_endings() -> None:
    """Every Markdown file's actual delimiters agree with TOML metadata."""
    corpus = load_corpus(Path(__file__).parent / "fixtures" / "markdown_contract")
    observed_classes: set[str] = set()

    for case in corpus.cases:
        _assert_source_round_trip(case.input, markdown_contract.read_source)
        markdown_contract.assert_source_witness(case)
        if case.kind == "markdown":
            _assert_declared_line_endings(case)
            assert case.line_endings is not None, (
                f"Markdown case {case.id!r} must declare line endings"
            )
            observed_classes.add(case.line_endings)

    assert {"lf", "crlf", "cr"} <= observed_classes, (
        "the corpus must retain LF, CRLF, and CR source witnesses"
    )


@pytest.mark.parametrize(
    ("case_id", "removed", "replacement"),
    [
        ("link-full-reference-before", b"[x][r]", b'[x](/u "t")'),
        ("link-unused-definition", b"\n[unused]: /u\n", b"\n"),
    ],
    ids=["reference-to-direct", "remove-unused-definition"],
)
def test_source_witness_rejects_semantically_weaker_replacements(
    tmp_path: Path, case_id: str, removed: bytes, replacement: bytes
) -> None:
    """Source witnesses catch semantic-preserving simplifications and removals."""
    corpus = load_corpus(Path(__file__).parent / "fixtures" / "markdown_contract")
    case = next(record for record in corpus.cases if record.id == case_id)
    changed_input = tmp_path / "changed-source.txt"
    source_bytes = case.input.read_bytes()
    assert removed in source_bytes, f"case {case_id!r} must contain the mutation target"
    changed_input.write_bytes(source_bytes.replace(removed, replacement, 1))

    with pytest.raises(
        AssertionError, match=r"source no longer contains its declared witness"
    ):
        markdown_contract.assert_source_witness(
            dataclasses.replace(case, input=changed_input)
        )


def test_crlf_source_with_lf_bytes_is_rejected_in_a_copied_corpus(
    tmp_path: Path,
) -> None:
    """A newline-corrupted copy cannot pass unchanged CRLF metadata."""
    original_root = Path(__file__).parent / "fixtures" / "markdown_contract"
    copied_root = tmp_path / "corpus"
    shutil.copytree(original_root, copied_root)
    copied_corpus = load_corpus(copied_root)
    crlf_case = next(
        case for case in copied_corpus.cases if case.id == "line-endings-crlf"
    )
    crlf_case.input.write_bytes(crlf_case.input.read_bytes().replace(b"\r\n", b"\n"))

    with pytest.raises(AssertionError, match=r"line-endings-crlf.*'crlf'"):
        _assert_declared_line_endings(crlf_case)


def test_load_corpus_rejects_malformed_toml(tmp_path: Path) -> None:
    """Malformed manifest syntax is reported with the manifest filename."""
    (tmp_path / "manifest.toml").write_text("[cases = broken", encoding="utf-8")

    with pytest.raises(ValueError, match=r"manifest.toml.*invalid TOML"):
        load_corpus(tmp_path)


def test_load_corpus_rejects_non_utf8_manifest(tmp_path: Path) -> None:
    """Manifest decoding errors gain context before format parsing."""
    (tmp_path / "manifest.toml").write_bytes(b"corpus_version = \xff")

    with pytest.raises(ValueError, match=r"manifest.toml.*UTF-8"):
        load_corpus(tmp_path)


def test_load_corpus_rejects_duplicate_case_ids(tmp_path: Path) -> None:
    """Case identifiers are unique across the ordered manifest."""
    manifest = VALID_MINIMAL_MANIFEST.replace('id = "second"', 'id = "first"')
    _write_minimal_corpus(tmp_path, manifest)

    with pytest.raises(ValueError, match=r"duplicate case id 'first'"):
        load_corpus(tmp_path)


def test_load_corpus_rejects_duplicate_relation_ids(tmp_path: Path) -> None:
    """Relation identifiers are unique across the ordered manifest."""
    relation = """
[[relations]]
id = "first-relation"
relation = "distinct"
cases = ["first", "second"]
"""
    _write_minimal_corpus(tmp_path, VALID_MINIMAL_MANIFEST + relation)

    with pytest.raises(ValueError, match=r"duplicate relation id 'first-relation'"):
        load_corpus(tmp_path)


def test_load_corpus_rejects_dangling_relation_cases(tmp_path: Path) -> None:
    """Every relation case ID must name a loaded case."""
    manifest = VALID_MINIMAL_MANIFEST.replace(
        'cases = ["first", "second"]', 'cases = ["first", "missing"]'
    )
    _write_minimal_corpus(tmp_path, manifest)

    with pytest.raises(ValueError, match=r"first-relation.*unknown cases.*missing"):
        load_corpus(tmp_path)


@pytest.mark.parametrize(
    "invalid_path",
    ["/outside/source.txt", "../outside/source.txt", "C:/outside/source.txt"],
    ids=["posix-absolute", "parent-escape", "windows-absolute"],
)
def test_load_corpus_rejects_absolute_and_escaping_paths(
    tmp_path: Path, invalid_path: str
) -> None:
    """Manifest paths cannot leave the supplied corpus root."""
    manifest = VALID_MINIMAL_MANIFEST.replace("sources/first.txt", invalid_path)
    _write_minimal_corpus(tmp_path, manifest)

    with pytest.raises(ValueError, match=r"case 'first' input path must be relative"):
        load_corpus(tmp_path)


@pytest.mark.parametrize(
    ("path_field", "path_value"),
    [("input", "sources/missing.txt"), ("expected", "expected/missing.json")],
    ids=["missing-source", "missing-golden"],
)
def test_load_corpus_rejects_missing_case_files(
    tmp_path: Path, path_field: str, path_value: str
) -> None:
    """Every declared case input and golden must exist as a regular file."""
    original = (
        f'{path_field} = "sources/first.txt"'
        if path_field == "input"
        else (f'{path_field} = "expected/first.json"')
    )
    manifest = VALID_MINIMAL_MANIFEST.replace(
        original, f'{path_field} = "{path_value}"'
    )
    _write_minimal_corpus(tmp_path, manifest)

    with pytest.raises(ValueError, match=r"case 'first'.*file does not exist"):
        load_corpus(tmp_path)


def test_load_corpus_rejects_empty_relation_groups(tmp_path: Path) -> None:
    """Relations need at least two cases to state a meaningful comparison."""
    manifest = VALID_MINIMAL_MANIFEST.replace(
        'cases = ["first", "second"]', 'cases = ["first"]'
    )
    _write_minimal_corpus(tmp_path, manifest)

    with pytest.raises(ValueError, match=r"first-relation.*at least two"):
        load_corpus(tmp_path)


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ('kind = "markdown"', 'kind = "parser"', "first.*unknown kind"),
        ('rules = ["NF-1"]', 'rules = ["NF-99"]', "first.*unknown rule ids"),
        (
            'line_endings = "lf"',
            'line_endings = "mixed"',
            "first.*unknown line_endings",
        ),
        ('rules = ["NF-1"]', "rules = []", "first.*rules must not be empty"),
        (
            'witness = "text"',
            'witness = ""',
            r"first.*witness must be a non-empty string",
        ),
        ("corpus_version = 1", "corpus_version = 2", r"corpus_version must be 1"),
        ("contract_version = 1", "contract_version = 2", r"contract_version must be 1"),
        (
            'wenmode_evidence_version = "0.15.2"',
            'wenmode_evidence_version = "0.15.3"',
            r"wenmode_evidence_version",
        ),
    ],
)
def test_load_corpus_rejects_invalid_manifest_metadata(
    tmp_path: Path, old: str, new: str, message: str
) -> None:
    """Manifest and case records reject unsupported declarations."""
    _write_minimal_corpus(tmp_path, VALID_MINIMAL_MANIFEST.replace(old, new, 1))

    with pytest.raises(ValueError, match=message):
        load_corpus(tmp_path)


@pytest.mark.parametrize(
    ("manifest", "message"),
    [
        (
            VALID_MINIMAL_MANIFEST.split("[[cases]]", maxsplit=1)[0]
            + 'cases = "invalid"\n',
            r"manifest.toml: cases must be an array",
        ),
        (
            VALID_MINIMAL_MANIFEST.replace('rules = ["NF-1"]', "rules = 1", 1),
            r"case 'first' rules must be an array of strings",
        ),
        (
            VALID_MINIMAL_MANIFEST.replace('cases = ["first", "second"]', "cases = 1"),
            r"relation 'first-relation' cases must be an array of strings",
        ),
        (
            VALID_MINIMAL_MANIFEST.replace('witness = "text"', "witness = 1", 1),
            r"case 'first' witness must be a string",
        ),
        (
            VALID_MINIMAL_MANIFEST.partition("[[cases]]")[0] + "cases = [1]\n",
            r"case at index 0 must be a TOML table",
        ),
    ],
    ids=["records", "rules", "relation-cases", "case-witness", "case-table"],
)
def test_manifest_type_errors(tmp_path: Path, manifest: str, message: str) -> None:
    """Manifest fields reject values with the wrong type."""
    _write_minimal_corpus(tmp_path, manifest)

    with pytest.raises(TypeError, match=message):
        load_corpus(tmp_path)


def test_load_corpus_rejects_line_endings_on_synthetic_cases(tmp_path: Path) -> None:
    """Synthetic JSON records have no source newline classification."""
    manifest = VALID_MINIMAL_MANIFEST.replace(
        'kind = "markdown"', 'kind = "synthetic"', 1
    )
    _write_minimal_corpus(tmp_path, manifest)

    with pytest.raises(ValueError, match=r"synthetic case 'first'.*omit line_endings"):
        load_corpus(tmp_path)


def test_read_source_rejects_invalid_utf8_without_translation(tmp_path: Path) -> None:
    """Source decoding preserves the standard strict UTF-8 error type."""
    source_path = tmp_path / "invalid.txt"
    source_path.write_bytes(b"invalid: \xff")

    with pytest.raises(UnicodeDecodeError):
        markdown_contract.read_source(source_path)


@pytest.mark.parametrize(
    "source_bytes",
    [b"first\r\nsecond\r", b"first\rsecond\r"],
    ids=["crlf", "cr"],
)
def test_newline_normalizing_reader_is_detected(
    tmp_path: Path, source_bytes: bytes
) -> None:
    """The source-byte assertion rejects a universal-newline reader."""
    source_path = tmp_path / "source.txt"
    source_path.write_bytes(source_bytes)
    with pytest.raises(AssertionError, match=r"source bytes changed"):
        _assert_source_round_trip(source_path, _read_text_with_newline_normalization)
