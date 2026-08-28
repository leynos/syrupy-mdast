"""Contract tests for Skylos dead-code detection in Make and CI.

Skylos is invoked through variables and recipes whose order is significant:
the scanner accepts ``--config-file`` before a scan path, while the standalone
``whitelist`` subcommand must appear immediately after ``skylos``. Skylos also
parses source with its own Python AST, so it must run under Python 3.14 to
understand the project's supported syntax. These tests parse the Makefile with
Makeutil and the workflows with PyYAML, asserting the interface rather than
source text.
"""

from __future__ import annotations

import shlex
import tomllib
import typing as typ

from tests.support.make_contract import (
    REPO_ROOT,
    mapping,
    objects,
    recipe_tokens,
    sole_recipe_rule,
    sole_workflow_step,
    text_sequence,
    variable_tokens,
    workflow_job,
)

_MAKEUTIL_ENVIRONMENT_KEYS: typ.Final = ("MAKEUTIL_REVISION", "MAKEUTIL_TOOLCHAIN")
_MAKEUTIL_INSTALL_TOKENS: typ.Final = (
    "rustup",
    "toolchain",
    "install",
    "${MAKEUTIL_TOOLCHAIN}",
    "--profile",
    "minimal",
    "RUSTFLAGS=-Zpolonius=next",
    "cargo",
    "+${MAKEUTIL_TOOLCHAIN}",
    "install",
    "--git",
    "https://github.com/leynos/makeutil",
    "--rev",
    "${MAKEUTIL_REVISION}",
    "--locked",
    "--force",
    "makeutil",
)
# The current Skylos scan reports no production false positives, so both the
# documented whitelist and the typed entry-point rules are deliberately empty.
# Recording a new exception must extend these sets alongside the
# `skylos-allow` run or entry-point rule that justifies it.
_DOCUMENTED_WHITELIST_NAMES: typ.Final[frozenset[str]] = frozenset()
_RUNTIME_ENTRY_POINT_NAMES: typ.Final[frozenset[str]] = frozenset()
_FULL_SUITE_WORKFLOW_JOBS: typ.Final = (
    (".github/workflows/ci.yml", "lint-test"),
    (".github/workflows/act-validation.yml", "act-validation"),
)
_SKYLOS_LINT_COMMAND: typ.Final = (
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
)
_SKYLOS_CLI_TOKENS: typ.Final = (
    "$(UV_ENV)",
    "$(UV)",
    "tool",
    "run",
    "--python",
    "3.14",
    "--from",
    "skylos==$(SKYLOS_VERSION)",
    "skylos",
)
_SKYLOS_WHITELIST_COMMAND: typ.Final = (
    "flock",
    "$(SKYLOS_WHITELIST_LOCK)",
    "env",
    "$(SKYLOS_CLI)",
    "whitelist",
    "$${SKYLOS_SYMBOL}",
    "--reason",
    "$${SKYLOS_REASON}",
)


def _assert_makeutil_installation(command: object, *, contract: str) -> None:
    """Assert ``command`` installs Makeutil through the shared command shape.

    The expected tokens reference ``${MAKEUTIL_TOOLCHAIN}`` and
    ``${MAKEUTIL_REVISION}`` rather than literal values, so this asserts how
    the parser is installed while leaving the pinned values to the job
    environment.
    """
    assert isinstance(command, str), (
        f"{contract} must provide a Makeutil installation shell command"
    )
    assert (
        tuple(shlex.split(command.replace("\\\n", ""))) == _MAKEUTIL_INSTALL_TOKENS
    ), f"{contract} must install Makeutil through the shared command shape"


def test_lint_recipe_runs_the_production_dead_code_gate() -> None:
    """`make lint` must scan production code with Skylos's strict gate."""
    test_prerequisites = text_sequence(
        sole_recipe_rule("test").get("prerequisites"),
        subject="test target prerequisites",
    )
    assert "makeutil" in test_prerequisites, (
        "Make test prerequisite contract must require makeutil"
    )
    skylos_version = variable_tokens("SKYLOS_VERSION")
    assert len(skylos_version) == 1, (
        "Skylos version contract must declare exactly one release token for "
        f"$(SKYLOS_CLI) to pin, got {skylos_version!r}"
    )
    assert skylos_version[0], "Skylos version contract must declare a non-empty release"
    assert variable_tokens("SKYLOS_PRODUCTION_TARGETS") == ("syrupy_mdast",), (
        "Skylos production-target contract must scan syrupy_mdast"
    )
    assert variable_tokens("SKYLOS_EXCLUDE_FOLDERS") == ("tests",), (
        "Skylos exclusion contract must omit the tests tree"
    )
    skylos_commands = [
        command
        for command in recipe_tokens("lint-python")
        if command[:1] == ("$(SKYLOS)",)
    ]

    assert skylos_commands == [_SKYLOS_LINT_COMMAND], (
        "Skylos lint command contract must scan production dead code strictly"
    )


