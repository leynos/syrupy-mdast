"""Semantic and writer-shape checks for the seed contract corpus."""

import dataclasses
import json
import shutil
from pathlib import Path

import pytest

from tests.support.markdown_contract import (
    CaseRecord,
    ContractCorpus,
    JSONValue,
    all_mappings,
    assert_preferred_member_order,
    contains_node_mapping,
    json_array,
    json_mapping,
    load_corpus,
    node_mappings,
    read_expected_payload,
)

CORPUS_ROOT = Path(__file__).parent / "fixtures" / "markdown_contract"
CONTRACT_ASSERTIONS = json.loads(
    (CORPUS_ROOT / "assertions" / "contract-assertions.json")
    .read_bytes()
    .decode("utf-8")
)
NODE_TYPES = frozenset(CONTRACT_ASSERTIONS["node_types"])
REQUIRED_CASE_RULES = CONTRACT_ASSERTIONS["case_rules"]
REQUIRED_RELATIONS = CONTRACT_ASSERTIONS["relations"]
SEMANTIC_MARKERS = CONTRACT_ASSERTIONS["semantic_markers"]


@pytest.fixture
def corpus() -> ContractCorpus:
    """Load the authored corpus used by the contract assertions."""
    return load_corpus(CORPUS_ROOT)


def _case_by_id(corpus: ContractCorpus, case_id: str) -> CaseRecord:
    """Return a named case record from the ordered corpus."""
    return next(case for case in corpus.cases if case.id == case_id)


def test_required_case_inventory_rejects_missing_case_in_copied_corpus(
    tmp_path: Path, corpus: ContractCorpus
) -> None:
    """The exact map passes, then fails when one non-relational case is deleted."""
    actual_rules = {case.id: list(case.rules) for case in corpus.cases}
    assert actual_rules == REQUIRED_CASE_RULES, (
        "the corpus must contain the approved case IDs and rule assignments"
    )

    missing_id = "html-type1-script"
    copied_root = tmp_path / "corpus"
    shutil.copytree(CORPUS_ROOT, copied_root)
    manifest_path = copied_root / "manifest.toml"
    header, *records = manifest_path.read_text(encoding="utf-8").split("[[cases]]")
    kept = [
        "[[cases]]" + record
        for record in records
        if f'id = "{missing_id}"' not in record
    ]
    manifest_path.write_text(header + "".join(kept), encoding="utf-8")
    changed = load_corpus(copied_root)

    with pytest.raises(AssertionError, match="missing required case"):
        assert {
            case.id: list(case.rules) for case in changed.cases
        } == REQUIRED_CASE_RULES, f"missing required case {missing_id!r}"


def _assert_relation_contract(corpus: ContractCorpus, relation_id: str) -> None:
    """Check the exact relation members and complete expected payload bytes."""
    relation = next(item for item in corpus.relations if item.id == relation_id)
    assert {
        "relation": relation.relation,
        "cases": list(relation.cases),
    } == REQUIRED_RELATIONS[relation_id], f"relation {relation_id!r} changed"
    payloads = [
        _case_by_id(corpus, item).expected.read_bytes() for item in relation.cases
    ]
    is_equal = len(set(payloads)) == 1
    assert is_equal is (relation.relation == "equal"), (
        f"relation {relation_id!r} has the wrong complete golden bytes"
    )


@pytest.mark.parametrize(
    "relation_id",
    sorted(REQUIRED_RELATIONS),
    ids=sorted(REQUIRED_RELATIONS),
)
def test_relations_compare_complete_expected_bytes(
    corpus: ContractCorpus, relation_id: str
) -> None:
    """Equal groups share bytes and distinction pairs retain different bytes."""
    _assert_relation_contract(corpus, relation_id)


