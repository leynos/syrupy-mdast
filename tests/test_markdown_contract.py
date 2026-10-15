"""Semantic and writer-shape checks for the seed contract corpus."""

import json
import tomllib
from pathlib import Path

import pytest

from tests.support.markdown_contract import (
    CaseRecord,
    ContractCorpus,
    JSONValue,
    RelationRecord,
    load_corpus,
    read_expected_payload,
)

CORPUS_ROOT = Path(__file__).parent / "fixtures" / "markdown_contract"
KEY_ORDER = (
    "type",
    "depth",
    "ordered",
    "start",
    "spread",
    "checked",
    "align",
    "lang",
    "meta",
    "url",
    "title",
    "alt",
    "identifier",
    "label",
    "value",
    "data",
    "children",
)
SEED_RULES = {
    "emphasis-asterisk": ("NF-1",),
    "emphasis-underscore": ("NF-1",),
    "strong-asterisk": ("NF-1",),
    "strong-underscore": ("NF-1",),
    "break-soft": ("NF-10",),
    "break-hard-spaces": ("NF-10",),
    "break-hard-backslash": ("NF-10",),
    "line-endings-lf": ("NF-8", "normalize-line-endings"),
    "line-endings-crlf": ("NF-8", "normalize-line-endings"),
    "line-endings-cr": ("NF-8", "normalize-line-endings"),
}
SEED_SOURCE_BYTES = {
    "emphasis-asterisk": b"*a*\n",
    "emphasis-underscore": b"_a_\n",
    "strong-asterisk": b"**b**\n",
    "strong-underscore": b"__b__\n",
    "break-soft": b"a\nb\n",
    "break-hard-spaces": b"a  \nb\n",
    "break-hard-backslash": b"a\\\nb\n",
    "line-endings-lf": b"first\nsecond\n",
    "line-endings-crlf": b"first\r\nsecond\r\n",
    "line-endings-cr": b"first\rsecond\r",
}
SEED_RELATIONS = {
    "emphasis-delimiters": ("equal", ("emphasis-asterisk", "emphasis-underscore")),
    "strong-delimiters": ("equal", ("strong-asterisk", "strong-underscore")),
    "hard-break-spellings": (
        "equal",
        ("break-hard-spaces", "break-hard-backslash"),
    ),
    "soft-and-hard-breaks": ("distinct", ("break-soft", "break-hard-spaces")),
    "paragraph-line-endings": (
        "equal",
        ("line-endings-lf", "line-endings-crlf", "line-endings-cr"),
    ),
}


@pytest.fixture
def corpus() -> ContractCorpus:
    """Load the small authored corpus used by these seed assertions."""
    return load_corpus(CORPUS_ROOT)


def _case_by_id(corpus: ContractCorpus, case_id: str) -> CaseRecord:
    """Return a named case record from the ordered corpus."""
    return next(case for case in corpus.cases if case.id == case_id)


def _relation_by_id(corpus: ContractCorpus, relation_id: str) -> RelationRecord:
    """Return a named relation record from the ordered corpus."""
    return next(relation for relation in corpus.relations if relation.id == relation_id)


def _mapping(value: JSONValue) -> dict[str, JSONValue]:
    """Narrow one decoded JSON value to an object for its caller."""
    assert isinstance(value, dict), "expected the golden payload member to be an object"
    return value


def _array(value: JSONValue) -> list[JSONValue]:
    """Narrow one decoded JSON value to an array for its caller."""
    assert isinstance(value, list), "expected the golden payload member to be an array"
    return value


def _first_paragraph(corpus: ContractCorpus, case_id: str) -> dict[str, JSONValue]:
    """Return the first paragraph mapping from a named authored golden.

    Returns
    -------
    dict[str, JSONValue]
        The first document child in the named case's expected payload.

    Examples
    --------
    ``_first_paragraph(corpus, "emphasis-asterisk")`` selects its paragraph.
    """
    payload = _mapping(read_expected_payload(_case_by_id(corpus, case_id).expected))
    return _mapping(_array(payload["children"])[0])


