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

import re
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _extract_version(pattern: str, text: str, description: str) -> str:
    """Return the single regex capture for ``pattern``, failing helpfully.

    Parameters
    ----------
    pattern : str
        Multiline regex with one capture group holding the version.
    text : str
        File contents to search.
    description : str
        Human-readable name of the pin site, used in the failure message.

    Returns
    -------
    str
        The captured version string.

    Examples
    --------
    >>> _extract_version("^V=(.+)$", "V=1.2.3", "example pin")
    '1.2.3'
    """
    match = re.search(pattern, text, re.MULTILINE)
    assert match is not None, f"could not locate the {description}"
    return match.group(1)


def _makefile_version(tool_env_name: str) -> str:
    """Read a tool's default version pin from the Makefile."""
    makefile_text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    return _extract_version(
        rf"^{tool_env_name} \?= (\S+)$",
        makefile_text,
        f"{tool_env_name} default in the Makefile",
    )


def _ci_version(tool_env_name: str) -> str:
    """Read a tool's version pin from the CI workflow environment block."""
    ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    return _extract_version(
        rf"^\s+{tool_env_name}: ['\"]?([0-9][^'\"\s]*)['\"]?$",
        ci_text,
        f"{tool_env_name} environment variable in ci.yml",
    )


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
