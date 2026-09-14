"""Markdown AST snapshot support for Syrupy.

The public exports join the dependency-free domain error with the Syrupy
snapshot adapter. Markdown parsing and canonical serialization arrive in
roadmap task 2.3.1.
"""

from ._core import MarkdownAstError
from ._extension import MarkdownAstSnapshotExtension

__all__ = ["MarkdownAstError", "MarkdownAstSnapshotExtension"]
