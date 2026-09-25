"""Contracts for the shared-actions revisions this repository pins.

A full-SHA pin stops a tag from moving, but a composite action runs its
own `uses:` entries, so the pinned revision can reach a third-party action
that GitHub has since retired. These contracts hold every shared-actions
pin to a checked-in record of what it nests, and refuse a revision whose
record reaches a retired SHA. The record is offline by design; refresh it
when a pin moves.
"""

from __future__ import annotations

import json

import pytest
import yaml

from tests.support.make_contract import (
    REPO_ROOT,
    mapping,
    objects,
    workflow_document,
    workflow_paths,
)

_ACTION_REVISIONS = "tests/support/approved_action_revisions.json"


def _revision_fixture() -> dict[str, object]:
    """Return the approved shared-actions revisions and retired pins.

    The contract tests must not reach the network, so what each pin resolves
    to is recorded in the repository instead of fetched. That record has to be
    refreshed when a pin moves; the fixture itself is reviewed like any other
    change.

    Returns
    -------
    dict[str, object]
        The fixture's ``retired`` and ``approved`` sections.
    """
    return mapping(
        json.loads((REPO_ROOT / _ACTION_REVISIONS).read_text(encoding="utf-8")),
        subject="approved action revisions fixture",
    )


def _workflow_uses() -> list[tuple[str, str]]:
    """Return every ``(key, revision)`` pair a workflow step pins.

    Composite actions pin third-party actions internally, so a workflow can
    reach a retired dependency without naming it. These keys are the ones the
    fixture records dependencies against.

    Returns
    -------
    list[tuple[str, str]]
        Each ``uses:`` value split into its action path and revision.
    """
    references = [
        reference
        for workflow_path in workflow_paths()
        for reference in _uses_of(workflow_document(workflow_path))
    ]
    return [
        (action, revision)
        for action, _, revision in (
            reference.partition("@") for reference in references
        )
        if revision
    ]


def _uses_of(document: dict[str, object]) -> list[str]:
    """Return every job-level and step-level ``uses:`` scalar in a workflow.

    The parsed scalar is read, not the line, so a quoted reference is seen
    without its quotes.

    Parameters
    ----------
    document : dict[str, object]
        A parsed workflow.

    Returns
    -------
    list[str]
        Each ``uses:`` value, as GitHub reads it.
    """
    jobs = mapping(document.get("jobs", {}), subject="workflow jobs")
    holders = [
        holder
        for job in jobs.values()
        if isinstance(job, dict)
        for holder in (job, *objects(job.get("steps", []), subject="job steps"))
    ]
    return [str(holder["uses"]) for holder in holders if "uses" in holder]


def _repository_pin(reference: str) -> str:
    """Return ``owner/repository@revision`` for any action reference."""
    path, _, revision = reference.partition("@")
    return "/".join(path.split("/")[:2]) + "@" + revision


def _is_retired(dependency: str, retired: dict[str, object]) -> bool:
    """Return whether a dependency is a retired pin or a sub-action of one.

    A retired entry naming a whole repository at a revision, such as
    ``actions/cache@<sha>``, also retires the sub-actions that revision
    ships, such as ``actions/cache/restore@<sha>``: they fail in the same
    action preparation. An entry naming one action path retires only that
    path.

    Parameters
    ----------
    dependency : str
        The nested ``uses:`` reference to judge.
    retired : dict[str, object]
        The fixture's retired pins.

    Returns
    -------
    bool
        Whether the dependency is retired.
    """
    whole_repositories = {pin for pin in retired if pin == _repository_pin(pin)}
    return dependency in retired or _repository_pin(dependency) in whole_repositories


def test_the_obsolete_codescene_revision_is_rejected() -> None:
    """The superseded revision must not come back, in any workflow.

    Its nested ``actions/cache`` pin was retired by GitHub, so a workflow that
    reaches it fails during action preparation, before any step runs. That
    failure is invisible to a local test run, which is exactly why it is
    asserted here.
    """
    retired = mapping(_revision_fixture()["retired"], subject="retired pins")
    for workflow_path in workflow_paths():
        text = (REPO_ROOT / workflow_path).read_text(encoding="utf-8")
        for pin, reason in retired.items():
            assert pin not in text, f"{workflow_path} pins a retired action: {reason}"


def test_selected_revisions_carry_no_retired_nested_dependency() -> None:
    """A clean top-level pin does not make a composite safe.

    A composite action runs its own ``uses:`` entries, so the pin a workflow
    names is not the whole dependency set. Each approved revision records the
    dependencies nested inside it, and this rejects any revision whose record
    reaches a SHA the fixture lists as retired.
    """
    fixture = _revision_fixture()
    retired = mapping(fixture["retired"], subject="retired pins")
    approved = mapping(fixture["approved"], subject="approved revisions")

    for action, revision in _workflow_uses():
        if not action.startswith("leynos/shared-actions/"):
            continue
        releases = mapping(
            approved.get(action), subject=f"approved revisions for {action}"
        )
        assert revision in releases, (
            f"{action}@{revision} is not recorded in {_ACTION_REVISIONS}; add it "
            "with the dependencies nested inside it, so the retired-SHA check "
            "below can see them"
        )
        detail = mapping(releases[revision], subject=f"{action}@{revision}")
        nested = mapping(detail["nested_uses"], subject=f"{action}@{revision} uses")
        for dependency in nested:
            assert not _is_retired(dependency, retired), (
                f"{action}@{revision} reaches {dependency}, which is retired"
            )


@pytest.mark.parametrize(
    ("dependency", "expected"),
    [
        ("actions/cache@6849a6489940f00c2f30c0fb92c6274307ccb58a", True),
        ("actions/cache/restore@6849a6489940f00c2f30c0fb92c6274307ccb58a", True),
        ("actions/cache/save@6849a6489940f00c2f30c0fb92c6274307ccb58a", True),
        ("actions/cache/save@55cc8345863c7cc4c66a329aec7e433d2d1c52a9", False),
        (
            (
                "leynos/shared-actions/.github/actions/generate-coverage"
                "@395f8e8630d431abb4a136847f1c14c4ad5a0ccc"
            ),
            False,
        ),
    ],
)
def test_a_retired_revision_retires_its_sub_actions(
    dependency: str, *, expected: bool
) -> None:
    """A sub-action of a retired repository revision fails the same way."""
    retired = mapping(_revision_fixture()["retired"], subject="retired pins")
    assert _is_retired(dependency, retired) == expected, dependency


def test_a_quoted_reference_is_read_without_its_quotes() -> None:
    """A quoted ``uses:`` must not escape the approved-revision check."""
    document = yaml.safe_load(
        "jobs:\n  a:\n    steps:\n"
        '      - uses: "leynos/shared-actions/.github/actions/x@abc"\n'
        "  b:\n    uses: 'leynos/shared-actions/.github/workflows/y.yml@def'\n"
    )
    found = _uses_of(document)
    assert found == [
        "leynos/shared-actions/.github/actions/x@abc",
        "leynos/shared-actions/.github/workflows/y.yml@def",
    ], found