def test_distinct_relation_rejects_partner_golden_in_a_temporary_copy(
    tmp_path: Path, corpus: ContractCorpus
) -> None:
    """A copied list golden cannot be replaced with its distinct partner."""
    original = _case_by_id(corpus, "list-unordered")
    partner = _case_by_id(corpus, "list-item-order-swapped")
    copied_expected = tmp_path / original.expected.name
    shutil.copyfile(partner.expected, copied_expected)
    changed_cases = tuple(
        dataclasses.replace(case, expected=copied_expected)
        if case.id == original.id
        else case
        for case in corpus.cases
    )

    with pytest.raises(AssertionError, match="wrong complete golden bytes"):
        _assert_relation_contract(
            dataclasses.replace(corpus, cases=changed_cases), "list-item-order"
        )


@pytest.mark.parametrize(
    ("case_id", "marker"),
    sorted(SEMANTIC_MARKERS.items()),
    ids=sorted(SEMANTIC_MARKERS),
)
def test_named_cases_pin_their_expected_node_fields(
    corpus: ContractCorpus, case_id: str, marker: dict[str, JSONValue]
) -> None:
    """Stable case IDs retain the node members named by their source witness."""
    payload = read_expected_payload(_case_by_id(corpus, case_id).expected)
    assert contains_node_mapping(payload, marker), (
        f"case {case_id!r} lost marker {marker!r}"
    )


def test_goldens_cover_all_node_types(corpus: ContractCorpus) -> None:
    """Focused and supplementary goldens collectively cover every node type."""
    observed = {
        node["type"]
        for case in corpus.cases
        for node in node_mappings(read_expected_payload(case.expected))
    }
    assert observed == NODE_TYPES, "all expected goldens must cover the node set"


@pytest.mark.parametrize(
    ("case_id", "node_type", "member"),
    [
        ("link-title-absent", "link", "title"),
        ("image-title-absent", "image", "title"),
        ("code-indented-omissions", "code", "lang"),
        ("code-indented-omissions", "code", "meta"),
        ("list-unordered", "list", "start"),
        ("list-non-task-item", "listItem", "checked"),
    ],
    ids=[
        "link-title",
        "image-title",
        "code-lang",
        "code-meta",
        "list-start",
        "item-checked",
    ],
)
def test_optional_members_stay_omitted(
    corpus: ContractCorpus, case_id: str, node_type: str, member: str
) -> None:
    """Optional members remain absent when their source has no value."""
    payload = read_expected_payload(_case_by_id(corpus, case_id).expected)
    assert not any(
        node.get("type") == node_type and member in node
        for node in node_mappings(payload)
    ), f"case {case_id!r} must omit {node_type}.{member}"


@pytest.mark.parametrize(
    ("case_id", "expected_values"),
    [("list-unordered", ["a", "b"]), ("list-item-order-swapped", ["b", "a"])],
    ids=["source-order", "swapped-source-order"],
)
def test_list_item_order_is_preserved(
    corpus: ContractCorpus, case_id: str, expected_values: list[str]
) -> None:
    """Canonical list arrays retain the order written in each source."""
    payload = read_expected_payload(_case_by_id(corpus, case_id).expected)
    list_node = next(
        node for node in node_mappings(payload) if node.get("type") == "list"
    )
    values: list[str] = []
    for item in json_array(list_node["children"]):
        list_item = json_mapping(item)
        paragraph = json_mapping(json_array(list_item["children"])[0])
        text_node = json_mapping(json_array(paragraph["children"])[0])
        value = text_node["value"]
        assert isinstance(value, str), (
            f"case {case_id!r} list item text must be a string"
        )
        values.append(value)
    assert values == expected_values, f"case {case_id!r} must preserve item order"


