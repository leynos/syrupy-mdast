"""Guard the Namespace runner and reusable wheel-build boundaries."""

from __future__ import annotations

from pathlib import Path
import typing as typ

import pytest
import yaml

_REPO_ROOT: typ.Final = Path(__file__).resolve().parents[1]
_NAMESPACE_RUNNER: typ.Final = "namespace-profile-default"
_DIRECT_JOBS: typ.Final = (
    ("ci.yml", "lint-test"),
    ("get-codescene-sha.yml", "refresh-sha"),
    ("release.yml", "pure-wheel"),
    ("release.yml", "release"),
)


def test_act_validation_retains_github_hosted_docker() -> None:
    """Keep the Docker-backed workflow on its proven GitHub-hosted runner."""
    jobs = _workflow("act-validation.yml")["jobs"]
    assert isinstance(jobs, dict), "act-validation.yml must declare jobs"
    act_validation = jobs["act-validation"]
    assert isinstance(act_validation, dict), "act-validation job must be a mapping"
    assert act_validation["runs-on"] == "ubuntu-latest"


def _workflow(name: str) -> dict[str, object]:
    """Parse a checked-in GitHub Actions workflow."""
    path = _REPO_ROOT / ".github" / "workflows" / name
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict), f"{name} must contain a mapping"
    return loaded


@pytest.mark.parametrize(("workflow_name", "job_name"), _DIRECT_JOBS)
def test_direct_linux_job_uses_shared_namespace_profile(
    workflow_name: str, job_name: str
) -> None:
    """Require each repository-owned Linux job to retain the shared profile."""
    jobs = _workflow(workflow_name)["jobs"]
    assert isinstance(jobs, dict), f"{workflow_name} must declare jobs"
    job = jobs[job_name]
    assert isinstance(job, dict), f"{workflow_name} {job_name} must be a mapping"
    assert job["runs-on"] == _NAMESPACE_RUNNER


def test_reusable_wheel_matrix_retains_its_cross_platform_boundary() -> None:
    """Keep wheel-build runner selection in the reusable matrix."""
    jobs = _workflow("build-wheels.yml")["jobs"]
    assert isinstance(jobs, dict), "build-wheels.yml must declare jobs"
    build = jobs["build"]
    assert isinstance(build, dict), "build-wheels.yml build must be a mapping"
    assert build["runs-on"] == "${{ matrix.os }}"
