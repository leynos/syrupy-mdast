"""Barrier-controlled evidence that overlapping calls own their parser state.

Real Wenmode parsers are wrapped so each ``parse`` announces its entry, waits
at a two-party barrier, and then waits for an explicit release. The test thread
therefore knows both calls are inside ``parse`` at the same time, and knows the
other call is still blocked when the first completes. A serialized or shared
parser cannot produce that ordering: it either breaks the barrier or fails a
retained-instance assertion. Every wait is bounded and every blocker is
released in cleanup, so a broken implementation fails rather than hangs.
"""

from __future__ import annotations

import concurrent.futures
import threading

import pytest
from wenmode import Parser

import syrupy_mdast._wenmode as wenmode_adapter
from tests.support.wenmode_adapter import (
    DEFINITION_DOCUMENT,
    REDEFINITION_DOCUMENT,
    UNRESOLVED_DOCUMENT,
    OverlapControls,
    RuleSource,
    SynchronizedAdapter,
    footnote_texts,
    parse_directly,
    reference_urls,
)

_BOUND_SECONDS = 5.0


def _parse_with_controlled_overlap(
    monkeypatch: pytest.MonkeyPatch,
    documents: tuple[str, str],
    *,
    first_to_finish: int,
) -> tuple[dict[str, dict[str, object]], SynchronizedAdapter]:
    """Run two adapter calls concurrently at a shared parse barrier.

    Parameters
    ----------
    monkeypatch
        Fixture used to install the synchronizing parser factory.
    documents
        The two sources, in start order.
    first_to_finish
        Index of the call released first.

    Returns
    -------
    tuple[dict[str, dict[str, object]], SynchronizedAdapter]
        Trees keyed by source, and the factory holding both parser instances.
    """
    controls = OverlapControls(
        sources=documents,
        bound_seconds=_BOUND_SECONDS,
        barrier=threading.Barrier(len(documents)),
    )
    factory = SynchronizedAdapter(controls)
    factory.install(monkeypatch)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(documents))
    futures: dict[str, concurrent.futures.Future[dict[str, object]]] = {}
    try:
        futures[documents[0]] = executor.submit(
            wenmode_adapter.parse_markdown, documents[0]
        )
        assert controls.entered[documents[0]].wait(_BOUND_SECONDS), (
            "the first call never reached parse"
        )
        futures[documents[1]] = executor.submit(
            wenmode_adapter.parse_markdown, documents[1]
        )
        for source in documents:
            assert controls.passed[source].wait(_BOUND_SECONDS), (
                "both calls must be inside parse before either proceeds"
            )

        released = documents[first_to_finish]
        blocked = documents[1 - first_to_finish]
        controls.release[released].set()
        futures[released].result(timeout=_BOUND_SECONDS)
        assert not futures[blocked].done(), (
            "the other call must still be inside parse when the first completes"
        )
        controls.release[blocked].set()

        return {
            source: future.result(timeout=_BOUND_SECONDS)
            for source, future in futures.items()
        }, factory
    finally:
        controls.abort()
        executor.shutdown(wait=True, cancel_futures=True)


@pytest.mark.parametrize(
    "first_to_finish",
    [0, 1],
    ids=["definitions-complete-first", "redefinitions-complete-first"],
)
def test_overlapping_calls_retain_distinct_parsers(
    monkeypatch: pytest.MonkeyPatch, first_to_finish: int
) -> None:
    """Colliding labels parsed simultaneously stay with their own parser."""
    documents = (DEFINITION_DOCUMENT, REDEFINITION_DOCUMENT)

    results, factory = _parse_with_controlled_overlap(
        monkeypatch, documents, first_to_finish=first_to_finish
    )

    assert len(factory.parsers) == 2, "each overlapping call must construct a parser"
    first, second = factory.parsers
    assert first is not second, "overlapping calls must retain distinct parsers"
    assert first.sources == [DEFINITION_DOCUMENT], (
        "the first parser must retain only the first source"
    )
    assert second.sources == [REDEFINITION_DOCUMENT], (
        "the second parser must retain only the second source"
    )
    assert results[DEFINITION_DOCUMENT] == parse_directly(DEFINITION_DOCUMENT), (
        "the first overlapping result must equal its independent parse"
    )
    assert results[REDEFINITION_DOCUMENT] == parse_directly(REDEFINITION_DOCUMENT), (
        "the second overlapping result must equal its independent parse"
    )
    assert reference_urls(results[DEFINITION_DOCUMENT]) == [
        "https://example.com/first"
    ], "the first overlapping tree must resolve its own destination"
    assert reference_urls(results[REDEFINITION_DOCUMENT]) == [
        "https://example.com/second"
    ], "the second overlapping tree must resolve its own destination"
    assert footnote_texts(results[DEFINITION_DOCUMENT]) == ["First footnote text."], (
        "the first overlapping tree must keep its own footnote text"
    )
    assert footnote_texts(results[REDEFINITION_DOCUMENT]) == [
        "Second footnote text."
    ], "the second overlapping tree must keep its own footnote text"


