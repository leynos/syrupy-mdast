"""Contracts for the public Markdown AST error."""

from __future__ import annotations

import pickle  # ruff: ignore[suspicious-pickle-import] -- test-created object only.
import typing as typ

import pytest
from hypothesis import given
from hypothesis import strategies as st

from syrupy_mdast._core import (
    CATEGORIES,
    AstShapeError,
    InputTooLargeError,
    MarkdownAstError,
    ParseError,
    SerializationError,
    SourceEncodingError,
)


class ErrorFactory(typ.Protocol):
    """Construct a concrete Markdown AST error from its message."""

    def __call__(self, message: str) -> MarkdownAstError:
        """Create the category-specific error for ``message``."""


@pytest.mark.parametrize("category", CATEGORIES)
def test_error_preserves_category_and_pickle_round_trip(category: str) -> None:
    """Each ratified category survives construction and pickling."""
    error = MarkdownAstError("cannot parse source", category=category)
    restored = pickle.loads(pickle.dumps(error))  # ruff: ignore[suspicious-pickle-usage] -- local bytes
    assert restored.category == category, "pickling must preserve the category"
    assert str(restored) == "cannot parse source", "pickling must preserve the message"


def test_category_taxonomy_has_five_values() -> None:
    """The design's closed error taxonomy retains all five categories."""
    assert CATEGORIES == (
        "source-encoding",
        "input-too-large",
        "parse",
        "ast-shape",
        "serialization",
    ), "the public category taxonomy must contain the five ratified values in order"


@pytest.mark.parametrize(
    ("error_factory", "category"),
    [
        (SourceEncodingError, "source-encoding"),
        (InputTooLargeError, "input-too-large"),
        (ParseError, "parse"),
        (AstShapeError, "ast-shape"),
        (SerializationError, "serialization"),
    ],
)
def test_specialized_errors_preserve_category_and_pickle_type(
    error_factory: ErrorFactory, category: str
) -> None:
    """Each concrete domain error keeps its category through pickling."""
    error = error_factory("operation failed")
    restored = pickle.loads(pickle.dumps(error))  # ruff: ignore[suspicious-pickle-usage] -- local bytes
    assert type(restored) is error_factory, (
        "pickling must preserve the concrete error type"
    )
    assert restored.category == category, "each concrete error must retain its category"


@given(st.text(), st.sampled_from(CATEGORIES))
def test_error_pickles_arbitrary_messages(message: str, category: str) -> None:
    """Pickling preserves every generated message and each valid category."""
    error = MarkdownAstError(message, category=category)
    restored = pickle.loads(pickle.dumps(error))  # ruff: ignore[suspicious-pickle-usage] -- local bytes
    assert str(restored) == message, (
        "MarkdownAstError must preserve every caller-provided message"
    )
    assert restored.category == category, "pickling must preserve every valid category"


def test_error_rejects_unknown_category() -> None:
    """The public error refuses categories outside the ratified taxonomy."""
    with pytest.raises(ValueError, match="unknown category"):
        MarkdownAstError("cannot parse source", category="unknown")
