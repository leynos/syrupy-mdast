"""Prove that a fresh offline install fails when Wenmode is unavailable."""

from __future__ import annotations

import subprocess  # ruff: ignore[suspicious-subprocess-import] -- fixed argv vectors only.
import sys
import typing as typ

from tests.support.wenmode_installation import (
    Wheelhouse,
    _clean_dependency_environment,
    _environment_python,
    _require_tool,
    _run,
)

if typ.TYPE_CHECKING:
    from pathlib import Path


def install_without_wenmode(wheelhouse: Wheelhouse, environment_path: Path) -> str:
    """Show a fresh offline installation fails when Wenmode is unavailable.

    Parameters
    ----------
    wheelhouse
        Prepared wheelhouse from which the Wenmode wheel is withheld.
    environment_path
        New virtual-environment path; its parent holds the staged wheelhouse
        and the empty installer cache.

    Returns
    -------
    str
        Combined standard output and standard error from the failed resolver.

    Examples
    --------
    >>> failure = install_without_wenmode(wheelhouse, environment_path)
    >>> "wenmode==0.15.2" in failure
    True
    """
    uv = _require_tool("uv")
    no_wenmode = _stage_wheelhouse_without_wenmode(wheelhouse, environment_path)
    _run(
        [uv, "venv", "--python", sys.executable, environment_path],
        cwd=environment_path.parent,
    )
    completed = _run_offline_install_expecting_failure(
        uv, no_wenmode, wheelhouse, environment_path
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    normalized = output.lower()
    assert "wenmode==0.15.2" in normalized, (
        f"failure did not report the missing Wenmode 0.15.2 candidate:\n{output}"
    )
    assert "not found" in normalized, (
        f"failure did not report the candidate as not found:\n{output}"
    )
    return output


def _stage_wheelhouse_without_wenmode(
    wheelhouse: Wheelhouse, environment_path: Path
) -> Path:
    """Link every prepared wheel except Wenmode into a separate wheelhouse."""
    no_wenmode = environment_path.parent / "wheelhouse-without-wenmode"
    no_wenmode.mkdir()
    for wheel in wheelhouse.path.glob("*.whl"):
        if wheel.name != wheelhouse.wenmode_wheel.name:
            (no_wenmode / wheel.name).symlink_to(wheel)
    return no_wenmode


def _run_offline_install_expecting_failure(
    uv: str,
    no_wenmode: Path,
    wheelhouse: Wheelhouse,
    environment_path: Path,
) -> subprocess.CompletedProcess[str]:
    """Attempt the dependency-free install and require a non-zero exit."""
    cache = environment_path.parent / "empty-uv-cache"
    cache.mkdir()
    try:
        completed = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- fixed uv executable and controlled test paths.
            [
                uv,
                "pip",
                "install",
                "--offline",
                "--no-index",
                "--no-cache",
                "--find-links",
                str(no_wenmode),
                "--python",
                str(_environment_python(environment_path)),
                str(wheelhouse.project_wheel),
            ],
            cwd=environment_path,
            env={**_clean_dependency_environment(), "UV_CACHE_DIR": str(cache)},
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired as error:
        message = (
            "offline missing-dependency install timed out after 300s\n"
            f"stdout:\n{error.stdout}\nstderr:\n{error.stderr}"
        )
        raise AssertionError(message) from error
    if completed.returncode == 0:
        message = "offline installation unexpectedly succeeded without Wenmode"
        raise AssertionError(message)
    return completed
