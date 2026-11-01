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
    """Resolve one required local tool executable.

    Parameters
    ----------
    executable
        Command name that the packaging contract needs on ``PATH``.

    Returns
    -------
    str
        Absolute path of the resolved executable.

    Examples
    --------
    >>> Path(require_tool("uv")).name
    'uv'
    """
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
    """Run one known local command and fail the test if it exits non-zero.

    Parameters
    ----------
    command
        Program and arguments to run.
    cwd
        Directory the child starts in.
    env
        Environment override; the credential-scrubbed host environment is used
        when omitted.
    timeout
        Seconds to allow before the test fails.

    Returns
    -------
    subprocess.CompletedProcess[str]
        Captured text output from the successful command.

    Examples
    --------
    >>> run_command([python, "-c", "pass"], cwd=temporary_path).returncode
    0
    """
    result = _invoke(command, cwd=cwd, env=env, timeout=timeout)
    _require_exit_status(result, command, expected_failure=False)
    return result


def run_command_expecting_failure(
    command: cabc.Sequence[str | Path],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    """Run one known local command that must exit non-zero.

    Parameters
    ----------
    command
        Failing invocation to attempt.
    cwd
        Directory the child starts in.
    env
        Environment override for the failing attempt.
    timeout
        Seconds to allow before the test fails.

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
    _require_exit_status(result, command, expected_failure=True)
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


def _require_exit_status(
    completed: subprocess.CompletedProcess[str],
    command: cabc.Sequence[str | Path],
    *,
    expected_failure: bool,
) -> None:
    """Fail the test when the exit status contradicts the caller's expectation."""
    if (completed.returncode == 0) is expected_failure:
        headline = (
            f"command unexpectedly succeeded: {_argv(command)!r}"
            if expected_failure
            else f"command failed ({completed.returncode}): {_argv(command)!r}"
        )
        _fail_on_output(headline, completed)


def _argv(command: cabc.Sequence[str | Path]) -> list[str]:
    """Render an argv sequence as the strings the child received."""
    return [str(part) for part in command]


def _fail_on_output(
    headline: str, completed: subprocess.CompletedProcess[str]
) -> typ.NoReturn:
    """Fail the test with the command's bounded output as evidence."""
    pytest.fail(
        f"{headline}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        pytrace=False,
    )