class _ReentrantAdapter:
    """Factory double whose first outer parse starts one nested adapter call."""

    def __init__(self, outer_source: str, inner_source: str) -> None:
        """Record the two sources and start with no parsers or events."""
        self.outer_source = outer_source
        self.inner_source = inner_source
        self.parsers: list[_ReentrantParser] = []
        self.events: list[tuple[str, str]] = []
        self.inner_result: dict[str, object] = {}
        self._has_started_inner_call = False

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Patch the adapter module's parser for one test."""
        monkeypatch.setattr(wenmode_adapter, "Parser", self)

    def __call__(self, rules: RuleSource, *, positions: bool) -> _ReentrantParser:
        """Retain a new parser double for one adapter call."""
        parser = _ReentrantParser(self, rules, positions=positions)
        self.parsers.append(parser)
        return parser

    def start_inner_call_once(self) -> None:
        """Run the nested adapter call once, guarded against recursion."""
        if self._has_started_inner_call:
            return
        self._has_started_inner_call = True
        self.inner_result = wenmode_adapter.parse_markdown(self.inner_source)


class _ReentrantParser:
    """Parser double that nests one real parse inside its outer parse."""

    def __init__(
        self, double: _ReentrantAdapter, rules: RuleSource, *, positions: bool
    ) -> None:
        """Build the real parser that the outer ``parse`` delegates to."""
        self._double = double
        self._delegate = Parser(rules, positions=positions)
        self.sources: list[str] = []

    def parse(self, source: str) -> object:
        """Announce entry, nest the inner call once, then parse for real."""
        self._double.events.append(("enter", source))
        self._double.start_inner_call_once()
        self.sources.append(source)
        document = self._delegate.parse(source)
        self._double.events.append(("return", source))
        return document


def test_nested_call_constructs_an_independent_parser(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A call made from inside parse gets its own parser and result."""
    double = _ReentrantAdapter(DEFINITION_DOCUMENT, UNRESOLVED_DOCUMENT)
    double.install(monkeypatch)

    outer_result = wenmode_adapter.parse_markdown(double.outer_source)

    expected_events = [
        ("enter", DEFINITION_DOCUMENT),
        ("enter", UNRESOLVED_DOCUMENT),
        ("return", UNRESOLVED_DOCUMENT),
        ("return", DEFINITION_DOCUMENT),
    ]
    assert double.events == expected_events, (
        "the inner call must complete while the outer parse is still active"
    )
    assert len(double.parsers) == 2, "each nested call must construct a parser"
    outer, inner = double.parsers
    assert outer is not inner, "the inner call must not reuse the outer parser"
    assert outer.sources == [DEFINITION_DOCUMENT], (
        "the outer parser must retain only the outer source"
    )
    assert inner.sources == [UNRESOLVED_DOCUMENT], (
        "the inner parser must retain only the inner source"
    )
    assert double.inner_result == parse_directly(UNRESOLVED_DOCUMENT), (
        "the nested result must equal its independent parse"
    )
    assert reference_urls(double.inner_result) == [], (
        "the inner document must not observe the outer definitions"
    )
    assert outer_result == parse_directly(DEFINITION_DOCUMENT), (
        "the outer result must still equal its independent parse"
    )
