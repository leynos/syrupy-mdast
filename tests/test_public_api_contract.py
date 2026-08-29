"""Contracts for the v1 public package surface."""

from __future__ import annotations

import pytest

import syrupy_mdast


def test_public_surface_matches_design_section_six() -> None:
    """Only the two ratified public names are reachable from the package."""
    public_names = {name for name in dir(syrupy_mdast) if not name.startswith("_")}
    expected_names = {"MarkdownAstError", "MarkdownAstSnapshotExtension"}
    assert public_names == expected_names, f"unexpected public names: {public_names}"
    assert set(syrupy_mdast.__all__) == expected_names, (
        "__all__ must match the public surface"
    )


def test_extension_rejects_unsupported_inputs() -> None:
    """The adapter reports unsupported caller inputs before serialisation exists."""
    extension = syrupy_mdast.MarkdownAstSnapshotExtension()
    with pytest.raises(TypeError, match="int"):
        extension.serialize(1)
    with pytest.raises(ValueError, match="exclude"):
        extension.serialize("# Title", exclude=lambda _path, _name: True)
    with pytest.raises(NotImplementedError, match=r"2\.3\.1"):
        extension.serialize("# Title")
