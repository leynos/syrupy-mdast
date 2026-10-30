"""Contracts for published package metadata."""

from __future__ import annotations

import tomllib
from email import message_from_bytes
from importlib import metadata
from pathlib import Path
from zipfile import ZipFile

import pytest
from packaging.requirements import Requirement
from syrupy.extensions.single_file import SingleFileSnapshotExtension, WriteMode

from tests.support.package_boundary import find_javascript_assets
from tests.support.wenmode_installation import Wheelhouse, _run, install_project


def test_declared_ranges_match_installed_metadata() -> None:
    """Package metadata declares the ratified Python and Syrupy ranges."""
    configuration = tomllib.loads(
        (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    )
    _assert_runtime_requirements(configuration["project"]["dependencies"])
    distribution = metadata.metadata("syrupy-mdast")
    assert distribution["Requires-Python"] == ">=3.12", (
        "installed metadata must preserve the supported Python range"
    )
    _assert_runtime_requirements(distribution.get_all("Requires-Dist") or [])
    assert SingleFileSnapshotExtension.file_extension, (
        "installed Syrupy must expose SingleFileSnapshotExtension"
    )
    assert WriteMode.TEXT.value, "installed Syrupy must expose WriteMode.TEXT"
    assert hasattr(SingleFileSnapshotExtension, "_write_mode"), (
        "installed Syrupy must retain the private text-mode hook"
    )


@pytest.mark.parametrize(
    "wenmode_requirement",
    [
        None,
        "wenmode>=0.15.2,<0.16",
        "wenmode==0.15.1",
        "wenmode==0.15.2; python_version > '3'",
        "wenmode[extra]==0.15.2",
    ],
)
def test_runtime_requirement_rejects_unapproved_wenmode(
    wenmode_requirement: str | None,
) -> None:
    """The required dependency cannot be absent, ranged, altered or conditional."""
    requirements = ["syrupy>=5.0.0,<7.0.0"]
    if wenmode_requirement is not None:
        requirements.append(wenmode_requirement)
    with pytest.raises(AssertionError):
        _assert_runtime_requirements(requirements)


def test_package_ships_py_typed_marker(wheelhouse: Wheelhouse, tmp_path: Path) -> None:
    """Built wheels contain every package module and no JavaScript assets."""
    member_names = _wheel_member_names(wheelhouse.project_wheel)
    _assert_required_wheel_members(member_names)
    with ZipFile(wheelhouse.project_wheel) as wheel:
        metadata_path = next(
            name for name in member_names if name.endswith(".dist-info/METADATA")
        )
        wheel_metadata = message_from_bytes(wheel.read(metadata_path))
        _assert_runtime_requirements(wheel_metadata.get_all("Requires-Dist") or [])
    _assert_isolated_wheel_import(wheelhouse, tmp_path)
    _assert_no_javascript_assets(member_names)


def _wheel_member_names(wheel_path: Path) -> set[str]:
    """Return the member names from a built wheel."""
    with ZipFile(wheel_path) as wheel:
        return set(wheel.namelist())


def _assert_required_wheel_members(member_names: set[str]) -> None:
    """Assert that a wheel contains every v1 package member."""
    required_members = {
        "syrupy_mdast/__init__.py",
        "syrupy_mdast/_core/__init__.py",
        "syrupy_mdast/_core/errors.py",
        "syrupy_mdast/_extension.py",
        "syrupy_mdast/py.typed",
    }
    assert required_members <= member_names, (
        "the installed wheel must contain every v1 Python package member"
    )


def _assert_isolated_wheel_import(wheelhouse: Wheelhouse, temporary_path: Path) -> None:
    """Install the shared wheel in isolation and assert its import contract."""
    wheel_python = install_project(
        wheelhouse, "wheel", temporary_path / "wheel-environment"
    )
    _run(
        [
            wheel_python,
            "-I",
            "-c",
            "\n".join((
                "from pathlib import Path",
                "import sys",
                "import syrupy_mdast",
                "from syrupy_mdast import MarkdownAstError as Error",
                "Extension = syrupy_mdast.MarkdownAstSnapshotExtension",
                "module_path = Path(syrupy_mdast.__file__)",
                "assert module_path.is_relative_to(Path(sys.prefix))",
                "expected = {'MarkdownAstError', 'MarkdownAstSnapshotExtension'}",
                "assert set(syrupy_mdast.__all__) == expected",
                "assert Error.__module__ == 'syrupy_mdast._core.errors'",
                "assert Extension.__module__ == 'syrupy_mdast._extension'",
            )),
        ],
        cwd=temporary_path,
        timeout=30,
    )


def _assert_no_javascript_assets(member_names: set[str]) -> None:
    """Assert wheel members exclude JavaScript and TypeScript assets."""
    unexpected_assets = find_javascript_assets(member_names)
    assert not unexpected_assets, f"forbidden wheel assets: {unexpected_assets}"


def _assert_runtime_requirements(requirements: list[str]) -> None:
    """Check both mandatory requirements independently of header order."""
    parsed = [Requirement(value) for value in requirements]
    assert len(parsed) == 2, "Expected len(parsed) == 2"
    by_name = {item.name.lower(): item for item in parsed}
    assert set(by_name) == {"syrupy", "wenmode"}, (
        'Expected set(by_name) == {"syrupy", "wenmode"}'
    )
    assert str(by_name["syrupy"].specifier) == "<7.0.0,>=5.0.0", (
        'Expected str(by_name["syrupy"].specifier) == "<7.0.0,>=5.0.0"'
    )
    assert str(by_name["wenmode"].specifier) == "==0.15.2", (
        'Expected str(by_name["wenmode"].specifier) == "==0.15.2"'
    )
    assert all(
        item.marker is None and not item.extras and item.url is None for item in parsed
    ), "Runtime requirements must be unconditional and have no extras or URLs"