def test_recursive_removal_and_falsy_value_contracts(corpus: ContractCorpus) -> None:
    """Position and empty data are removed while non-empty and falsy values survive."""
    positioned = read_expected_payload(
        _case_by_id(corpus, "position-removal-exposes-text").expected
    )
    assert all("position" not in mapping for mapping in all_mappings(positioned)), (
        "position members must be absent recursively"
    )
    assert contains_node_mapping(
        positioned, {"type": "root", "data": {"keep": False}}
    ), "non-empty data must retain its falsy member"
    exposed = read_expected_payload(
        _case_by_id(corpus, "data-removal-exposes-text").expected
    )
    text_nodes = [node for node in node_mappings(exposed) if node.get("type") == "text"]
    assert [node.get("value") for node in text_nodes] == ["abc", "d", "e", "f", "g"], (
        "empty data removal must expose adjacent text before merging"
    )
    assert "data" not in text_nodes[0], "empty mapping data must be removed"
    assert text_nodes[1]["data"] == {"keep": False}, "non-empty data must be retained"
    assert text_nodes[2]["data"] == [], "empty arrays in data must be preserved"
    assert text_nodes[3]["data"] is None, "null data must be preserved"
    assert text_nodes[4]["data"] is False, "false data must be preserved"
    preserved = json_mapping(
        read_expected_payload(_case_by_id(corpus, "preserve-falsy-values").expected)
    )
    data = json_mapping(
        next(
            mapping["data"] for mapping in node_mappings(preserved) if "data" in mapping
        )
    )
    assert data["false"] is False, "false must remain a boolean"
    assert type(data["zero"]) is int, "zero must remain an integer"
    assert data["zero"] == 0, "integer zero must be preserved"
    assert isinstance(data["empty_string"], str), "empty string data must remain text"
    assert not data["empty_string"], "empty strings must be preserved"
    assert data["empty_array"] == [], "empty arrays must be preserved"
    assert data["null"] is None, "null members must be preserved"
    assert data["empty"] == {}, "nested empty mappings must be preserved"
    assert json_array(preserved["children"])[-1] is None, "null array slot must remain"
    assert json_array(preserved["unknown"]) == [3, 1, 2], (
        "unknown arrays must retain their order"
    )


def test_retained_position_mutation_is_rejected_in_a_temporary_golden(
    tmp_path: Path, corpus: ContractCorpus
) -> None:
    """The position assertion rejects a copied golden with a retained position."""
    expected = _case_by_id(corpus, "position-removal-exposes-text").expected
    copied_expected = tmp_path / expected.name
    copied_expected.write_bytes(
        expected.read_bytes().replace(
            b'"type": "root"', b'"position": {},\n  "type": "root"', 1
        )
    )
    changed = read_expected_payload(copied_expected)

    with pytest.raises(AssertionError, match="position"):
        assert all("position" not in mapping for mapping in all_mappings(changed)), (
            "position members must be absent recursively"
        )


def test_footnotes_keep_source_order_and_repeated_references(
    corpus: ContractCorpus,
) -> None:
    """Definitions stay in source order and repeated references remain repeated."""
    before = json_mapping(
        read_expected_payload(
            _case_by_id(corpus, "footnote-definition-before").expected
        )
    )
    after = json_mapping(
        read_expected_payload(_case_by_id(corpus, "footnote-definition-after").expected)
    )
    first_before = json_mapping(json_array(before["children"])[0])
    last_after = json_mapping(json_array(after["children"])[-1])
    assert first_before["type"] == "footnoteDefinition", (
        "a definition before text must remain first"
    )
    assert last_after["type"] == "footnoteDefinition", (
        "a definition after text must remain last"
    )
    repeated = read_expected_payload(
        _case_by_id(corpus, "footnote-repeated-reference").expected
    )
    references = [
        node for node in node_mappings(repeated) if node["type"] == "footnoteReference"
    ]
    assert len(references) == 2, "repeated source references must remain repeated"


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
    assert_preferred_member_order(payload)


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
            (
                '{\n  "type": "root",\n  "data": {},\n  "children": [],\n  '
                '"\U00010000supplementary": "supplementary",\n  '
                '"\ue000private": "private"\n}\n'
            ).encode("utf-8"),
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
        "unicode-codepoint-order",
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
