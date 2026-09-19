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

import re

from tests.support.make_contract import (
    mapping,
    sole_workflow_step,
    workflow_jobs,
    workflow_steps,
)

_CI_WORKFLOW = ".github/workflows/ci.yml"
_CI_JOB = "lint-test"
_CODESCENE_ACTION = "leynos/shared-actions/.github/actions/upload-codescene-coverage"
_PUSH_TO_MAIN = "github.event_name == 'push' && github.ref == 'refs/heads/main'"
_MEASURE_COVERAGE = "Test and Measure Coverage"
_UPLOAD_COVERAGE = "Upload coverage data to CodeScene"


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
    assert upload_inputs["archive-checksum"] == "${{ vars.CODESCENE_CLI_SHA256 }}", (
        "the upload must verify the pinned CodeScene archive against the "
        "manifest digest the refresh workflow publishes, not the deprecated "
        "installer checksum"
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
    """The shared action is consumed at a commit, never at a moving tag."""
    upload = sole_workflow_step(_CI_WORKFLOW, _CI_JOB, _UPLOAD_COVERAGE)
    assert re.fullmatch(
        rf"{re.escape(_CODESCENE_ACTION)}@[0-9a-f]{{40}}", str(upload["uses"])
    ), "the shared CodeScene action must use an immutable commit SHA"


def test_codescene_checksum_refresh_uses_an_immutable_action_reference() -> None:
    """The retained checksum refresh workflow pins its GitHub API client."""
    update_variable = sole_workflow_step(
        ".github/workflows/get-codescene-sha.yml",
        "refresh-sha",
        "Update repository variable",
    )
    assert update_variable["uses"] == (
        "actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd"
    ), "checksum refresh must pin its GitHub API action"
    update_inputs = mapping(
        update_variable["with"], subject="CodeScene checksum refresh inputs"
    )
    assert "CODESCENE_CLI_SHA256" in str(update_inputs["script"]), (
        "the checksum refresh workflow must continue to update CODESCENE_CLI_SHA256"
    )


def test_refresh_publishes_the_digest_the_pinned_action_validates() -> None:
    """The refreshed digest must come from the pinned action's own manifest.

    The action compares the value it receives against `archive_sha256` in the
    manifest at its own revision. A digest taken from anywhere else — the
    upstream installer script, or a manifest at another revision — would fail
    that comparison and break the upload the moment the variable was set.
    """
    upload = sole_workflow_step(_CI_WORKFLOW, _CI_JOB, _UPLOAD_COVERAGE)
    pinned_action = str(upload["uses"])
    pinned_sha = pinned_action.rpartition("@")[2]

    refresh = sole_workflow_step(
        ".github/workflows/get-codescene-sha.yml",
        "refresh-sha",
        "Read the manifest digest & record it",
    )
    script = str(refresh.get("run", ""))
    assert "cli-manifest.json" in script, (
        "the refresh must read the digest from the action's cli-manifest.json"
    )
    assert "archive_sha256" in script, (
        "the refresh must publish the manifest's archive digest, which is the "
        "value the action compares archive-checksum against"
    )
    assert pinned_sha in script, (
        "the refresh must read the manifest at the same immutable revision "
        "ci.yml pins the action at; bump the two together"
    )
    assert "install-cs-coverage-tool.sh" not in script, (
        "the deprecated installer-script digest is not what the action checks"
    )
