"""Execution-boundary tests for the `lint` and `typecheck` Make targets.

The structural contracts in ``tests/test_lint_pipeline_contract.py`` assert
what the Makefile *declares*. These tests assert what Make actually *does*:
that running a target expands its variables, dispatches each tier in order,
and stops at the first failure.

No real tool runs. The Makefile routes every tier through ``$(UV)``, so
overriding that single variable on the ``make`` command line redirects the
whole pipeline to a recorder script while leaving each tier's own flags to
expand normally. Each target runs with ``make -f <repository Makefile>`` from
an isolated temporary directory, so production behaviour is untouched and the
``build`` prerequisite resolves against a throwaway ``pyproject.toml``. The
recorder itself lives in ``tests/support/make_recorder.py``.
"""

from __future__ import annotations

import typing as typ

import pytest

from tests.support.make_contract import variable_tokens
from tests.support.make_recorder import (
    PYPY_PYLINT,
    arguments_for,
    entry_points,
    invocations,
    run_make,
)

if typ.TYPE_CHECKING:
    from pathlib import Path


_RUFF: typ.Final = "ruff"
_INTERROGATE: typ.Final = "interrogate"
_PYPY_PYLINT: typ.Final = PYPY_PYLINT
_DF12_PYLINT: typ.Final = "pylint"
_AMBRLEAKS: typ.Final = "ambrleaks"
_SKYLOS: typ.Final = "skylos"
_TY: typ.Final = "ty"
# The order `lint-python` must dispatch its tiers in.
_LINT_TIERS: typ.Final = (
    _RUFF,
    _INTERROGATE,
    _PYPY_PYLINT,
    _DF12_PYLINT,
    _AMBRLEAKS,
    _SKYLOS,
)
# Static flags each tier carries, ahead of its expanded target list.
_RUFF_FLAGS: typ.Final = ("check",)
_INTERROGATE_FLAGS: typ.Final = ("--fail-under", "100")
_PYPY_PYLINT_FLAGS: typ.Final = ("--load-plugins=",)
_DF12_PYLINT_FLAGS: typ.Final = ("--disable=all", "--load-plugins=df12_python_lints")
_SKYLOS_LEADING_FLAGS: typ.Final = ("--config-file", "pyproject.toml")
_SKYLOS_TRAILING_FLAGS: typ.Final = (
    "--category",
    "dead_code",
    "--gate",
    "--format",
    "concise",
    "--no-upload",
    "--no-provenance",
    "--no-grep-verify",
)
_TY_VERSION_ARGUMENTS: typ.Final = ("--version",)
# Tokens that uniquely identify one invocation, used to tell the recorder
# which call should fail. Matching tokens keeps the recorder free of any
# classification logic that would have to be kept in step with this module.
_FAILURE_TOKENS: typ.Final = {
    _RUFF: (_RUFF,),
    _INTERROGATE: (_INTERROGATE,),
    _PYPY_PYLINT: ("--load-plugins=",),
    _DF12_PYLINT: ("--load-plugins=df12_python_lints",),
    _AMBRLEAKS: (_AMBRLEAKS,),
    _SKYLOS: (_SKYLOS,),
}


def _expected_tier_arguments() -> dict[str, tuple[str, ...]]:
    """Return the arguments each tier should receive, expanded by Make.

    Target lists and the df12 message set are read from the Makefile rather
    than restated, so this asserts that execution matches the declaration
    without pinning either value.

    Returns
    -------
    dict
        Entry-point name mapped to its expected arguments.
    """
    python_targets = variable_tokens("PYTHON_TARGETS")
    pylint_targets = variable_tokens("PYLINT_TARGETS")
    if pylint_targets == ("$(PYTHON_TARGETS)",):
        pylint_targets = python_targets
    messages = variable_tokens("DF12_PYLINT_MESSAGES")
    assert len(messages) == 1, (
        f"DF12_PYLINT_MESSAGES must hold one message list, got {messages!r}"
    )
    return {
        _RUFF: _RUFF_FLAGS + python_targets,
        _INTERROGATE: _INTERROGATE_FLAGS + python_targets,
        _PYPY_PYLINT: _PYPY_PYLINT_FLAGS + pylint_targets,
        _DF12_PYLINT: (
            *_DF12_PYLINT_FLAGS,
            f"--enable={messages[0]}",
            *pylint_targets,
        ),
        _AMBRLEAKS: ("tests",),
        _SKYLOS: (
            *_SKYLOS_LEADING_FLAGS,
            *variable_tokens("SKYLOS_PRODUCTION_TARGETS"),
            "--exclude",
            *variable_tokens("SKYLOS_EXCLUDE_FOLDERS"),
            *_SKYLOS_TRAILING_FLAGS,
        ),
    }


