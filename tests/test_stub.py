"""Tests for the generated package stub."""

from __future__ import annotations

import syrupy_mdast


def test_hello_returns_stub_greeting() -> None:
    """The generated package exposes a working greeting."""
    greeting = syrupy_mdast.hello()
    assert greeting == "hello from Python", (
        f"expected the pure-Python stub greeting, got {greeting!r}"
    )
