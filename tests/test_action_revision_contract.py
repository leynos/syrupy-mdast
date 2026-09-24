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
import re

from tests.support.make_contract import REPO_ROOT, mapping, workflow_paths

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
    pinned = []
    for workflow_path in workflow_paths():
        text = (REPO_ROOT / workflow_path).read_text(encoding="utf-8")
        for action, revision in re.findall(r"uses:\s*(\S+?)@(\S+)", text):
            pinned.append((action, revision))
    return pinned


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
            assert dependency not in retired, (
                f"{action}@{revision} reaches {dependency}, which is retired"
            )