def test_lint_dispatches_through_lint_python(tmp_path: Path) -> None:
    """`make lint` must run the same tiers as `make lint-python`."""
    lint_directory = tmp_path / "lint"
    lint_python_directory = tmp_path / "lint-python"
    lint_directory.mkdir()
    lint_python_directory.mkdir()

    run_make(lint_directory, "lint", check=True)
    run_make(lint_python_directory, "lint-python", check=True)

    assert entry_points(lint_directory) == entry_points(lint_python_directory), (
        "`make lint` must delegate to `lint-python` and dispatch identical tiers"
    )


def test_lint_python_executes_every_tier_in_order(tmp_path: Path) -> None:
    """`make lint-python` must dispatch the six tiers in Makefile order."""
    run_make(tmp_path, "lint-python", check=True)

    assert entry_points(tmp_path) == _LINT_TIERS, (
        "lint-python must execute Ruff, Interrogate, the PyPy Pylint pass, the "
        "df12 Pylint pass, ambrleaks, and Skylos, in that order"
    )


def test_lint_python_expands_each_tier_argument_list(tmp_path: Path) -> None:
    """Each tier must receive its fully expanded Makefile arguments."""
    run_make(tmp_path, "lint-python", check=True)

    expected = _expected_tier_arguments()
    for entry_point, arguments in expected.items():
        assert arguments_for(tmp_path, entry_point) == arguments, (
            f"the {entry_point!r} tier must receive its expanded Makefile arguments"
        )


def test_pypy_pylint_tier_runs_with_plugins_disabled(tmp_path: Path) -> None:
    """The PyPy pass must pass `--load-plugins=`, which needs CPython."""
    run_make(tmp_path, "lint-python", check=True)

    assert "--load-plugins=" in arguments_for(tmp_path, _PYPY_PYLINT), (
        "the PyPy Pylint tier must execute with `--load-plugins=` so the df12 "
        "plugin is not loaded under PyPy"
    )


def test_df12_pylint_tier_runs_with_the_configured_message_set(
    tmp_path: Path,
) -> None:
    """The df12 pass must disable defaults and enable its configured messages."""
    run_make(tmp_path, "lint-python", check=True)

    arguments = arguments_for(tmp_path, _DF12_PYLINT)
    messages = variable_tokens("DF12_PYLINT_MESSAGES")
    for expected in (
        "--disable=all",
        "--load-plugins=df12_python_lints",
        f"--enable={messages[0]}",
    ):
        assert expected in arguments, (
            f"the df12 Pylint tier must execute with {expected!r}"
        )


def test_typecheck_executes_ty_twice_in_order(tmp_path: Path) -> None:
    """`make typecheck` must report the ty version before checking sources."""
    run_make(tmp_path, "typecheck", check=True)

    recorded = invocations(tmp_path)
    assert tuple(name for name, _ in recorded) == (_TY, _TY), (
        "typecheck must execute ty exactly twice"
    )
    assert recorded[0][1] == _TY_VERSION_ARGUMENTS, (
        "typecheck must report the pinned ty version first"
    )
    assert recorded[1][1] == ("check", *variable_tokens("PYTHON_TARGETS")), (
        "typecheck must then check the configured Python targets"
    )


@pytest.mark.parametrize(
    "failing_tier",
    [
        pytest.param(_RUFF, id="early-tier"),
        pytest.param(_DF12_PYLINT, id="middle-tier"),
        pytest.param(_SKYLOS, id="late-tier"),
    ],
)
def test_lint_python_stops_at_the_first_failing_tier(
    tmp_path: Path, failing_tier: str
) -> None:
    """A failing tier must fail the target and prevent every later tier."""
    completed = run_make(
        tmp_path,
        "lint-python",
        check=False,
        fail_tokens=_FAILURE_TOKENS[failing_tier],
    )

    assert completed.returncode != 0, (
        f"a failing {failing_tier!r} tier must fail `make lint-python`: "
        f"{completed.stdout}{completed.stderr}"
    )
    expected = _LINT_TIERS[: _LINT_TIERS.index(failing_tier) + 1]
    assert entry_points(tmp_path) == expected, (
        f"`make lint-python` must stop after the failing {failing_tier!r} tier "
        "and dispatch no later tier"
    )


@pytest.mark.parametrize(
    "failing_token",
    [
        pytest.param("--version", id="version-probe"),
        pytest.param("check", id="check-run"),
    ],
)
def test_typecheck_fails_when_either_ty_command_fails(
    tmp_path: Path, failing_token: str
) -> None:
    """Either ty invocation failing must fail `make typecheck`."""
    completed = run_make(
        tmp_path, "typecheck", check=False, fail_tokens=(_TY, failing_token)
    )

    assert completed.returncode != 0, (
        f"a failing `ty {failing_token}` must fail `make typecheck`: "
        f"{completed.stdout}{completed.stderr}"
    )
