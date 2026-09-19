"""Contracts for the default-branch CodeScene coverage upload.

Pull requests used to reach CodeScene through a separate changed-line gate.
That gate is gone. A pull request now enforces coverage locally, through the
ratchet on ``generate-coverage``, and never contacts CodeScene, so the only
CodeScene contact left is the default-branch upload that refreshes the
analysed branch's coverage data.

These contracts read the workflow's structure rather than its text. A step is
identified by what it does to CodeScene, not by the name it is filed under, so
relabelling or relocating a step cannot slip past them.
"""

from __future__ import annotations

import json
import re

from tests.support.make_contract import (
    REPO_ROOT,
    mapping,
    sole_workflow_step,
    workflow_jobs,
    workflow_paths,
    workflow_steps,
)

_CI_WORKFLOW = ".github/workflows/ci.yml"
_CI_JOB = "lint-test"
_CODESCENE_ACTION = "leynos/shared-actions/.github/actions/upload-codescene-coverage"
_PUSH_TO_MAIN = "github.event_name == 'push' && github.ref == 'refs/heads/main'"
_MEASURE_COVERAGE = "Test and Measure Coverage"
_UPLOAD_COVERAGE = "Upload coverage data to CodeScene"
_ACTION_REVISIONS = "tests/support/approved_action_revisions.json"
_SHA = r"[0-9a-f]{40}"


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


def _codescene_steps() -> list[dict[str, object]]:
    """Return every CI step that could invoke the external CodeScene service.

    A step qualifies whether it calls the shared action or shells out to the
    ``cs-coverage`` CLI, and whether it lives in the build job or anywhere else
    in the workflow, so delegating the call under a new name or moving it to a
    new job cannot hide it from the contracts below.

    Returns
    -------
    list[dict[str, object]]
        Each step outside the repository that could reach CodeScene.
    """
    contacts = []
    for job_name in workflow_jobs(_CI_WORKFLOW):
        for step in workflow_steps(_CI_WORKFLOW, job_name):
            invokes_action = _CODESCENE_ACTION in str(step.get("uses", ""))
            invokes_cli = "cs-coverage" in str(step.get("run", ""))
            if invokes_action or invokes_cli:
                contacts.append(step)
    return contacts


def test_codescene_is_contacted_only_from_a_default_branch_push() -> None:
    """One step contacts CodeScene, and a pull request cannot reach it.

    Reachability is the whole point. A pull request executes arbitrary
    head-repository code, so a CodeScene step a pull request could reach would
    either hand the access token to a fork or leave a secret-less fork waiting
    on a check that can never be produced.
    """
    codescene_steps = _codescene_steps()
    assert len(codescene_steps) == 1, (
        "exactly one step may contact CodeScene, found "
        f"{len(codescene_steps)}: {[step.get('name') for step in codescene_steps]}"
    )

    condition = str(codescene_steps[0].get("if", ""))
    assert "pull_request" not in condition, (
        "a pull request must not be able to reach the CodeScene step"
    )
    assert condition.startswith(_PUSH_TO_MAIN), (
        "the CodeScene step must be gated on a default-branch push; any "
        "further terms may only narrow that gate"
    )


def test_default_branch_upload_publishes_the_measured_report() -> None:
    """The baseline is uploaded in upload mode, from the analysed branch."""
    upload = sole_workflow_step(_CI_WORKFLOW, _CI_JOB, _UPLOAD_COVERAGE)
    upload_inputs = mapping(upload["with"], subject="CodeScene upload inputs")
    assert upload_inputs["mode"] == "upload", "main must use upload mode"
    assert upload_inputs["format"] == "cobertura", "main must upload Cobertura data"
    assert upload_inputs["path"] == "coverage.xml", "main must upload coverage.xml"
    assert "archive-checksum" not in upload_inputs, (
        "the action verifies the CLI archive against its own cli-manifest.json "
        "on every run, so a caller-supplied digest would only restate a value "
        "the action already holds"
    )
    assert "installer-checksum" not in upload_inputs, (
        "the pinned action rejects a non-empty installer-checksum, so the "
        "upload must not fall back to the deprecated input"
    )
    assert upload_inputs["access-token"] == "${{ env.CS_ACCESS_TOKEN }}", (
        "the upload must read the token from the guarded environment, so an "
        "unset secret skips the step instead of failing it"
    )


def test_coverage_is_measured_before_it_is_uploaded() -> None:
    """The uploaded report is the one this job measured, not a stale file."""
    steps = workflow_steps(_CI_WORKFLOW, _CI_JOB)
    names = [str(step.get("name", "")) for step in steps]
    assert _MEASURE_COVERAGE in names, "the job must generate the report it uploads"
    assert _UPLOAD_COVERAGE in names, "the job must upload the report to CodeScene"
    assert names.index(_MEASURE_COVERAGE) < names.index(_UPLOAD_COVERAGE), (
        "coverage must be measured before it is uploaded"
    )


def test_pull_requests_enforce_coverage_with_the_local_ratchet() -> None:
    """Pull requests keep a coverage gate, but it is the local one."""
    coverage = sole_workflow_step(_CI_WORKFLOW, _CI_JOB, _MEASURE_COVERAGE)
    coverage_inputs = mapping(coverage["with"], subject="coverage generation inputs")
    assert coverage_inputs["with-ratchet"] == "true", (
        "the ratchet is the only coverage decision left on a pull request"
    )
    assert "if" not in coverage, (
        "the measuring step must run for both pushes and pull requests"
    )


def test_codescene_upload_uses_an_immutable_pin() -> None:
    """Every CodeScene reference is a full SHA, never a tag or short hash."""
    references = [
        f"{action}@{revision}"
        for action, revision in _workflow_uses()
        if action == _CODESCENE_ACTION
    ]
    assert references, "the repository must pin the CodeScene action somewhere"
    for reference in references:
        assert re.fullmatch(rf"{re.escape(_CODESCENE_ACTION)}@{_SHA}", reference), (
            f"{reference} is not an immutable commit SHA; a branch, tag, or "
            "abbreviated hash can be repointed by whoever controls it"
        )


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


def test_no_checksum_machinery_is_passed_or_maintained() -> None:
    """No step restates the digest the action already verifies for itself.

    The action reads `archive_sha256` from its own `cli-manifest.json` and
    checks the downloaded archive against it on every run. A caller-supplied
    digest adds no verification — it can only agree, or go stale and fail the
    run. This holds the whole workflow to that, so a checksum input cannot be
    reintroduced one step at a time alongside the refresh workflow that would
    have to feed it.
    """
    for workflow_path in workflow_paths():
        text = (REPO_ROOT / workflow_path).read_text(encoding="utf-8")
        assert "CODESCENE_CLI_SHA256" not in text, (
            f"{workflow_path} references the retired CodeScene checksum "
            "variable; the action verifies the archive from its own manifest"
        )