def _assert_preferred_member_order(value: JSONValue) -> None:
    """Check ADR-004's preferred keys and code-point ordered remainder."""
    match value:
        case dict():
            keys = list(value)
            preferred = [key for key in KEY_ORDER if key in value]
            remainder = sorted(key for key in keys if key not in KEY_ORDER)
            assert keys == preferred + remainder, (
                "golden object keys must follow the accepted writer order"
            )
            for member_value in value.values():
                _assert_preferred_member_order(member_value)
        case list():
            for item in value:
                _assert_preferred_member_order(item)
        case _:
            return


def test_manifest_pins_the_accepted_corpus_versions() -> None:
    """The corpus records contract v1 and ADR-004's evidence version."""
    manifest = tomllib.loads(
        (CORPUS_ROOT / "manifest.toml").read_bytes().decode("utf-8")
    )

    assert manifest["corpus_version"] == 1, "the corpus format version must be 1"
    assert manifest["contract_version"] == 1, "the Markdown contract version must be 1"
    assert manifest["wenmode_evidence_version"] == "0.15.2", (
        "the Wenmode evidence pin must match ADR-004"
    )


@pytest.mark.parametrize(
    ("case_id", "expected_rules"),
    sorted(SEED_RULES.items()),
    ids=sorted(SEED_RULES),
)
def test_seed_cases_name_their_normative_rule(
    corpus: ContractCorpus, case_id: str, expected_rules: tuple[str, ...]
) -> None:
    """Each seed case is explicitly tied to the rule it demonstrates."""
    assert _case_by_id(corpus, case_id).rules == expected_rules, (
        f"case {case_id!r} must name its normative rule"
    )


@pytest.mark.parametrize(
    ("case_id", "source_bytes"),
    sorted(SEED_SOURCE_BYTES.items()),
    ids=sorted(SEED_SOURCE_BYTES),
)
def test_seed_sources_preserve_the_named_syntax(
    corpus: ContractCorpus, case_id: str, source_bytes: bytes
) -> None:
    """Each seed source retains its exact Markdown spelling and byte ending."""
    assert _case_by_id(corpus, case_id).input.read_bytes() == source_bytes, (
        f"case {case_id!r} must retain its authored Markdown spelling"
    )


@pytest.mark.parametrize(
    ("relation_id", "expected_relation"),
    sorted(SEED_RELATIONS.items()),
    ids=sorted(SEED_RELATIONS),
)
def test_seed_relations_compare_complete_expected_bytes(
    corpus: ContractCorpus,
    relation_id: str,
    expected_relation: tuple[str, tuple[str, ...]],
) -> None:
    """Equal groups share bytes and distinction pairs retain different bytes."""
    expected_kind, expected_cases = expected_relation
    relation = _relation_by_id(corpus, relation_id)
    assert relation.cases == expected_cases, (
        f"relation {relation_id!r} must name its required case IDs"
    )
    payloads = [
        _case_by_id(corpus, case_id).expected.read_bytes() for case_id in relation.cases
    ]

    assert relation.relation == expected_kind, (
        f"relation {relation_id!r} must have its declared relation kind"
    )
    if expected_kind == "equal":
        assert all(payload == payloads[0] for payload in payloads[1:]), (
            f"equal relation {relation_id!r} must have identical golden bytes"
        )
    else:
        assert len(set(payloads)) == len(payloads), (
            f"distinct relation {relation_id!r} must have different golden bytes"
        )


def test_seed_goldens_pin_emphasis_and_strong_nodes(corpus: ContractCorpus) -> None:
    """Authored trees retain emphasis and strong nodes."""
    emphasis_children = _array(
        _first_paragraph(corpus, "emphasis-asterisk")["children"]
    )
    strong_children = _array(_first_paragraph(corpus, "strong-asterisk")["children"])
    emphasis_node = _mapping(emphasis_children[0])
    strong_node = _mapping(strong_children[0])

    assert emphasis_node["type"] == "emphasis", "asterisk syntax must form emphasis"
    assert strong_node["type"] == "strong", "asterisk syntax must form strong text"
    emphasis_text = _mapping(_array(emphasis_node["children"])[0])
    strong_text = _mapping(_array(strong_node["children"])[0])
    assert emphasis_text["type"] == "text", "emphasis content must be a text node"
    assert strong_text["type"] == "text", "strong content must be a text node"
    assert emphasis_text["value"] == "a", "emphasis text must retain its authored value"
    assert strong_text["value"] == "b", "strong text must retain its authored value"


