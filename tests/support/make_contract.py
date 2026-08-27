"""Structured Makefile and workflow parsing for contract tests.

Contract tests must assert the Make and CI interfaces without depending on
whitespace or nearby source text, so this module parses the Makefile with the
pinned ``makeutil`` binary (structured rules and variables as JSON) and CI
workflows with PyYAML. Reports are parsed afresh on every call; nothing is
cached at module level, so the suite never observes stale parse results.

Examples
--------
>>> variable_tokens("SKYLOS_VERSION")
('4.33.2',)
"""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess  # ruff: ignore[suspicious-subprocess-import] - contract tests invoke the pinned parser.
import typing as typ
from pathlib import Path

import yaml

REPO_ROOT: typ.Final = Path(__file__).resolve().parents[2]
_MAKEUTIL_COMMAND: typ.Final = ("makeutil", "parse", "Makefile")


def makefile_report() -> dict[str, object]:
    """Return Makeutil's complete, successfully parsed Makefile report."""
    completed = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] - fixed parser command.
        _MAKEUTIL_COMMAND,
        capture_output=True,
        check=True,
        cwd=REPO_ROOT,
        text=True,
    )
    report = typ.cast("dict[str, object]", json.loads(completed.stdout))
    parse = mapping(report.get("parse"), subject="parse report")
    assert parse.get("status") == "complete", (
        f"makeutil did not complete the Makefile parse: {parse!r}"
    )
    return report


def mapping(value: object, *, subject: str) -> dict[str, object]:
    """Return a JSON object, naming the unexpected ``subject`` on failure."""
    assert isinstance(value, dict), f"expected {subject} to be a JSON object"
    return typ.cast("dict[str, object]", value)


def objects(value: object, *, subject: str) -> list[dict[str, object]]:
    """Return a JSON object array, naming the unexpected ``subject`` on failure."""
    assert isinstance(value, list), f"expected {subject} to be a JSON array"
    return [mapping(item, subject=f"{subject} item") for item in value]


def text_sequence(value: object, *, subject: str) -> tuple[str, ...]:
    """Return a JSON string array, naming the unexpected ``subject`` on failure."""
    assert isinstance(value, list), f"expected {subject} to be a JSON array"
    assert all(isinstance(item, str) for item in value), (
        f"expected {subject} to contain only JSON strings"
    )
    return tuple(typ.cast("list[str]", value))


def sole_variable(name: str) -> dict[str, object]:
    """Return Makeutil's sole variable fact for ``name``."""
    variables = objects(makefile_report().get("variables"), subject="variables")
    matches = [variable for variable in variables if variable.get("name") == name]
    assert len(matches) == 1, (
        f"expected one Makefile variable named {name!r}, found {len(matches)}"
    )
    return matches[0]


def sole_recipe_rule(target: str) -> dict[str, object]:
    """Return the only parsed rule for ``target`` that has recipes."""
    rules = objects(makefile_report().get("rules"), subject="rules")
    matches = [
        rule
        for rule in rules
        if target in text_sequence(rule.get("targets"), subject="rule targets")
        and objects(rule.get("recipes"), subject="rule recipes")
    ]
    assert len(matches) == 1, (
        f"expected one recipe-bearing Makefile rule named {target!r}, found "
        f"{len(matches)}"
    )
    return matches[0]


def variable_tokens(name: str) -> tuple[str, ...]:
    """Return shell-like tokens from Makeutil's raw variable value."""
    value = sole_variable(name).get("raw_value")
    assert isinstance(value, str), f"expected {name!r} to have a string value"
    return tuple(shlex.split(value))


def recipe_tokens(target: str) -> tuple[tuple[str, ...], ...]:
    """Return shell-like tokens for every recipe in ``target``."""
    recipes = objects(
        sole_recipe_rule(target).get("recipes"), subject=f"{target} recipes"
    )
    return tuple(
        tuple(shlex.split(recipe_text))
        for recipe in recipes
        if isinstance(recipe_text := recipe.get("text"), str)
    )


def make_executable() -> str:
    """Return the absolute path to the required Make executable."""
    executable = shutil.which("make")
    assert executable is not None, "Make boundary contract tests require make"
    return executable


def workflow_job(workflow_path: str, job_name: str) -> dict[str, object]:
    """Return the named job from a repository workflow."""
    workflow = yaml.safe_load((REPO_ROOT / workflow_path).read_text(encoding="utf-8"))
    workflow_mapping = mapping(workflow, subject=f"{workflow_path} workflow")
    jobs = mapping(workflow_mapping.get("jobs"), subject=f"{workflow_path} jobs")
    return mapping(jobs.get(job_name), subject=f"{workflow_path} job {job_name!r}")


def sole_workflow_step(
    workflow_path: str,
    job_name: str,
    step_name: str,
) -> dict[str, object]:
    """Return the sole step named ``step_name`` from a workflow job."""
    job = workflow_job(workflow_path, job_name)
    steps = objects(job.get("steps"), subject=f"{workflow_path} job {job_name!r} steps")
    matches = [step for step in steps if step.get("name") == step_name]
    assert len(matches) == 1, (
        f"expected one {step_name!r} step in {workflow_path} job {job_name!r}, "
        f"found {len(matches)}"
    )
    return matches[0]
