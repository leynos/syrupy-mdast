"""Behavioural scenarios for the public Markdown snapshot extension.

These scenarios drive only the public package: `syrupy_mdast` and a Syrupy
snapshot assertion configured with its registered extension. They record what
a consumer observes today, which is that valid Markdown is refused with the
roadmap task that will implement serialisation. No step reaches into
`syrupy_mdast._wenmode`, so a change to the private parsing seam cannot satisfy
or break them by accident.
"""

from __future__ import annotations

import typing as typ
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

import syrupy_mdast

if typ.TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

_FEATURE = Path(__file__).parent / "features" / "public_extension.feature"
scenarios(str(_FEATURE))

_VALID_DOCUMENT = "# Title\n\nA paragraph.\n"


@pytest.fixture
def scenario_state() -> dict[str, object]:
    """Hold the extension and the observed refusal for one scenario."""
    return {}


def _observe_serialisation(scenario_state: dict[str, object]) -> None:
    """Serialise a valid document and record the extension's response."""
    extension = scenario_state["extension"]
    assert isinstance(extension, syrupy_mdast.MarkdownAstSnapshotExtension), (
        "the scenario must hold the public Markdown AST extension"
    )
    scenario_state["failure"] = None
    try:
        extension.serialize(_VALID_DOCUMENT)
    except NotImplementedError as error:
        scenario_state["failure"] = error


@given("the public Markdown snapshot extension")
def public_extension(scenario_state: dict[str, object]) -> None:
    """Build the extension the package publishes."""
    scenario_state["extension"] = syrupy_mdast.MarkdownAstSnapshotExtension()


@given("a Syrupy snapshot assertion using the public extension")
def registered_assertion(
    snapshot: SnapshotAssertion, scenario_state: dict[str, object]
) -> None:
    """Register the public extension through a real Syrupy assertion."""
    assertion = snapshot.with_defaults(
        extension_class=syrupy_mdast.MarkdownAstSnapshotExtension
    )
    scenario_state["extension"] = assertion.extension


@when("a caller serialises a valid Markdown document directly")
def serialise_directly(scenario_state: dict[str, object]) -> None:
    """Serialise through the extension the consumer constructs itself."""
    _observe_serialisation(scenario_state)


@when("that assertion serialises a valid Markdown document")
def serialise_through_assertion(scenario_state: dict[str, object]) -> None:
    """Serialise through the extension Syrupy registered."""
    _observe_serialisation(scenario_state)


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


@then("the registered extension is the public type")
def registered_extension_is_public(scenario_state: dict[str, object]) -> None:
    """Require Syrupy to have instantiated the published extension type."""
    extension = scenario_state["extension"]
    assert isinstance(extension, syrupy_mdast.MarkdownAstSnapshotExtension), (
        "Syrupy registration must instantiate the Markdown AST extension"
    )
