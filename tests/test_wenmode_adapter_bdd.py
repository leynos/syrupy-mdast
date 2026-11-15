"""Contract scenarios for independent internal Wenmode adapter calls.

These are contract scenarios for the private seam, expressed in BDD form. They
are not behavioural acceptance of the public package: the seam has no public
entrypoint, and public behaviour is covered by `tests/test_public_api_contract.py`.

The first two scenarios use the real parser and are compared with a fresh
direct Wenmode parse. The third uses a recording parser double so a failure can
be raised on demand; that double is test machinery, not a package extension
point, and the real parser cannot be made to fail deterministically.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

import syrupy_mdast._wenmode as wenmode_adapter
from tests.support.wenmode_adapter import (
    DEFINITION_DOCUMENT,
    REDEFINITION_DOCUMENT,
    UNRESOLVED_DOCUMENT,
    FailureStage,
    RecordingAdapter,
    UpstreamSentinelError,
    footnote_texts,
    parse_directly,
    reference_urls,
)

_FEATURE = Path(__file__).parent / "features" / "wenmode_adapter.feature"
scenarios(str(_FEATURE))


@pytest.fixture
def scenario_state() -> dict[str, object]:
    """Hold evidence produced by the current behavioural scenario."""
    return {}


@given("a document defining an ordinary reference and a footnote")
def definitions_document(scenario_state: dict[str, object]) -> None:
    """Select the document that defines both labels."""
    scenario_state["first_source"] = DEFINITION_DOCUMENT
    scenario_state["second_source"] = UNRESOLVED_DOCUMENT


@when("it is parsed before a document using those labels without definitions")
def parse_definitions_then_unresolved(scenario_state: dict[str, object]) -> None:
    """Parse both real documents in order and snapshot the first tree."""
    first = wenmode_adapter.parse_markdown(str(scenario_state["first_source"]))
    scenario_state["first_tree"] = first
    scenario_state["first_snapshot"] = copy.deepcopy(first)
    scenario_state["second_tree"] = wenmode_adapter.parse_markdown(
        str(scenario_state["second_source"])
    )


@then("the second tree equals its independent parse")
def second_tree_matches_direct_parse(scenario_state: dict[str, object]) -> None:
    """Assert the second tree equals a fresh direct parse of its own source."""
    second_source = str(scenario_state["second_source"])
    assert scenario_state["second_tree"] == parse_directly(second_source), (
        "an unresolved document must not reuse earlier definitions"
    )


@then("the first tree remains unchanged")
def first_tree_is_unchanged(scenario_state: dict[str, object]) -> None:
    """Require a later call not to mutate an earlier result."""
    assert scenario_state["first_tree"] == scenario_state["first_snapshot"], (
        "the first tree changed after a later adapter call"
    )


@given("two documents defining the same labels with different contents")
def redefinition_documents(scenario_state: dict[str, object]) -> None:
    """Select two documents that define the same labels differently."""
    scenario_state["first_source"] = DEFINITION_DOCUMENT
    scenario_state["second_source"] = REDEFINITION_DOCUMENT


@when("both documents are parsed sequentially")
def parse_both_documents(scenario_state: dict[str, object]) -> None:
    """Parse both real documents in order."""
    scenario_state["first_tree"] = wenmode_adapter.parse_markdown(
        str(scenario_state["first_source"])
    )
    scenario_state["second_tree"] = wenmode_adapter.parse_markdown(
        str(scenario_state["second_source"])
    )


@then("each tree contains only its own reference and footnote contents")
def each_tree_keeps_its_own_contents(scenario_state: dict[str, object]) -> None:
    """Each definition resolves only within the document that declared it."""
    first_tree = scenario_state["first_tree"]
    second_tree = scenario_state["second_tree"]
    assert isinstance(first_tree, dict), "the first tree must be a mapping"
    assert isinstance(second_tree, dict), "the second tree must be a mapping"
    assert reference_urls(first_tree) == ["https://example.com/first"], (
        "the first tree must keep its own reference destination"
    )
    assert reference_urls(second_tree) == ["https://example.com/second"], (
        "the second tree must resolve the redefined destination"
    )
    assert footnote_texts(first_tree) == ["First footnote text."], (
        "the first tree must keep its own footnote text"
    )
    assert footnote_texts(second_tree) == ["Second footnote text."], (
        "the second tree must carry the redefined footnote text"
    )


@given("a parser double that fails during one parse")
def failing_parser_double(
    monkeypatch: pytest.MonkeyPatch, scenario_state: dict[str, object]
) -> None:
    """Install a recording double that raises during the next parse."""
    recorder = RecordingAdapter()
    recorder.install(monkeypatch)
    failure = UpstreamSentinelError("deliberate parse failure")
    recorder.fail_at(FailureStage.PARSE, failure)
    scenario_state.update(recorder=recorder, failure=failure)


@when("the failure is observed and a second document is parsed")
def observe_failure_then_parse(scenario_state: dict[str, object]) -> None:
    """Record the raised exception, then parse a second document."""
    recorder = scenario_state["recorder"]
    assert isinstance(recorder, RecordingAdapter), (
        "the scenario state must hold the installed recording adapter"
    )
    with pytest.raises(UpstreamSentinelError) as caught:
        wenmode_adapter.parse_markdown("# Broken\n")
    scenario_state["observed"] = caught.value
    recorder.clear_failure()
    scenario_state["second_tree"] = wenmode_adapter.parse_markdown("# Recovered\n")


@then("the original exception is propagated unchanged")
def exception_is_unchanged(scenario_state: dict[str, object]) -> None:
    """Require the same exception object to reach the caller."""
    assert scenario_state["observed"] is scenario_state["failure"], (
        "the adapter must not translate or replace a Wenmode failure"
    )


@then("the second call uses a new parser and succeeds")
def second_call_recovers(scenario_state: dict[str, object]) -> None:
    """Require the recovered call to construct its own parser and return its tree."""
    recorder = scenario_state["recorder"]
    assert isinstance(recorder, RecordingAdapter), (
        "the scenario state must hold the installed recording adapter"
    )
    assert len(recorder.parsers) == 2, "the second call must build a new parser"
    assert recorder.parsers[0] is not recorder.parsers[1], (
        "the recovered call must not reuse the failed call's parser"
    )
    second_parser = recorder.parsers[1]
    assert second_parser.sources == ["# Recovered\n"], (
        "the second parser must receive only the recovered source"
    )
    assert scenario_state["second_tree"] is second_parser.documents[0].ast_result, (
        "the recovered tree must be the object the new parser produced"
    )