def test_seed_goldens_pin_soft_and_hard_break_nodes(corpus: ContractCorpus) -> None:
    """Authored trees distinguish soft text breaks from hard break nodes."""
    soft_children = _array(_first_paragraph(corpus, "break-soft")["children"])
    assert len(soft_children) == 1, "a soft break must remain in one text node"
    soft_text = _mapping(soft_children[0])
    assert soft_text["type"] == "text", "a soft break must not create a break node"
    assert soft_text["value"] == "a\nb", "a soft break must retain its LF value"

    hard_children = _array(_first_paragraph(corpus, "break-hard-spaces")["children"])
    assert len(hard_children) == 3, "a hard break must split text around one break node"
    before_break = _mapping(hard_children[0])
    break_node = _mapping(hard_children[1])
    after_break = _mapping(hard_children[2])
    assert before_break["type"] == "text", "hard-break content before the break is text"
    assert before_break["value"] == "a", "hard-break text before the break is retained"
    assert set(break_node) == {"type"}, "a Markdown break node has no extra members"
    assert break_node["type"] == "break", "two trailing spaces must create a break node"
    assert after_break["type"] == "text", "hard-break content after the break is text"
    assert after_break["value"] == "b", "hard-break text after the break is retained"


def _assert_expected_writer_shape(expected_path: Path) -> None:
    """Check one golden's exact bytes, strict values, and preferred key order."""
    payload_bytes = expected_path.read_bytes()
    assert not payload_bytes.startswith(b"\xef\xbb\xbf"), (
        f"{expected_path.name} must not contain a UTF-8 BOM"
    )
    assert payload_bytes.endswith(b"\n"), (
        f"{expected_path.name} must end with exactly one LF"
    )
    assert not payload_bytes.endswith(b"\n\n"), (
        f"{expected_path.name} must not have a blank trailing line"
    )
    payload = read_expected_payload(expected_path)
    expected_bytes = (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            separators=(",", ": "),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    assert expected_bytes == payload_bytes, (
        f"{expected_path.name} must match the accepted JSON writer bytes"
    )
    _assert_preferred_member_order(payload)


def test_seed_expected_files_match_the_accepted_writer_shape(
    corpus: ContractCorpus,
) -> None:
    """Seed goldens use strict UTF-8, ordered keys, and one final LF."""
    expected_paths = sorted({case.expected for case in corpus.cases})
    for expected_path in expected_paths:
        _assert_expected_writer_shape(expected_path)


@pytest.mark.parametrize(
    ("payload_bytes", "error_type", "message"),
    [
        (
            b'{\n "type": "root"\n}\n',
            AssertionError,
            "accepted JSON writer bytes",
        ),
        (
            b'{\n  "type": "root"\n}',
            AssertionError,
            "exactly one LF",
        ),
        (
            b'{\n  "children": [],\n  "type": "root"\n}\n',
            AssertionError,
            "accepted writer order",
        ),
        (
            b'{\r\n  "type": "root"\r\n}\r\n',
            AssertionError,
            "accepted JSON writer bytes",
        ),
        (
            b'{"type":"root","type":"root"}\n',
            ValueError,
            "duplicate JSON object member",
        ),
        (
            b'{"type":"root","children":[{"value":1.5}]}\n',
            TypeError,
            "forbidden floating-point value",
        ),
        (
            b'{"type":"root","children":[{"value":"\\ud800"}]}\n',
            ValueError,
            "invalid Unicode scalar",
        ),
    ],
    ids=[
        "indentation",
        "trailing-newline",
        "key-order",
        "crlf",
        "duplicate-key",
        "float",
        "surrogate",
    ],
)
def test_expected_golden_mutations_are_rejected(
    tmp_path: Path,
    payload_bytes: bytes,
    error_type: type[Exception],
    message: str,
) -> None:
    """Temporary malformed goldens fail for their specific contract violation."""
    mutated_path = tmp_path / "mutated.json"
    mutated_path.write_bytes(payload_bytes)

    with pytest.raises(error_type, match=message):
        _assert_expected_writer_shape(mutated_path)
