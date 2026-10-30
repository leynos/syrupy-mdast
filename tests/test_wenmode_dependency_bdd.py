"""Behavioural contracts for isolated Wenmode package installations."""

from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.support.package_boundary import find_javascript_assets
from tests.support.wenmode_installation import (
    Wheelhouse,
    install_and_probe,
    prepare_wheelhouse,
)
from tests.support.wenmode_offline_install import install_without_wenmode

_FEATURE = Path(__file__).parent / "features" / "wenmode_dependency.feature"
scenarios(str(_FEATURE))


@pytest.fixture(scope="session")
def wheelhouse(tmp_path_factory: pytest.TempPathFactory) -> Wheelhouse:
    """Prepare one local wheelhouse shared by every scenario in the worker."""
    temporary_path = tmp_path_factory.mktemp("wenmode-wheelhouse")
    return prepare_wheelhouse(temporary_path)


@pytest.fixture(scope="session")
def parser_results(
    wheelhouse: Wheelhouse, tmp_path_factory: pytest.TempPathFactory
) -> dict[str, tuple[str, list[object]]]:
    """Run fresh wheel and editable probes and require identical AST results."""
    temporary_path = tmp_path_factory.mktemp("wenmode-parser-modes")
    results = {}
    for mode in ("wheel", "editable"):
        output, _stderr = install_and_probe(wheelhouse, mode, temporary_path / mode)
        ast_line = next(line for line in output.splitlines() if line.startswith("["))
        results[mode] = output, json.loads(ast_line)
    assert results["wheel"][1] == results["editable"][1], (
        "wheel and editable Wenmode installs must return the same ASTs"
    )
    return results


@pytest.fixture
def scenario_state() -> dict[str, object]:
    """Hold evidence produced by the current behavioural scenario."""
    return {}


@given(
    parsers.parse("a fresh {mode} installation from the prepared local wheelhouse"),
    target_fixture="installation_mode",
)
def fresh_installation(mode: str) -> str:
    """Select the requested independent installation mode."""
    assert mode in {"wheel", "editable"}, (
        f"unsupported Wenmode installation mode: {mode}"
    )
    return mode


@given("JavaScript execution and network access are denied")
def isolation_contract_is_checked() -> None:
    """Rely on the child probe audit-hook controls before parsing."""


@when("the reviewed GitHub parser parses the smoke documents")
def parse_smoke_documents(
    installation_mode: str,
    parser_results: dict[str, tuple[str, list[object]]],
    scenario_state: dict[str, object],
) -> None:
    """Run the real parser in a fresh offline environment and external cwd."""
    output, _ast = parser_results[installation_mode]
    scenario_state.update(mode=installation_mode, output=output)


@then("Wenmode version 0.15.2 is imported from that environment")
def wenmode_version_and_origin(
    scenario_state: dict[str, object],
) -> None:
    """Require the probe to verify the installed version and import origin."""
    assert "wenmode=0.15.2" in str(scenario_state["output"]), (
        "the isolated probe must import Wenmode 0.15.2"
    )


@then("the expected root and child semantics are returned")
def parsed_ast_semantics(scenario_state: dict[str, object]) -> None:
    """Require empty, heading, and task-list parser results to pass assertions."""
    output = str(scenario_state["output"])
    assert "isolation=passed" in output, "the isolated parser probe must pass"
    assert str(scenario_state["mode"]) in output, (
        "the probe output must identify its installation mode"
    )
    ast_results = json.loads(
        next(line for line in output.splitlines() if line.startswith("["))
    )
    assert ast_results[0] == {"type": "root", "children": []}, (
        "empty Markdown must produce a root with no children"
    )
    assert ast_results[1]["children"][0]["depth"] == 1, (
        "the heading smoke document must produce a depth-one heading"
    )
    task_items = ast_results[2]["children"][0]["children"]
    assert [item["checked"] for item in task_items] == [True, False], (
        "the task-list smoke document must preserve checked states"
    )


@given(
    "a local wheelhouse without Wenmode and an empty installer cache",
    target_fixture="missing_dependency_wheelhouse",
)
def wheelhouse_without_dependency(wheelhouse: Wheelhouse) -> Wheelhouse:
    """Use the real project wheel while withholding the Wenmode wheel."""
    return wheelhouse


@when("a fresh wheel installation is attempted offline")
def attempt_offline_install(
    missing_dependency_wheelhouse: Wheelhouse,
    tmp_path: Path,
    scenario_state: dict[str, object],
) -> None:
    """Attempt installation with an independently empty uv cache."""
    scenario_state["failure"] = install_without_wenmode(
        missing_dependency_wheelhouse, tmp_path / "missing-wenmode-environment"
    )


@then("installation fails because Wenmode cannot be resolved")
def missing_wenmode_is_named(scenario_state: dict[str, object]) -> None:
    """Require the failed offline resolver to name its missing dependency."""
    assert "wenmode" in str(scenario_state["failure"]).lower(), (
        "the offline installation failure must name the missing Wenmode wheel"
    )


@given(
    "a synthetic wheel containing a nested TypeScript file",
    target_fixture="synthetic_wheel",
)
def synthetic_wheel_with_typescript(tmp_path: Path) -> Path:
    """Create a ZIP archive with one forbidden nested TypeScript member."""
    synthetic_wheel = tmp_path / "synthetic.whl"
    with ZipFile(synthetic_wheel, "w") as archive:
        archive.writestr("example-1.dist-info/METADATA", "Name: example\nVersion: 1\n")
        archive.writestr("example/vendor/parser/index.ts", "export {};\n")
    return synthetic_wheel


@when("the Python-only archive contract is checked")
def inspect_synthetic_wheel(
    synthetic_wheel: Path, scenario_state: dict[str, object]
) -> None:
    """Run the same archive member inspection used for release wheels."""
    with ZipFile(synthetic_wheel) as archive:
        scenario_state["forbidden_assets"] = find_javascript_assets(archive.namelist())


@then("the forbidden asset is identified")
def nested_typescript_is_rejected(scenario_state: dict[str, object]) -> None:
    """Require the exact synthetic member to be rejected."""
    assert scenario_state["forbidden_assets"] == ["example/vendor/parser/index.ts"], (
        "the archive contract must identify the nested TypeScript asset"
    )
