"""Boundary tests for the Skylos documented-whitelist Make target.

The ``skylos-allow`` target validates ``SYMBOL`` and ``REASON`` at the Make
boundary before invoking Skylos, so invalid invocations here are non-mutating
by construction. Valid invocations are exercised against a temporary argument
recorder injected through ``SKYLOS_CLI``, proving the quoted Make exports
reach Skylos as exactly ``["whitelist", symbol, "--reason", reason]`` without
touching the repository's ``pyproject.toml``.
"""

from __future__ import annotations

import json
import os
import string
import subprocess  # ruff: ignore[suspicious-subprocess-import] - boundary tests invoke a fixed Make command.
import sys
import typing as typ

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from tests.support.make_contract import REPO_ROOT, make_executable

if typ.TYPE_CHECKING:
    from pathlib import Path

_MISSING_SYMBOL_ERROR: typ.Final = (
    "Error: SYMBOL is required for a named whitelist exception"
)
_MISSING_REASON_ERROR: typ.Final = (
    "Error: REASON is required for a named whitelist exception"
)
_WHITESPACE_ONLY_TEXT = st.text(alphabet=" \t", min_size=1, max_size=8)
_SHELL_SENSITIVE_TEXT = st.builds(
    lambda prefix, content, suffix: prefix + content + suffix,
    st.text(alphabet=" \t", max_size=4),
    st.text(
        alphabet=string.ascii_letters + string.digits + "_$;|&'\"()[]{}*?!\\`",
        min_size=1,
        max_size=24,
    ),
    st.text(alphabet=" \t", max_size=4),
)


def _run_skylos_allow(**variables: str) -> subprocess.CompletedProcess[str]:
    """Run the whitelist boundary in the repository without reaching Skylos.

    Injects ``NAME=wsl-hostname`` to prove the target reads ``SYMBOL`` rather
    than WSL's caller-owned ``NAME`` environment variable.

    Returns
    -------
    subprocess.CompletedProcess[str]
        The completed ``make skylos-allow`` process.
    """
    environment: dict[str, str] = {**os.environ, "NAME": "wsl-hostname"}
    environment.pop("SYMBOL", None)
    environment.pop("REASON", None)
    environment.update(variables)
    return subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - resolved Make target and arguments.
        (make_executable(), "skylos-allow"),
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
        env=environment,
        text=True,
    )


def _write_argument_recorder(directory: Path) -> str:
    """Create a fake Skylos CLI that serializes its arguments to a file."""
    recorder = directory / "skylos-recorder"
    recorder.write_text(
        f"#!{sys.executable}\n"
        "import json\n"
        "import sys\n"
        "from pathlib import Path\n"
        "Path('skylos-arguments.json').write_text(\n"
        "    json.dumps(sys.argv[1:]), encoding='utf-8'\n"
        ")\n",
        encoding="utf-8",
    )
    recorder.chmod(0o755)
    return str(recorder)


def _run_recorded_whitelist(
    directory: Path,
    *,
    symbol: str,
    reason: str,
) -> subprocess.CompletedProcess[str]:
    """Run ``skylos-allow`` against a recorder in an isolated directory."""
    command = (
        make_executable(),
        "-f",
        str(REPO_ROOT / "Makefile"),
        "skylos-allow",
        f"SKYLOS_CLI={_write_argument_recorder(directory)}",
        f"SKYLOS_WHITELIST_LOCK={directory / '.skylos-whitelist.lock'}",
    )
    return subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - fixed Makefile and test arguments.
        command,
        capture_output=True,
        check=False,
        cwd=directory,
        env={**os.environ, "SYMBOL": symbol, "REASON": reason},
        text=True,
    )


def _assert_rejected(
    completed: subprocess.CompletedProcess[str], expected_error: str
) -> None:
    """Assert a boundary rejection with exit code 2 and the named error."""
    assert completed.returncode == 2, (
        "Skylos whitelist boundary must reject invalid input with exit code 2"
    )
    assert expected_error in completed.stderr, (
        "Skylos whitelist boundary must name the missing required argument"
    )


@pytest.mark.parametrize(
    ("variables", "expected_error"),
    [
        pytest.param({}, _MISSING_SYMBOL_ERROR, id="missing-symbol"),
        pytest.param({"SYMBOL": "   "}, _MISSING_SYMBOL_ERROR, id="whitespace-symbol"),
        pytest.param({"SYMBOL": "\t"}, _MISSING_SYMBOL_ERROR, id="tab-symbol"),
        pytest.param({"SYMBOL": "handler"}, _MISSING_REASON_ERROR, id="missing-reason"),
        pytest.param(
            {"SYMBOL": "handler", "REASON": "   "},
            _MISSING_REASON_ERROR,
            id="whitespace-reason",
        ),
        pytest.param(
            {"SYMBOL": "handler", "REASON": "\t"},
            _MISSING_REASON_ERROR,
            id="tab-reason",
        ),
    ],
)
def test_skylos_allow_rejects_missing_or_whitespace_values(
    variables: dict[str, str], expected_error: str
) -> None:
    """The whitelist target must reject incomplete input without running Skylos."""
    _assert_rejected(_run_skylos_allow(**variables), expected_error)


@settings(max_examples=10, deadline=None)
@given(value=_WHITESPACE_ONLY_TEXT)
def test_skylos_allow_rejects_generated_whitespace_values(value: str) -> None:
    """Whitespace-only values must be treated as missing for both variables."""
    _assert_rejected(_run_skylos_allow(SYMBOL=value), _MISSING_SYMBOL_ERROR)
    _assert_rejected(
        _run_skylos_allow(SYMBOL="handler", REASON=value), _MISSING_REASON_ERROR
    )


@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(symbol=_SHELL_SENSITIVE_TEXT, reason=_SHELL_SENSITIVE_TEXT)
def test_skylos_allow_forwards_generated_argument_boundaries(
    tmp_path: Path, symbol: str, reason: str
) -> None:
    """The Make boundary must forward each valid whitelist argument exactly."""
    completed = _run_recorded_whitelist(tmp_path, symbol=symbol, reason=reason)

    assert completed.returncode == 0, (
        "Skylos whitelist boundary must accept non-empty shell-sensitive values: "
        f"{completed.stdout}{completed.stderr}"
    )
    recorded_arguments = json.loads(
        (tmp_path / "skylos-arguments.json").read_text(encoding="utf-8")
    )
    assert recorded_arguments == ["whitelist", symbol, "--reason", reason], (
        "Skylos whitelist boundary must quote values and preserve argument order"
    )
