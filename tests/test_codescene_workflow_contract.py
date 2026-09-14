"""Contracts for the CodeScene coverage upload and pull-request gates."""

from __future__ import annotations

import re

from tests.support.make_contract import (
    mapping,
    objects,
    sole_workflow_step,
    workflow_job,
)


def test_codescene_workflow_uses_distinct_upload_and_check_modes() -> None:
    """The CI workflow creates a baseline and evaluates trusted pull requests."""
    checkout = sole_workflow_step(
        ".github/workflows/ci.yml", "lint-test", "Check out repository"
    )
    checkout_inputs = mapping(checkout["with"], subject="CodeScene checkout inputs")
    assert checkout_inputs["fetch-depth"] == 0, (
        "the CodeScene pull-request gate must have full history for its merge base"
    )

    upload = sole_workflow_step(
        ".github/workflows/ci.yml", "lint-test", "Upload main coverage to CodeScene"
    )
    assert (
        upload["if"] == "github.event_name == 'push' && github.ref == 'refs/heads/main'"
    ), "CodeScene uploads must run only for default-branch pushes"
    upload_inputs = mapping(upload["with"], subject="CodeScene upload inputs")
    assert upload_inputs["mode"] == "upload", "main must use upload mode"
    assert upload_inputs["path"] == "coverage.xml", "main must upload coverage.xml"
    assert upload_inputs["format"] == "cobertura", "main must upload Cobertura data"
    assert upload_inputs["access-token"] == "${{ secrets.CS_ACCESS_TOKEN }}", (
        "main uploads must receive the CodeScene token"
    )
    assert upload_inputs["installer-checksum"] == "${{ vars.CODESCENE_CLI_SHA256 }}", (
        "main uploads must verify the CodeScene installer"
    )

    check = sole_workflow_step(
        ".github/workflows/ci.yml",
        "lint-test",
        "Check trusted pull request coverage with CodeScene",
    )
    assert (
        "github.event.pull_request.base.ref == github.event.repository.default_branch"
        in str(check["if"])
    ), "CodeScene checks must target the default branch"
    check_inputs = mapping(check["with"], subject="CodeScene check inputs")
    assert check_inputs["mode"] == "check", "trusted pull requests must use check mode"
    assert check_inputs["path"] == "coverage.xml", "checks must read coverage.xml"
    assert check_inputs["format"] == "cobertura", "checks must read Cobertura data"
    assert check_inputs["project-url"] == (
        "https://api.codescene.io/v2/projects/82582"
    ), "checks must target the syrupy-mdast CodeScene project"
    assert check_inputs["access-token"] == "${{ secrets.CS_ACCESS_TOKEN }}", (
        "checks must receive the CodeScene token"
    )
    assert check_inputs["installer-checksum"] == "${{ vars.CODESCENE_CLI_SHA256 }}", (
        "checks must verify the CodeScene installer"
    )


def test_codescene_workflow_has_a_pinned_action_and_token_preflight() -> None:
    """The trusted check cannot silently pass without its required secret."""
    job = workflow_job(".github/workflows/ci.yml", "lint-test")
    steps = objects(job["steps"], subject="CodeScene workflow steps")
    shared_action_steps = [
        step
        for step in steps
        if str(step.get("uses", "")).startswith(
            "leynos/shared-actions/.github/actions/upload-codescene-coverage@"
        )
    ]
    assert len(shared_action_steps) == 2, "CI must have separate upload and check steps"
    for step in shared_action_steps:
        assert re.fullmatch(
            r"leynos/shared-actions/.github/actions/upload-codescene-coverage@[0-9a-f]{40}",
            str(step["uses"]),
        ), "the shared CodeScene action must use an immutable commit SHA"

    preflight = sole_workflow_step(
        ".github/workflows/ci.yml",
        "lint-test",
        "Preflight CodeScene token for trusted pull requests",
    )
    assert "github.event.pull_request.head.repo.full_name == github.repository" in str(
        preflight["if"]
    ), "only trusted pull requests may receive the CodeScene secret"
    assert "CS_ACCESS_TOKEN is empty" in str(preflight["run"]), (
        "trusted pull requests must fail quickly when their CodeScene secret is absent"
    )


def test_codescene_workflow_has_no_raw_cli_commands_and_notices_forks() -> None:
    """Consumers delegate to the action and never expose a token to fork code."""
    job = workflow_job(".github/workflows/ci.yml", "lint-test")
    steps = objects(job["steps"], subject="CodeScene workflow steps")
    raw_command_steps = [
        str(step.get("run", ""))
        for step in steps
        if "cs-coverage upload" in str(step.get("run", ""))
        or "cs-coverage check" in str(step.get("run", ""))
    ]
    assert not raw_command_steps, (
        "CI must delegate CodeScene CLI execution to the action"
    )

    fork_notice = sole_workflow_step(
        ".github/workflows/ci.yml",
        "lint-test",
        "Skip CodeScene coverage gate for fork pull requests",
    )
    assert "github.event.pull_request.head.repo.full_name != github.repository" in str(
        fork_notice["if"]
    ), "fork pull requests require an explicit CodeScene skip path"
    assert "Fork pull requests do not receive CS_ACCESS_TOKEN" in str(
        fork_notice["run"]
    ), "fork skips must explain why CodeScene does not run"


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
