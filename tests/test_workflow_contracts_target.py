"""Execution-boundary tests for the `test-workflow-contracts` Make target.

The target is the repository's only entry to the shared CV-005 checker. These
tests assert what Make actually does with it, using the recorder that stands in
for ``$(UV)``: the target dispatches ``cv005-contracts check --repository .``
from the pinned shared-actions commit, a failing checker fails the target, and
``make all`` includes the target so a local green run covers the contract.
"""

from __future__ import annotations

import re
import subprocess  # ruff: ignore[suspicious-subprocess-import] - reads Make's rule database.
import tomllib
import typing as typ

from tests.support.make_contract import (
    REPO_ROOT,
    make_executable,
    sole_workflow_step,
    variable_tokens,
    workflow_jobs,
    workflow_steps,
)
from tests.support.make_recorder import invocations, run_make

if typ.TYPE_CHECKING:
    import collections.abc as cabc
    from pathlib import Path

_TARGET: typ.Final = "test-workflow-contracts"
_CI_STEP: typ.Final = "Check the CV-005 contracts"
_ENTRY_POINT: typ.Final = "cv005-contracts"
_PIN: typ.Final = re.compile(r"^[0-9a-f]{40}$")


def test_the_target_runs_the_pinned_checker_against_this_repository(
    tmp_path: Path,
) -> None:
    """The target must dispatch `cv005-contracts check --repository .` once."""
    run_make(tmp_path, _TARGET, check=True)

    checker = [call for call in invocations(tmp_path) if call[0] == _ENTRY_POINT]
    assert len(checker) == 1, "the target must run the shared checker exactly once"
    assert checker[0][1] == ("check", "--repository", "."), (
        "the checker must verify this repository's own workflows"
    )


def test_the_checker_is_fetched_from_a_full_commit_pin(tmp_path: Path) -> None:
    """The checker must come from the commit `CV005_CONTRACTS_REF` names."""
    (pin,) = variable_tokens("CV005_CONTRACTS_REF")[-1:]
    assert _PIN.match(pin), "CV005_CONTRACTS_REF must be a full 40-hex commit"

    run_make(tmp_path, _TARGET, check=True)
    log = (tmp_path / "invocations.jsonl").read_text(encoding="utf-8")
    assert f"shared-actions@{pin}" in log, (
        "the recorded uv call must fetch shared-actions at the pinned commit"
    )


def test_a_failing_checker_fails_the_target(tmp_path: Path) -> None:
    """A checker exit status must reach Make, so a violation fails the gate."""
    result = run_make(tmp_path, _TARGET, check=False, fail_tokens=(_ENTRY_POINT,))

    assert result.returncode != 0, "the target must fail when the shared checker fails"


def test_make_all_includes_the_target() -> None:
    """`make all` must list the target so a local gate run covers the contract."""
    database = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - fixed Make command.
        [make_executable(), "-pn", "-f", str(REPO_ROOT / "Makefile"), "all"],
        capture_output=True,
        check=True,
        cwd=REPO_ROOT,
        text=True,
    ).stdout
    rule = next(
        (line for line in database.splitlines() if line.startswith("all:")), None
    )
    assert rule is not None, "the Makefile must define an `all` target"
    assert _TARGET in rule.removeprefix("all:").split(), (
        f"`all` must depend on {_TARGET}"
    )


def test_ci_runs_the_target_unconditionally() -> None:
    """The `lint-test` job must run the target as a plain, enforcing step."""
    step = sole_workflow_step(".github/workflows/ci.yml", "lint-test", _CI_STEP)

    assert step.get("run") == f"make {_TARGET}", (
        "the CI step must run exactly `make test-workflow-contracts`"
    )
    for key in ("if", "continue-on-error", "shell"):
        assert key not in step, f"the CI step must not carry `{key}`"


_WORKFLOWS: typ.Final = (
    ".github/workflows/ci.yml",
    ".github/workflows/coverage-main.yml",
)
_PACKAGE: typ.Final = "syrupy_mdast"


def _coverage_steps(workflow: str) -> cabc.Iterator[tuple[str, dict[str, object]]]:
    """Yield `(job name, step)` for each generate-coverage step of a workflow."""
    for job_name in workflow_jobs(workflow):
        for step in workflow_steps(workflow, job_name):
            uses = step.get("uses")
            if isinstance(uses, str) and "/generate-coverage@" in uses:
                yield job_name, step


def _coverage_scopes() -> dict[str, object]:
    """Return the `python-source` each workflow's generate-coverage step carries."""
    scopes: dict[str, object] = {}
    for workflow in _WORKFLOWS:
        for job_name, step in _coverage_steps(workflow):
            inputs = step.get("with")
            scopes[f"{workflow}:{job_name}"] = (
                inputs.get("python-source") if isinstance(inputs, dict) else None
            )
    return scopes


def test_both_coverage_lanes_measure_the_package_not_its_tests() -> None:
    """Both lanes and `cv005.toml` must scope coverage to exactly the package.

    The scope is compared with the package directory itself, not merely with
    each other, so `.` (the whole repository, tests included), `./tests` and a
    missing scope all fail.
    """
    expected = f"./{_PACKAGE}"
    selection = tomllib.loads(
        (REPO_ROOT / ".github" / "cv005.toml").read_text(encoding="utf-8")
    )["selection"]
    scopes = _coverage_scopes()

    assert selection["python-source"] == expected, (
        f"cv005.toml must select the package {expected!r}"
    )
    assert len(scopes) == 2, "the pull-request lane and the publisher each run it"
    assert set(scopes.values()) == {expected}, (
        f"every generate-coverage step must carry python-source {expected!r}: {scopes}"
    )
    assert (REPO_ROOT / _PACKAGE / "__init__.py").is_file(), (
        "the scope must name an importable package, not a directory of tests"
    )
