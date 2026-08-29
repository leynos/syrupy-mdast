"""Contracts for the v1 public package surface."""

from __future__ import annotations

import typing as typ

import pytest

import syrupy_mdast

if typ.TYPE_CHECKING:
    from syrupy.types import SerializableData


def test_public_surface_matches_design_section_six() -> None:
    """Only the two ratified public names are reachable from the package."""
    public_names = {name for name in dir(syrupy_mdast) if not name.startswith("_")}
    expected_names = {"MarkdownAstError", "MarkdownAstSnapshotExtension"}
    assert public_names == expected_names, f"unexpected public names: {public_names}"
    assert set(syrupy_mdast.__all__) == expected_names, (
        "__all__ must match the public surface"
    )


@pytest.mark.parametrize("data", [1, b"# Title", None, []])
def test_extension_rejects_non_string_data(data: object) -> None:
    """The adapter rejects every non-string partition named by the contract."""
    extension = syrupy_mdast.MarkdownAstSnapshotExtension()
    with pytest.raises(TypeError, match=type(data).__name__):
        extension.serialize(typ.cast("SerializableData", data))


@pytest.mark.parametrize("control_name", ["exclude", "include", "matcher"])
def test_extension_rejects_each_property_control(control_name: str) -> None:
    """Each unsupported Syrupy property control names itself in the failure."""
    """The adapter reports unsupported caller inputs before serialisation exists."""
    extension = syrupy_mdast.MarkdownAstSnapshotExtension()
    controls = {control_name: lambda _path, _name: True}
    with pytest.raises(ValueError, match=control_name):
        extension.serialize("# Title", **controls)


def test_extension_rejects_combined_property_controls() -> None:
    """The first supplied unsupported control fails before serialisation."""
    extension = syrupy_mdast.MarkdownAstSnapshotExtension()
    with pytest.raises(ValueError, match="exclude"):
        extension.serialize(
            "# Title",
            exclude=lambda _path, _name: True,
            include=lambda _path, _name: True,
            matcher=lambda _path, _name: True,
        )


def test_extension_defers_valid_serialisation_to_roadmap_task() -> None:
    """Valid source reaches the visible roadmap 2.3.1 serialization seam."""
    extension = syrupy_mdast.MarkdownAstSnapshotExtension()
    with pytest.raises(NotImplementedError, match=r"2\.3\.1"):
        extension.serialize("# Title")
