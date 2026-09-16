"""Contracts tying the CI compatibility matrix to package metadata."""

from __future__ import annotations

import tomllib

from tests.support.make_contract import REPO_ROOT, mapping, objects, workflow_job


def test_matrix_floor_matches_declared_specifier() -> None:
    """The matrix exercises every supported Python and the Syrupy floor."""
    configuration = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    job = workflow_job(".github/workflows/ci.yml", "compatibility-matrix")
    strategy = mapping(job.get("strategy"), subject="compatibility matrix strategy")
    assert strategy["fail-fast"] is False, (
        "the compatibility matrix must report every independent lane failure"
    )
    matrix = mapping(strategy.get("matrix"), subject="compatibility matrix")
    assert matrix["python-version"] == ["3.12", "3.13", "3.14"], (
        "the matrix must cover every supported Python release"
    )
    assert matrix["syrupy-version"] == ["5.0.0", "latest"], (
        "the matrix must test the declared Syrupy floor and latest release"
    )
    assert configuration["project"]["dependencies"] == ["syrupy>=5.0.0,<7.0.0"], (
        "the tested Syrupy floor must remain the declared package floor"
    )
    assert mapping(
        job.get("permissions"), subject="compatibility matrix permissions"
    ) == {"contents": "read"}, (
        "the compatibility matrix must use read-only repository permissions"
    )
    steps = objects(job.get("steps"), subject="compatibility matrix steps")
    assert {"name": "Sync dependencies", "run": "uv sync --group dev"} in steps, (
        "the compatibility matrix must synchronize the declared development set"
    )
    assert {
        "name": "Pin the declared Syrupy floor",
        "if": "matrix.syrupy-version != 'latest'",
        "run": 'uv pip install "syrupy==${{ matrix.syrupy-version }}"',
    } in steps, "the floor matrix lane must install its exact Syrupy version"
    assert {
        "name": "Upgrade to the newest supported Syrupy release",
        "if": "matrix.syrupy-version == 'latest'",
        "run": 'uv pip install --upgrade "syrupy<7.0.0"',
    } in steps, "the latest matrix lane must install the newest Syrupy below 7.0.0"
