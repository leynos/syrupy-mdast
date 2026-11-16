"""Behavioural scenarios for the public Markdown snapshot extension.

These scenarios drive only the public package. The direct scenario calls
`MarkdownAstSnapshotExtension.serialize`; the registered scenario compares a
document through a Syrupy `SnapshotAssertion` configured with that extension,
which is the path a consumer's `assert data == snapshot` takes. Neither step
imports `syrupy_mdast._wenmode`, so a change to the private parsing seam cannot
satisfy or break them by accident.

Both scenarios record the same contract: valid Markdown cannot be serialised
until roadmap task 2.3.1 lands. Through the extension the refusal propagates as
`NotImplementedError`. Through a SnapshotAssertion the comparison fails before
serialisation is reached, because Syrupy always passes a `matcher` hook and the
extension rejects unsupported property controls; Syrupy reports that rejection
as the first line of its diff.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when
from syrupy.assertion import SnapshotAssertion

import syrupy_mdast

_FEATURE = Path(__file__).parent / "features" / "public_extension.feature"
scenarios(str(_FEATURE))

_VALID_DOCUMENT = "# Title\n\nA paragraph.\n"


@pytest.fixture
def scenario_state() -> dict[str, object]:
    """Hold the public entry point and what it produced for one scenario."""
    return {}


def _assertion_from(scenario_state: dict[str, object]) -> SnapshotAssertion:
    """Return the registered assertion, checked against Syrupy's own type."""
    assertion = scenario_state["assertion"]
    assert isinstance(assertion, SnapshotAssertion), (
        "the scenario must hold the registered Syrupy assertion"
    )
    return assertion


@given("the public Markdown snapshot extension")
def public_extension(scenario_state: dict[str, object]) -> None:
    """Build the extension the package publishes."""
    scenario_state["extension"] = syrupy_mdast.MarkdownAstSnapshotExtension()


@given("a Syrupy snapshot assertion using the public extension")
def registered_assertion(
    snapshot: SnapshotAssertion, scenario_state: dict[str, object]
) -> None:
    """Register the public extension through a real Syrupy assertion."""
    scenario_state["assertion"] = snapshot.with_defaults(
        extension_class=syrupy_mdast.MarkdownAstSnapshotExtension
    )


@when("a caller serialises a valid Markdown document directly")
def serialise_directly(scenario_state: dict[str, object]) -> None:
    """Call the extension method a consumer would call."""
    extension = scenario_state["extension"]
    assert isinstance(extension, syrupy_mdast.MarkdownAstSnapshotExtension), (
        "the scenario must hold the public Markdown AST extension"
    )
    scenario_state["failure"] = None
    try:
        extension.serialize(_VALID_DOCUMENT)
    except NotImplementedError as error:
        scenario_state["failure"] = error


@when("that assertion compares a valid Markdown document")
def compare_through_assertion(scenario_state: dict[str, object]) -> None:
    """Run the comparison behind a consumer's `assert data == snapshot`."""
    assertion = _assertion_from(scenario_state)
    scenario_state["matched"] = assertion == _VALID_DOCUMENT


@then("the extension refuses with the planned roadmap task")
def refusal_names_roadmap_task(scenario_state: dict[str, object]) -> None:
    """Require the documented refusal rather than a silent acceptance."""
    failure = scenario_state["failure"]
    assert isinstance(failure, NotImplementedError), (
        "valid Markdown must reach the planned serializer, not be accepted"
    )
    assert "2.3.1" in str(failure), (
        "the refusal must name the roadmap task that will serialise it"
    )


@then("the comparison does not match")
def comparison_does_not_match(scenario_state: dict[str, object]) -> None:
    """Require the registered assertion not to report a matching snapshot."""
    assert scenario_state["matched"] is False, (
        "valid Markdown must not match a snapshot before roadmap 2.3.1"
    )


@then("Syrupy reports the rejected property control")
def syrupy_reports_control_rejection(scenario_state: dict[str, object]) -> None:
    """Require Syrupy's recorded diff to name the unsupported control."""
    assertion = _assertion_from(scenario_state)
    diff = assertion.get_assert_diff()
    assert diff, "a failed comparison must record a diff"
    assert diff[0].startswith("ValueError"), (
        f"the recorded failure must be the control rejection, got: {diff[0]}"
    )
    assert "matcher" in diff[0], (
        "the recorded rejection must name the unsupported matcher control"
    )


@then("the registered extension is the public type")
def registered_extension_is_public(scenario_state: dict[str, object]) -> None:
    """Require Syrupy to have instantiated the published extension type."""
    assertion = _assertion_from(scenario_state)
    assert isinstance(assertion.extension, syrupy_mdast.MarkdownAstSnapshotExtension), (
        "Syrupy registration must instantiate the Markdown AST extension"
    )
