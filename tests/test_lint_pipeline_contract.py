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

import tomllib
import typing as typ

from tests.support.make_contract import REPO_ROOT, recipe_tokens, variable_tokens

_DF12_DISTRIBUTION: typ.Final = "df12-python-lints"
_DF12_SOURCE_TEMPLATE: typ.Final = (
    "git+https://github.com/leynos/df12-python-lints.git@$(DF12_PYTHON_LINTS_REF)"
)

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


def test_df12_python_lints_revision_agrees_across_invocation_sites() -> None:
    """The Makefile and pyproject.toml must request the same plugin revision.

    The lint gate resolves the plugin through the Makefile's
    ``DF12_PYTHON_LINTS_REF``, while ``uv sync`` resolves it through the git
    reference in the dev dependency group. If the two drift, the linted
    ruleset depends on which entry point ran, so this asserts they agree
    without constraining which revision is chosen.
    """
    makefile_tokens = variable_tokens("DF12_PYTHON_LINTS_REF")
    assert len(makefile_tokens) == 1, (
        f"DF12_PYTHON_LINTS_REF must hold a single revision, got {makefile_tokens!r}"
    )
    makefile_revision = makefile_tokens[0]

    pyproject = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    dev_dependencies: list[str] = pyproject["dependency-groups"]["dev"]
    specifiers = [
        specifier
        for specifier in dev_dependencies
        if specifier.startswith(f"{_DF12_DISTRIBUTION} @ ")
    ]
    assert len(specifiers) == 1, (
        f"expected exactly one {_DF12_DISTRIBUTION!r} entry in the dev "
        f"dependency group, found {len(specifiers)}"
    )
    _, _, requirement_url = specifiers[0].partition(" @ ")
    _, separator, pyproject_revision = requirement_url.strip().rpartition("@")
    assert separator, (
        f"the {_DF12_DISTRIBUTION!r} dev dependency must request an explicit "
        f"git revision, got {requirement_url.strip()!r}"
    )

    assert makefile_revision == pyproject_revision, (
        f"{_DF12_DISTRIBUTION} is requested at {makefile_revision!r} by the "
        f"Makefile but {pyproject_revision!r} by pyproject.toml; the lint gate "
        "and the synced environment must resolve the same plugin revision"
    )


def test_df12_python_lints_source_is_built_from_the_shared_revision() -> None:
    """The plugin URL must interpolate the ref rather than inline a revision."""
    assert variable_tokens("DF12_PYTHON_LINTS") == (_DF12_SOURCE_TEMPLATE,), (
        "df12-python-lints source contract must build its URL from "
        "$(DF12_PYTHON_LINTS_REF) so the Makefile has a single revision site"
    )
