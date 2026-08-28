"""Contract tests keeping toolchain version pins in sync.

The ruff and ty releases are pinned in three places: the ``RUFF_VERSION`` and
``TY_VERSION`` defaults in the Makefile, the matching environment variables in
``.github/workflows/ci.yml``, and the ``==``-pinned entries in the ``dev``
dependency group of ``pyproject.toml``. A mismatch between any two sites
produces version-skew failures (for example, preview-only Ruff rules firing in
one environment but not another), so these tests assert the sites agree
without asserting any specific version.
"""

from __future__ import annotations

import tomllib

import pytest

from tests.support.make_contract import (
    REPO_ROOT,
    mapping,
    variable_tokens,
    workflow_job,
)


def _makefile_version(tool_env_name: str) -> str:
    """Read a tool's default version pin from the parsed Makefile."""
    tokens = variable_tokens(tool_env_name)
    assert len(tokens) == 1, (
        f"expected {tool_env_name} to hold a single version token, got {tokens!r}"
    )
    return tokens[0]


def _ci_version(tool_env_name: str) -> str:
    """Read a tool's version pin from the CI lint job environment."""
    job = workflow_job(".github/workflows/ci.yml", "lint-test")
    environment = mapping(job.get("env"), subject="ci.yml lint-test environment")
    version = environment.get(tool_env_name)
    assert isinstance(version, str), (
        f"expected the {tool_env_name} environment variable in ci.yml to be a "
        "version string"
    )
    return version


def _pyproject_version(tool_name: str) -> str:
    """Read a tool's ``==`` pin from the dev dependency group."""
    pyproject = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    dev_dependencies: list[str] = pyproject["dependency-groups"]["dev"]
    pins = [
        specifier.removeprefix(f"{tool_name}==")
        for specifier in dev_dependencies
        if specifier.startswith(f"{tool_name}==")
    ]
    assert len(pins) == 1, (
        f"expected exactly one '{tool_name}==' pin in the dev dependency "
        f"group, found {len(pins)}"
    )
    return pins[0]


@pytest.mark.parametrize(
    ("tool_name", "tool_env_name"),
    [("ruff", "RUFF_VERSION"), ("ty", "TY_VERSION")],
)
def test_tool_version_pins_agree(tool_name: str, tool_env_name: str) -> None:
    """The Makefile, CI workflow, and pyproject.toml pin the same release."""
    makefile_pin = _makefile_version(tool_env_name)
    ci_pin = _ci_version(tool_env_name)
    pyproject_pin = _pyproject_version(tool_name)
    assert makefile_pin == ci_pin, (
        f"{tool_name} is pinned to {makefile_pin} in the Makefile but "
        f"{ci_pin} in .github/workflows/ci.yml; bump both sites together"
    )
    assert makefile_pin == pyproject_pin, (
        f"{tool_name} is pinned to {makefile_pin} in the Makefile but "
        f"{pyproject_pin} in pyproject.toml; bump both sites together"
    )
