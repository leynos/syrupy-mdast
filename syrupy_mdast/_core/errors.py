"""Stable domain errors for Markdown AST comparison."""

from __future__ import annotations

import typing as typ

CATEGORY_SOURCE_ENCODING: typ.Final = "source-encoding"
CATEGORY_INPUT_TOO_LARGE: typ.Final = "input-too-large"
CATEGORY_PARSE: typ.Final = "parse"
CATEGORY_AST_SHAPE: typ.Final = "ast-shape"
CATEGORY_SERIALIZATION: typ.Final = "serialization"

CATEGORIES: typ.Final[tuple[str, ...]] = (
    CATEGORY_SOURCE_ENCODING,
    CATEGORY_INPUT_TOO_LARGE,
    CATEGORY_PARSE,
    CATEGORY_AST_SHAPE,
    CATEGORY_SERIALIZATION,
)


def _restore_markdown_ast_error(message: str, category: str) -> MarkdownAstError:
    """Recreate a categorised error for pickle and copy operations."""
    return MarkdownAstError(message, category=category)


class MarkdownAstError(Exception):
    """Raised when Markdown cannot be compared as a canonical AST.

    Args:
        message: An actionable explanation of the failed operation.
        category: One of the stable values in :data:`CATEGORIES`.

    Raises
    ------
        ValueError: If ``category`` is not part of the public taxonomy.

    Example:
        >>> MarkdownAstError("source is not valid UTF-8", category="source-encoding")
        MarkdownAstError('source is not valid UTF-8')
    """

    def __init__(self, message: str, *, category: str) -> None:
        """Initialize an error with a required, stable category."""
        if category not in CATEGORIES:
            error_message = f"unknown category: {category!r}"
            raise ValueError(error_message)
        super().__init__(message)
        self.category = category

    def __reduce__(self) -> tuple[object, ...]:
        """Preserve the keyword-only category during pickling."""
        if type(self) is not MarkdownAstError:
            return (type(self), (str(self),))
        return (_restore_markdown_ast_error, (str(self), self.category))


class SourceEncodingError(MarkdownAstError):
    """Raised when Markdown source cannot be decoded as text."""

    def __init__(self, message: str) -> None:
        """Initialize an error in the source-encoding category."""
        super().__init__(message, category=CATEGORY_SOURCE_ENCODING)


class InputTooLargeError(MarkdownAstError):
    """Raised when Markdown input exceeds the supported size."""

    def __init__(self, message: str) -> None:
        """Initialize an error in the input-too-large category."""
        super().__init__(message, category=CATEGORY_INPUT_TOO_LARGE)


class ParseError(MarkdownAstError):
    """Raised when Markdown source cannot be parsed."""

    def __init__(self, message: str) -> None:
        """Initialize an error in the parse category."""
        super().__init__(message, category=CATEGORY_PARSE)


class AstShapeError(MarkdownAstError):
    """Raised when parsed Markdown has an unsupported AST shape."""

    def __init__(self, message: str) -> None:
        """Initialize an error in the ast-shape category."""
        super().__init__(message, category=CATEGORY_AST_SHAPE)


class SerializationError(MarkdownAstError):
    """Raised when canonical Markdown AST serialization fails."""

    def __init__(self, message: str) -> None:
        """Initialize an error in the serialization category."""
        super().__init__(message, category=CATEGORY_SERIALIZATION)
