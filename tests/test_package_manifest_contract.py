"""Contracts for published package metadata."""

from __future__ import annotations

import subprocess  # ruff: ignore[suspicious-subprocess-import] -- fixed local wheel-build contract.
import sys
import tomllib
from email import message_from_bytes
from importlib import metadata
from pathlib import Path
from shutil import which
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import pytest
from packaging.requirements import Requirement
from syrupy.extensions.single_file import SingleFileSnapshotExtension, WriteMode

from tests.support.package_boundary import find_javascript_assets


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


def test_package_ships_py_typed_marker() -> None:
    """Built wheels contain every package module and no JavaScript assets."""
    repository_root = Path(__file__).parents[1]
    uv_executable = _require_uv()
    with TemporaryDirectory() as temporary_directory:
        temporary_path = Path(temporary_directory)
        wheel_path = _build_wheel(uv_executable, repository_root, temporary_path)
        member_names = _wheel_member_names(wheel_path)
        _assert_required_wheel_members(member_names)
        with ZipFile(wheel_path) as wheel:
            metadata_path = next(
                name for name in member_names if name.endswith(".dist-info/METADATA")
            )
            wheel_metadata = message_from_bytes(wheel.read(metadata_path))
            _assert_runtime_requirements(wheel_metadata.get_all("Requires-Dist") or [])
        _assert_isolated_wheel_import(uv_executable, wheel_path, temporary_path)
    _assert_no_javascript_assets(member_names)


def _require_uv() -> str:
    """Return the required local uv executable."""
    uv_executable = which("uv")
    assert uv_executable is not None, "the wheel contract requires uv on PATH"
    return uv_executable


def _build_wheel(
    uv_executable: str, repository_root: Path, output_directory: Path
) -> Path:
    """Build one wheel in the supplied output directory."""
    subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- fixed local build command.
        [uv_executable, "build", "--wheel", "--out-dir", output_directory],
        check=True,
        cwd=repository_root,
    )
    return next(output_directory.glob("*.whl"))


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


def _assert_isolated_wheel_import(
    uv_executable: str, wheel_path: Path, temporary_path: Path
) -> None:
    """Install a wheel in isolation and assert its public import contract."""
    virtual_environment = temporary_path / "wheel-environment"
    subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- fixed local environment command.
        [uv_executable, "venv", "--python", sys.executable, virtual_environment],
        check=True,
        cwd=temporary_path,
    )
    wheel_python = (
        virtual_environment / "Scripts" / "python.exe"
        if sys.platform == "win32"
        else virtual_environment / "bin" / "python"
    )
    subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- fixed local wheel-install command.
        [uv_executable, "pip", "install", "--python", wheel_python, wheel_path],
        check=True,
        cwd=temporary_path,
    )
    subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- fixed isolated import contract.
        [
            wheel_python,
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
        check=True,
        cwd=temporary_path,
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
