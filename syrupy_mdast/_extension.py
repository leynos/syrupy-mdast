"""Syrupy adapter for future canonical Markdown AST serialisation."""

from __future__ import annotations

import typing as typ

from syrupy.extensions.single_file import SingleFileSnapshotExtension, WriteMode

if typ.TYPE_CHECKING:
    from syrupy.types import (
        PropertyFilter,
        PropertyMatcher,
        SerializableData,
        SerializedData,
    )


class MarkdownAstSnapshotExtension(SingleFileSnapshotExtension):
    """Compare Markdown sources as canonical mdast-compatible JSON.

    Parsing and serialisation arrive in roadmap task 2.3.1; this adapter
    already rejects inputs whose future implementation cannot support.
    """

    file_extension = "mdast.json"
    _write_mode = WriteMode.TEXT

    @typ.override
    def serialize(
        self,
        data: SerializableData,
        *,
        exclude: PropertyFilter | None = None,
        include: PropertyFilter | None = None,
        matcher: PropertyMatcher | None = None,
    ) -> SerializedData:
        """Validate the v1 boundary until the AST pipeline is implemented."""
        if not isinstance(data, str):
            error_message = (
                f"{self.__class__.__name__} accepts str data, got {type(data).__name__}"
            )
            raise TypeError(error_message)
        for control_name, control in (
            ("exclude", exclude),
            ("include", include),
            ("matcher", matcher),
        ):
            if control is not None:
                error_message = f"{control_name} is not supported"
                raise ValueError(error_message)
        raise NotImplementedError(
            "Markdown serialisation arrives in roadmap task 2.3.1"
        )
