"""Contract tests for the Python lint pipeline wired into `make lint-python`.

`make lint` is the single entry point CI and contributors share, so the tiers
it runs — and the environment each tier runs in — are part of the repository's
observable interface. These tests parse the Makefile with Makeutil and assert
that interface structurally, rather than executing the linters.

The environment assertions matter as much as the ordering. Every tier that
pins a Python version other than the project baseline must run through
`uv tool run`, which builds an isolated, ephemeral environment. A
project-aware `uv run --python <version>` would instead replace the project
`.venv` with that interpreter, and because CI runs `make lint` before
`make typecheck`, `make audit`, and coverage generation, those later steps
would silently reuse the replaced interpreter.
"""

from __future__ import annotations

import typing as typ

from tests.support.make_contract import recipe_tokens, variable_tokens

_EXPECTED_LINT_PIPELINE: typ.Final = (
    ("$(RUFF)", "check", "$(PYTHON_TARGETS)"),
    (
        "$(UV_ENV)",
        "$(UV)",
        "run",
        "interrogate",
        "--fail-under",
        "100",
        "$(PYTHON_TARGETS)",
    ),
    ("$(PYLINT)", "$(PYLINT_TARGETS)"),
    ("$(DF12_PYLINT)", "$(PYLINT_TARGETS)"),
    ("$(AMBRLEAKS)", "tests"),
    (
        "$(SKYLOS)",
        "$(SKYLOS_PRODUCTION_TARGETS)",
        "--exclude",
        "$(SKYLOS_EXCLUDE_FOLDERS)",
        "--category",
        "dead_code",
        "--gate",
        "--format",
        "concise",
        "--no-upload",
        "--no-provenance",
        "--no-grep-verify",
    ),
)
# Each tier that pins its own interpreter must build an isolated environment.
_ISOLATED_TOOL_MACROS: typ.Final = ("PYLINT", "DF12_PYLINT", "AMBRLEAKS", "SKYLOS_CLI")
_COMMIT_SHA_LENGTH: typ.Final = 40
_HEX_DIGITS: typ.Final = frozenset("0123456789abcdef")
_DF12_PYLINT_TOKENS: typ.Final = (
    "$(UV_ENV)",
    "$(UV)",
    "tool",
    "run",
    "--python",
    "$(DF12_PYTHON)",
    "--from",
    "$(DF12_PYTHON_LINTS)",
    "pylint",
    "--disable=all",
    "--load-plugins=df12_python_lints",
    "--enable=$(DF12_PYLINT_MESSAGES)",
)
_PYLINT_TOKENS: typ.Final = (
    "$(UV_ENV)",
    "$(UV)",
    "tool",
    "run",
    "--python",
    "$(PYLINT_PYTHON)",
    "--from",
    "$(PYLINT_PYPY_SHIM)",
    "pylint-pypy",
    "--load-plugins=",
)


def test_lint_python_runs_every_tier_in_order() -> None:
    """`lint-python` must run all six lint tiers, in the documented order."""
    assert recipe_tokens("lint-python") == _EXPECTED_LINT_PIPELINE, (
        "Lint pipeline contract must run Ruff, Interrogate, the PyPy Pylint "
        "pass, the df12 Pylint pass, ambrleaks, and the Skylos gate in order"
    )


def test_interpreter_pinning_tiers_use_isolated_tool_environments() -> None:
    """Version-pinned tiers must not replace the project virtual environment."""
    for macro in _ISOLATED_TOOL_MACROS:
        tokens = variable_tokens(macro)
        assert "run" in tokens, f"{macro} contract must invoke a uv run variant"
        run_index = tokens.index("run")
        assert tokens[run_index - 1] == "tool", (
            f"{macro} must use `uv tool run` for an isolated environment; a "
            "project-aware `uv run --python ...` replaces the project .venv "
            "and leaks that interpreter into later gates"
        )


def test_df12_pylint_pass_loads_the_plugin_with_its_message_set() -> None:
    """The df12 pass must disable defaults and enable only its own messages."""
    assert variable_tokens("DF12_PYLINT") == _DF12_PYLINT_TOKENS, (
        "df12 Pylint contract must load the plugin from the pinned source and "
        "enable exactly the configured message set"
    )


def test_pypy_pylint_pass_runs_without_plugins() -> None:
    """The PyPy-backed pass must disable plugins, which need CPython."""
    assert variable_tokens("PYLINT") == _PYLINT_TOKENS, (
        "PyPy Pylint contract must run the shim with plugins disabled"
    )


def test_df12_python_lints_is_pinned_to_an_immutable_revision() -> None:
    """The plugin source must be a commit SHA, not a movable tag or branch."""
    tokens = variable_tokens("DF12_PYTHON_LINTS_REF")
    assert len(tokens) == 1, (
        f"DF12_PYTHON_LINTS_REF must hold a single revision, got {tokens!r}"
    )
    revision = tokens[0]
    assert len(revision) == _COMMIT_SHA_LENGTH, (
        "df12-python-lints must be pinned to a full 40-character commit SHA so "
        f"the resolved code cannot change under the pin, got {revision!r}"
    )
    assert all(character in _HEX_DIGITS for character in revision), (
        "df12-python-lints must be pinned to a hexadecimal commit SHA, not a "
        f"movable tag or branch, got {revision!r}"
    )
