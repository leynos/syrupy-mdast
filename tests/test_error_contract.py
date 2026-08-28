"""Contracts for the public Markdown AST error."""

from __future__ import annotations

import pickle  # ruff: ignore[suspicious-pickle-import] -- test-created object only.

import pytest
from hypothesis import given
from hypothesis import strategies as st

from syrupy_mdast._core import CATEGORIES, MarkdownAstError


@pytest.mark.parametrize("category", CATEGORIES)
def test_error_preserves_category_and_pickle_round_trip(category: str) -> None:
    """Each ratified category survives construction and pickling."""
    error = MarkdownAstError("cannot parse source", category=category)
    restored = pickle.loads(pickle.dumps(error))  # ruff: ignore[suspicious-pickle-usage] -- local bytes
    assert restored.category == category, "pickling must preserve the category"
    assert str(restored) == "cannot parse source", "pickling must preserve the message"


@given(st.text())
def test_error_renders_arbitrary_messages(message: str) -> None:
    """The error renders every caller-provided message unchanged."""
    assert str(MarkdownAstError(message, category=CATEGORIES[0])) == message, (
        "MarkdownAstError must preserve every caller-provided message"
    )


def test_error_rejects_unknown_category() -> None:
    """The public error refuses categories outside the ratified taxonomy."""
    with pytest.raises(ValueError, match="unknown category"):
        MarkdownAstError("cannot parse source", category="unknown")
