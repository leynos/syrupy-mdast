"""Contracts for published package metadata."""

from __future__ import annotations

import subprocess  # ruff: ignore[suspicious-subprocess-import] -- fixed local wheel-build contract.
import tomllib
from importlib import metadata
from pathlib import Path
from shutil import which
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from syrupy.extensions.single_file import SingleFileSnapshotExtension, WriteMode


def test_declared_ranges_match_installed_metadata() -> None:
    """Package metadata declares the ratified Python and Syrupy ranges."""
    configuration = tomllib.loads(
        (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    )
    assert configuration["project"]["dependencies"] == ["syrupy>=5.0.0,<7.0.0"], (
        "pyproject.toml must declare the approved Syrupy compatibility range"
    )
    distribution = metadata.metadata("syrupy-mdast")
    assert distribution["Requires-Python"] == ">=3.12", (
        "installed metadata must preserve the supported Python range"
    )
    assert distribution.get_all("Requires-Dist") == ["syrupy<7.0.0,>=5.0.0"], (
        "installed metadata must contain only the canonical Syrupy requirement"
    )
    assert SingleFileSnapshotExtension.file_extension, (
        "installed Syrupy must expose SingleFileSnapshotExtension"
    )
    assert WriteMode.TEXT.value, "installed Syrupy must expose WriteMode.TEXT"
    assert hasattr(SingleFileSnapshotExtension, "_write_mode"), (
        "installed Syrupy must retain the private text-mode hook"
    )


def test_package_ships_py_typed_marker() -> None:
    """Built wheels ship typing data and omit JavaScript packaging assets."""
    repository_root = Path(__file__).parents[1]
    uv_executable = which("uv")
    assert uv_executable is not None, "the wheel contract requires uv on PATH"
    with TemporaryDirectory() as temporary_directory:
        subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- fixed local build command.
            [uv_executable, "build", "--wheel", "--out-dir", temporary_directory],
            check=True,
            cwd=repository_root,
        )
        wheel_path = next(Path(temporary_directory).glob("*.whl"))
        with ZipFile(wheel_path) as wheel:
            member_names = wheel.namelist()
    assert "syrupy_mdast/py.typed" in member_names, (
        "the installed wheel must ship the PEP 561 marker"
    )
    forbidden_names = {
        "package.json",
        "package-lock.json",
        "bun.lock",
        "bun.lockb",
        "pnpm-lock.yaml",
        "yarn.lock",
    }
    unexpected_assets = [
        member_name
        for member_name in member_names
        if member_name.endswith((".js", ".mjs", ".cjs"))
        or member_name.rsplit("/", maxsplit=1)[-1] in forbidden_names
        or member_name.startswith("node_modules/")
        or "/node_modules/" in member_name
    ]
    assert not unexpected_assets, (
        "the installed wheel must not contain JavaScript source or packaging assets"
    )
