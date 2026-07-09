"""Tests for the generated package stub."""

from __future__ import annotations

import syrupy_mdast


def test_hello_returns_stub_greeting() -> None:
    """The generated package exposes a working greeting."""
    assert syrupy_mdast.hello() == "hello from Python"
