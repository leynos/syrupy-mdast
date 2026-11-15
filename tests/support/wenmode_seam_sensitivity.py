"""Sensitivity control for the installed probe's internal adapter witness.

The installed probe proves that the private Wenmode seam works in a real
environment. That claim is only meaningful if the probe would notice the seam
being bypassed, so this control replaces ``syrupy_mdast._wenmode.parse_markdown``
with a callable that raises a named sentinel and requires the probe to fail with
that sentinel. A probe that reached Wenmode directly would still succeed, which
is exactly the sensitivity gap this control rejects.
"""

from __future__ import annotations

import typing as typ

from tests.support.local_commands import run_command_expecting_failure

if typ.TYPE_CHECKING:
    from pathlib import Path

_SEAM_SENTINEL = "SeamBypassError"

_REPLACED_SEAM_PROGRAM = f'''\
import runpy
import sys

import syrupy_mdast._wenmode as seam


class {_SEAM_SENTINEL}(RuntimeError):
    """Signal that the probe called the replaced adapter callable."""


def reject(source):
    """Raise the sentinel for any adapter call."""
    raise {_SEAM_SENTINEL}(source)


seam.parse_markdown = reject
runpy.run_path(sys.argv[1], run_name="__main__")
'''


def replaced_seam_program() -> str:
    """Return the child program that replaces the adapter before probing.

    Returns
    -------
    str
        Program for ``python -c`` whose first argument is the probe path. It
        replaces the seam, then executes the probe as ``__main__`` so the probe
        sees its own ``if __name__ == "__main__"`` entry point.
    """
    return _REPLACED_SEAM_PROGRAM


def assert_replaced_seam_fails_probe(
    python: Path, probe_path: Path, *, cwd: Path, env: dict[str, str]
) -> None:
    """Require the installed probe to fail through the replaced adapter seam.

    The probe must exit non-zero with the sentinel in its standard error. A
    probe that succeeds, or fails for any other reason, is not sensitive to the
    seam being bypassed, so this control fails the test in both cases.

    Parameters
    ----------
    python
        Interpreter of the fresh environment the probe runs in.
    probe_path
        Installed probe module to run unchanged under the replacement.
    cwd
        Directory the child starts in; kept outside the checkout.
    env
        Restricted probe environment, shared with the passing probe run.

    Examples
    --------
    >>> assert_replaced_seam_fails_probe(python, probe_path, cwd=cwd, env=probe_env)
    """
    completed = run_command_expecting_failure(
        [python, "-I", "-W", "error", "-c", replaced_seam_program(), probe_path],
        cwd=cwd,
        env=env,
        timeout=30,
    )
    assert _SEAM_SENTINEL in completed.stderr, (
        "the probe must fail through the replaced adapter callable, not bypass "
        f"it; stderr was:\n{completed.stderr}"
    )