def test_whitelist_target_uses_the_command_only_skylos_cli() -> None:
    """`skylos whitelist` must precede the name and carry no scan options."""
    assert variable_tokens("SKYLOS_CLI") == _SKYLOS_CLI_TOKENS, (
        "Skylos CLI contract must pin Python 3.14 and its tool release"
    )
    assert variable_tokens("SKYLOS") == (
        "$(SKYLOS_CLI)",
        "--config-file",
        "pyproject.toml",
    ), "Skylos scan command contract must add only the configuration file"
    assert variable_tokens("SKYLOS_WHITELIST_LOCK") == (".skylos-whitelist.lock",), (
        "Skylos whitelist contract must use a repository-local lock"
    )

    whitelist_commands = [
        command
        for command in recipe_tokens("skylos-allow")
        if command[:4] == _SKYLOS_WHITELIST_COMMAND[:4]
    ]
    assert whitelist_commands == [_SKYLOS_WHITELIST_COMMAND], (
        "Skylos whitelist command contract must lock and dispatch before --reason"
    )


def test_skylos_configuration_requires_strict_documented_exceptions() -> None:
    """Strict gating must hold, and every exception must carry a reason."""
    with (REPO_ROOT / "pyproject.toml").open("rb") as configuration_file:
        configuration = tomllib.load(configuration_file)

    tool = mapping(configuration.get("tool"), subject="tool configuration")
    skylos = mapping(tool.get("skylos"), subject="Skylos configuration")
    gate = mapping(skylos.get("gate"), subject="Skylos gate configuration")
    assert gate.get("strict") is True, (
        "Skylos gate configuration must enable strict mode"
    )

    dead_code = mapping(
        skylos.get("dead_code", {}), subject="Skylos dead-code configuration"
    )
    entry_points = objects(
        dead_code.get("entrypoints", []), subject="Skylos entry points"
    )
    entry_point_names = frozenset(
        name
        for entry_point in entry_points
        for name in text_sequence(
            entry_point.get("full_name"), subject="entry-point name"
        )
    )
    assert entry_point_names == _RUNTIME_ENTRY_POINT_NAMES, (
        "Skylos entry-point contract must match the recorded runtime exclusions"
    )
    for entry_point in entry_points:
        assert isinstance(entry_point.get("type"), str), (
            "Skylos entry-point contract must classify each exclusion with a type"
        )
        reason = entry_point.get("reason")
        assert isinstance(reason, str), (
            "Skylos entry-point contract must provide a textual reason"
        )
        assert reason, "Skylos entry-point contract must provide a non-empty reason"

    whitelist = mapping(
        skylos.get("whitelist", {}), subject="Skylos whitelist configuration"
    )
    documented = mapping(
        whitelist.get("documented", {}), subject="Skylos documented whitelist"
    )
    assert frozenset(documented) == _DOCUMENTED_WHITELIST_NAMES, (
        "Skylos documented-whitelist contract must match the recorded exceptions"
    )
    for name, reason in documented.items():
        assert isinstance(reason, str), (
            f"Skylos documented-whitelist entry {name!r} must record a textual reason"
        )
        assert reason, (
            f"Skylos documented-whitelist entry {name!r} must record a non-empty reason"
        )


def test_ci_runs_the_lint_target_with_skylos() -> None:
    """CI must run the shared lint target that includes the Skylos gate."""
    lint_step = sole_workflow_step(
        ".github/workflows/ci.yml",
        "lint-test",
        "Run lint, including Skylos dead-code detection",
    )
    assert lint_step.get("run") == "make lint", (
        "CI lint-step contract must invoke the shared make lint target"
    )


def test_full_suite_workflows_provision_the_makefile_parser_identically() -> None:
    """Every job running the full pytest suite must install Makeutil alike.

    The contract is agreement, not a particular revision: each full-suite job
    must declare both Makeutil pins, install through the same command shape,
    and resolve to the same values as its sibling jobs. Bumping the parser
    then requires updating every job together, while leaving the choice of
    revision and toolchain free.
    """
    declared: dict[str, dict[str, str]] = {}
    for workflow_path, job_name in _FULL_SUITE_WORKFLOW_JOBS:
        job = workflow_job(workflow_path, job_name)
        environment = mapping(
            job.get("env"), subject=f"{workflow_path} Makeutil environment"
        )
        for key in _MAKEUTIL_ENVIRONMENT_KEYS:
            value = environment.get(key)
            assert isinstance(value, str), (
                f"{workflow_path} {job_name} must declare {key} as a string so "
                "the parser install is reproducible"
            )
            assert value, f"{workflow_path} {job_name} must declare a non-empty {key}"
            declared.setdefault(key, {})[f"{workflow_path}:{job_name}"] = value

        parser_step = sole_workflow_step(
            workflow_path, job_name, "Install Makefile parser"
        )
        _assert_makeutil_installation(
            parser_step.get("run"),
            contract=f"{workflow_path} {job_name} Makeutil-install contract",
        )

    for key, values_by_job in declared.items():
        assert len(set(values_by_job.values())) == 1, (
            f"every full-suite job must provision the same {key}; found "
            f"{values_by_job!r}"
        )
