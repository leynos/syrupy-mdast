"""Prove that a fresh offline install fails when Wenmode is unavailable."""

from __future__ import annotations

import sys
import typing as typ

from tests.support.local_commands import (
    clean_dependency_environment,
    environment_python,
    require_tool,
    run_command,
    run_command_expecting_failure,
)

if typ.TYPE_CHECKING:
    import subprocess
    from pathlib import Path

    from tests.support.wenmode_installation import Wheelhouse


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
    uv = require_tool("uv")
    no_wenmode = _stage_wheelhouse_without_wenmode(wheelhouse, environment_path)
    run_command(
        [uv, "venv", "--python", sys.executable, environment_path],
        cwd=environment_path.parent,
    )
    completed = _install_from_missing_wenmode(
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


def _install_from_missing_wenmode(
    uv: str,
    no_wenmode: Path,
    wheelhouse: Wheelhouse,
    environment_path: Path,
) -> subprocess.CompletedProcess[str]:
    """Attempt the dependency-free install and require a non-zero exit."""
    cache = environment_path.parent / "empty-uv-cache"
    cache.mkdir()
    return run_command_expecting_failure(
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
            str(environment_python(environment_path)),
            str(wheelhouse.project_wheel),
        ],
        cwd=environment_path,
        env={**clean_dependency_environment(), "UV_CACHE_DIR": str(cache)},
    )
