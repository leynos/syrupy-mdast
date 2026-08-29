"""Contracts for published package metadata."""

from __future__ import annotations

import tomllib
from importlib import metadata
from pathlib import Path

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
    """Package ships the PEP 561 marker for downstream type checkers."""
    assert (Path(__file__).parents[1] / "syrupy_mdast" / "py.typed").is_file(), (
        "syrupy_mdast must ship a PEP 561 marker"
    )
