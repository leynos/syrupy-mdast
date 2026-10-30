"""Bounded execution of local commands for the packaging contracts."""

from __future__ import annotations

import os
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- fixed argv vectors only.
import typing as typ
from shutil import which

import pytest

if typ.TYPE_CHECKING:
    import collections.abc as cabc
    from pathlib import Path


def environment_python(environment_path: Path) -> Path:
    """Return the Python executable in a new virtual environment.

    Parameters
    ----------
    environment_path
        Root of a virtual environment created by the harness.

    Returns
    -------
    Path
        Interpreter path for the current host platform.

    Examples
    --------
    >>> environment_python(Path("env")).name in {"python", "python.exe"}
    True
    """
    return (
        environment_path / "Scripts" / "python.exe"
        if os.name == "nt"
        else environment_path / "bin" / "python"
    )


def require_tool(executable: str) -> str:
    """Return one required local tool executable."""
    resolved = which(executable)
    assert resolved is not None, f"the Wenmode contract requires {executable} on PATH"
    return resolved


def clean_dependency_environment() -> dict[str, str]:
    """Remove token and Git configuration overrides from the environment.

    The wheelhouse contains only pre-built PyPI wheels, so no Git transport or
    host-specific tool path is required for these commands.

    Returns
    -------
    dict[str, str]
        Copy of the current environment without credential or Git overrides.
    """
    environment = os.environ.copy()
    for key in list(environment):
        if key.startswith("GIT_CONFIG_") or key in {
            "GH_TOKEN",
            "GITHUB_TOKEN",
            "BASH_ENV",
            "GIT_SSH",
            "GIT_SSH_COMMAND",
        }:
            environment.pop(key, None)
    return environment


def run_command(
    command: cabc.Sequence[str | Path],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    """Run one known local command and fail the test if it exits non-zero."""
    result = _invoke(command, cwd=cwd, env=env, timeout=timeout)
    if result.returncode != 0:
        _fail_on_output(
            f"command failed ({result.returncode}): "
            f"{[str(part) for part in command]!r}",
            result,
        )
    return result


def run_command_expecting_failure(
    command: cabc.Sequence[str | Path],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    """Run one known local command that must exit non-zero.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Completed process whose output the caller can inspect. Timeouts still
        fail the test rather than counting as the expected failure.

    Examples
    --------
    >>> completed = run_command_expecting_failure(
    ...     [python, "-c", "raise SystemExit(1)"], cwd=temporary_path
    ... )
    >>> completed.returncode
    1
    """
    result = _invoke(command, cwd=cwd, env=env, timeout=timeout)
    if result.returncode == 0:
        _fail_on_output(
            f"command unexpectedly succeeded: {[str(part) for part in command]!r}",
            result,
        )
    return result


def _invoke(
    command: cabc.Sequence[str | Path],
    *,
    cwd: Path,
    env: dict[str, str] | None,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    """Run one argv without judging its exit status."""
    arguments = [str(argument) for argument in command]
    try:
        return subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- argv contains no shell text.
            arguments,
            cwd=cwd,
            env=clean_dependency_environment() if env is None else env,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        return _fail_on_timeout(timeout, arguments, error)


def _fail_on_timeout(
    timeout: int, arguments: list[str], error: subprocess.TimeoutExpired
) -> typ.NoReturn:
    """Fail the test with the timed-out command and its partial output."""
    pytest.fail(
        f"command timed out after {timeout}s: {arguments!r}\n"
        f"stdout:\n{error.stdout}\nstderr:\n{error.stderr}",
        pytrace=False,
    )


def _fail_on_output(
    headline: str, completed: subprocess.CompletedProcess[str]
) -> typ.NoReturn:
    """Fail the test with the command's bounded output as evidence."""
    pytest.fail(
        f"{headline}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        pytrace=False,
    )
