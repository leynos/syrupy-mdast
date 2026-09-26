"""Record the tools a Make target dispatches through ``$(UV)``.

The execution-boundary tests redirect the Makefile's single ``$(UV)`` variable
to a recorder script, run a target from an isolated directory, and read back
which tool each ``uv`` call would have executed and with which arguments. No
real tool runs, and the recorder can fail one chosen invocation so a test can
prove the target stops at the first failing tier.
"""

from __future__ import annotations

import json
import os
import subprocess  # ruff: ignore[suspicious-subprocess-import] - boundary tests drive Make.
import sys
import typing as typ

from tests.support.make_contract import REPO_ROOT, make_executable

if typ.TYPE_CHECKING:
    import collections.abc as cabc
    from pathlib import Path

LOG_NAME: typ.Final = "invocations.jsonl"
RECORDER_NAME: typ.Final = "uv-recorder"
FAIL_TOKENS_VARIABLE: typ.Final = "RECORDER_FAIL_TOKENS"
ARGUMENT_SEPARATOR: typ.Final = "\x1f"
# Both Pylint passes run the `pylint` entry point; the PyPy pass is told apart
# by its interpreter, and recorded under this label.
PYPY_PYLINT: typ.Final = "pylint@pypy"


def entry_index(argv: cabc.Sequence[str]) -> int | None:
    """Return the position of the tool `uv` would execute for `argv`.

    `uv` resolves the tool from ``--from <spec> <entry point>``, or from
    ``run <entry point>`` for project-environment commands. Setup calls such
    as ``uv venv --clear`` name no tool and yield ``None``.

    Returns
    -------
    int or None
        The entry point's index, or ``None`` for a call that runs no tool.
    """
    for marker, offset in (("--from", 2), ("run", 1)):
        if marker in argv:
            index = argv.index(marker) + offset
            return index if index < len(argv) else None
    return None


def tier_name(argv: cabc.Sequence[str], index: int) -> str:
    """Name the tier for an entry point, labelling Pylint run on PyPy."""
    python = argv[argv.index("--python") + 1] if "--python" in argv else ""
    is_pypy_pylint = argv[index] == "pylint" and python.startswith("pypy")
    return PYPY_PYLINT if is_pypy_pylint else argv[index]


def write_recorder(directory: Path) -> str:
    """Create a fake `uv` that logs each invocation and can fail one call.

    The recorder fails only when every token named by
    ``RECORDER_FAIL_TOKENS`` appears in its arguments, so the caller selects
    the failing invocation without the recorder needing to interpret `uv`'s
    command line.

    Returns
    -------
    str
        Absolute path to the executable recorder.
    """
    recorder = directory / RECORDER_NAME
    recorder.write_text(
        f"#!{sys.executable}\n"
        "import json\n"
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n"
        "argv = sys.argv[1:]\n"
        f"log = Path({str(directory / LOG_NAME)!r})\n"
        'with log.open("a", encoding="utf-8") as handle:\n'
        '    handle.write(json.dumps(argv) + "\\n")\n'
        f'raw = os.environ.get({FAIL_TOKENS_VARIABLE!r}, "")\n'
        f"tokens = [token for token in raw.split({ARGUMENT_SEPARATOR!r}) if token]\n"
        "if tokens and all(token in argv for token in tokens):\n"
        "    sys.exit(1)\n",
        encoding="utf-8",
    )
    recorder.chmod(0o755)
    return str(recorder)


def run_make(
    directory: Path,
    target: str,
    *,
    check: bool,
    fail_tokens: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    """Run one Make target against the recorder in an isolated directory.

    Returns
    -------
    subprocess.CompletedProcess[str]
        The completed ``make`` process.
    """
    # `build` depends on `.venv`, which depends on `pyproject.toml`; a
    # throwaway file lets the prerequisite resolve without touching the
    # repository. Its `uv` calls reach the recorder and name no entry point.
    (directory / "pyproject.toml").touch()
    recorder = write_recorder(directory)
    command = (
        make_executable(),
        "-f",
        str(REPO_ROOT / "Makefile"),
        target,
        f"UV={recorder}",
    )
    environment = {
        **os.environ,
        FAIL_TOKENS_VARIABLE: ARGUMENT_SEPARATOR.join(fail_tokens),
    }
    return subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - fixed Make command.
        command,
        capture_output=True,
        check=check,
        cwd=directory,
        env=environment,
        text=True,
    )


def invocations(directory: Path) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Return each recorded tool invocation as an entry point and arguments.

    Setup calls made by the `build` prerequisite carry no entry point and are
    omitted, leaving only the tools a target dispatches.

    Returns
    -------
    tuple
        Pairs of entry-point name and the arguments that follow it.
    """
    log = directory / LOG_NAME
    if not log.exists():
        return ()
    recorded: list[tuple[str, tuple[str, ...]]] = []
    for line in log.read_text(encoding="utf-8").splitlines():
        argv: list[str] = json.loads(line)
        index = entry_index(argv)
        if index is None:
            continue
        recorded.append((tier_name(argv, index), tuple(argv[index + 1 :])))
    return tuple(recorded)


def entry_points(directory: Path) -> tuple[str, ...]:
    """Return the ordered entry points a target dispatched.

    Returns
    -------
    tuple of str
        Entry-point names in invocation order.
    """
    return tuple(name for name, _ in invocations(directory))


def arguments_for(directory: Path, entry_point: str) -> tuple[str, ...]:
    """Return the sole recorded argument list for `entry_point`.

    Returns
    -------
    tuple of str
        The arguments the tier received.
    """
    matches = [
        arguments for name, arguments in invocations(directory) if name == entry_point
    ]
    assert len(matches) == 1, (
        f"expected exactly one {entry_point!r} invocation, found {len(matches)}"
    )
    return matches[0]
