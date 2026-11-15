"""Contract and sequence tests for the internal Wenmode adapter seam."""

from __future__ import annotations

import copy

import pytest

import syrupy_mdast._wenmode as wenmode_adapter
from tests.support.wenmode_adapter import (
    DEFINITION_DOCUMENT,
    REDEFINITION_DOCUMENT,
    UNRESOLVED_DOCUMENT,
    FailureStage,
    RecordingAdapter,
    UpstreamSentinelError,
    footnote_texts,
    parse_directly,
    plain_text_root,
    reference_urls,
)

SMOKE_SOURCES = {
    "empty": "",
    "ordinary": "# Title\n\nA [link](https://example.com) and **bold** text.\n",
    "unicode": "# Título\n\nCafé ☕ 日本語\n",
    "incomplete": "# Open\n\nA [dangling link and **unclosed emphasis\n",
}


def test_each_call_constructs_a_fresh_profile_and_parser(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two adapter calls build two profiles and two distinct parsers."""
    recorder = RecordingAdapter()
    recorder.install(monkeypatch)

    first = wenmode_adapter.parse_markdown("# One\n")
    second = wenmode_adapter.parse_markdown("# Two\n")

    assert recorder.profile_calls == 2, (
        "every adapter call must construct a new parser profile"
    )
    assert len(recorder.parsers) == 2, "every adapter call must construct a parser"
    assert recorder.parsers[0] is not recorder.parsers[1], (
        "two calls must retain two distinct parser instances"
    )
    assert [parser.rules for parser in recorder.parsers] == [
        recorder.profile_sentinel,
        recorder.profile_sentinel,
    ], "each parser must receive the freshly constructed profile"
    assert [parser.positions for parser in recorder.parsers] == [False, False], (
        "the adapter must disable source positions"
    )
    assert [parser.sources for parser in recorder.parsers] == [
        ["# One\n"],
        ["# Two\n"],
    ], "each parser must receive exactly its own call's source"
    assert [parser.parse_calls for parser in recorder.parsers] == [1, 1], (
        "each parser must parse exactly once"
    )
    assert first == {"type": "root", "source": "# One\n"}, (
        "the first call must return its own document's result"
    )
    assert second == {"type": "root", "source": "# Two\n"}, (
        "the second call must return its own document's result"
    )


def test_result_is_the_exact_object_returned_by_to_ast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The adapter returns Wenmode's data object without copying or wrapping."""
    recorder = RecordingAdapter()
    recorder.install(monkeypatch)

    result = wenmode_adapter.parse_markdown("# One\n")

    document = recorder.parsers[0].documents[0]
    assert result is document.ast_result, (
        "the adapter must return the object produced by to_ast() unchanged"
    )
    assert document.to_ast_calls == 1, "the adapter must call to_ast() exactly once"


@pytest.mark.parametrize(
    ("name", "source"), SMOKE_SOURCES.items(), ids=list(SMOKE_SOURCES)
)
def test_source_is_forwarded_verbatim(
    monkeypatch: pytest.MonkeyPatch, name: str, source: str
) -> None:
    """Empty, ordinary, Unicode, and incomplete Markdown reach the parser intact."""
    recorder = RecordingAdapter()
    recorder.install(monkeypatch)

    result = wenmode_adapter.parse_markdown(source)

    assert recorder.parsers[0].sources == [source], (
        f"the {name} source must be forwarded verbatim"
    )
    assert result == {"type": "root", "source": source}, (
        f"the {name} source must produce its own result"
    )


@pytest.mark.parametrize("stage", list(FailureStage))
def test_upstream_failure_reaches_the_caller_unchanged(
    monkeypatch: pytest.MonkeyPatch, stage: FailureStage
) -> None:
    """A Wenmode failure at any stage propagates as the same exception object."""
    recorder = RecordingAdapter()
    recorder.install(monkeypatch)
    failure = UpstreamSentinelError(f"wenmode failure during {stage.value}")
    recorder.fail_at(stage, failure)

    with pytest.raises(UpstreamSentinelError) as caught:
        wenmode_adapter.parse_markdown("# Broken\n")

    assert caught.value is failure, (
        f"a {stage.value} failure must reach the caller untranslated"
    )


@pytest.mark.parametrize("stage", list(FailureStage))
def test_call_after_failure_constructs_a_new_parser_and_succeeds(
    monkeypatch: pytest.MonkeyPatch, stage: FailureStage
) -> None:
    """A failed call leaves no cached parser or poisoned state behind."""
    recorder = RecordingAdapter()
    recorder.install(monkeypatch)
    recorder.fail_at(stage, UpstreamSentinelError("once"))
    with pytest.raises(UpstreamSentinelError):
        wenmode_adapter.parse_markdown("# Broken\n")
    recorder.clear_failure()
    parsers_before = len(recorder.parsers)

    result = wenmode_adapter.parse_markdown("# Recovered\n")

    assert result == {"type": "root", "source": "# Recovered\n"}, (
        "the recovered call must return its own document's result"
    )
    assert len(recorder.parsers) == parsers_before + 1, (
        "the call after a failure must construct its own parser"
    )
    assert recorder.parsers[-1].sources == ["# Recovered\n"], (
        "the recovered parser must receive only the recovered source"
    )


def test_definitions_do_not_escape_their_document() -> None:
    """A later document using undefined labels stays plain text."""
    first = wenmode_adapter.parse_markdown(DEFINITION_DOCUMENT)
    first_before_later_calls = copy.deepcopy(first)

    second = wenmode_adapter.parse_markdown(UNRESOLVED_DOCUMENT)

    assert second == parse_directly(UNRESOLVED_DOCUMENT), (
        "the second tree must equal its independent parse"
    )
    assert second == plain_text_root(UNRESOLVED_DOCUMENT), (
        "undefined reference and footnote labels must remain literal text"
    )
    assert first == first_before_later_calls, (
        "the first tree must remain unchanged after later calls"
    )
    assert reference_urls(first) == ["https://example.com/first"], (
        "the first tree must resolve its own reference"
    )
    assert footnote_texts(first) == ["First footnote text."], (
        "the first tree must carry its own footnote text"
    )


def test_later_definitions_belong_to_the_later_document() -> None:
    """Redefining the same labels yields only the later document's contents."""
    first = wenmode_adapter.parse_markdown(DEFINITION_DOCUMENT)
    second = wenmode_adapter.parse_markdown(REDEFINITION_DOCUMENT)

    assert reference_urls(first) == ["https://example.com/first"], (
        "the first document's reference must keep its destination"
    )
    assert reference_urls(second) == ["https://example.com/second"], (
        "the redefinition must resolve inside the later document only"
    )
    assert footnote_texts(first) == ["First footnote text."], (
        "the first document's footnote must keep its text"
    )
    assert footnote_texts(second) == ["Second footnote text."], (
        "the redefined footnote must carry the later text"
    )
    assert second == parse_directly(REDEFINITION_DOCUMENT), (
        "the later tree must equal its independent parse"
    )


@pytest.mark.parametrize(
    "source",
    [
        *SMOKE_SOURCES.values(),
        DEFINITION_DOCUMENT,
        UNRESOLVED_DOCUMENT,
        REDEFINITION_DOCUMENT,
    ],
    ids=[
        *SMOKE_SOURCES,
        "definitions",
        "unresolved",
        "redefinitions",
    ],
)
def test_result_matches_an_independent_parse(source: str) -> None:
    """Every adapter result equals a fresh direct Wenmode parse of that source."""
    assert wenmode_adapter.parse_markdown(source) == parse_directly(source), (
        "the adapter result must equal a fresh direct parse"
    )


def test_repeated_calls_return_equal_but_distinct_trees() -> None:
    """Repeating a call neither reuses nor returns a shared result object."""
    first = wenmode_adapter.parse_markdown(DEFINITION_DOCUMENT)
    second = wenmode_adapter.parse_markdown(DEFINITION_DOCUMENT)

    assert first == second, "repeating a parse must produce the same tree"
    assert first is not second, "each call must return its own tree object"


def test_empty_documents_between_documents_neither_reset_nor_leak() -> None:
    """An empty document in the middle of a sequence is independent of both."""
    first = wenmode_adapter.parse_markdown(DEFINITION_DOCUMENT)
    empty = wenmode_adapter.parse_markdown("")
    second = wenmode_adapter.parse_markdown(UNRESOLVED_DOCUMENT)

    assert first == parse_directly(DEFINITION_DOCUMENT), (
        "the definition document must equal its independent parse"
    )
    assert empty == {"type": "root", "children": []}, (
        "an empty document must produce an empty root"
    )
    assert second == parse_directly(UNRESOLVED_DOCUMENT), (
        "the unresolved document must equal its independent parse"
    )
    assert reference_urls(first) == ["https://example.com/first"], (
        "the first document must still resolve its own reference"
    )
    assert reference_urls(second) == [], (
        "the unresolved document must not borrow the earlier destination"
    )
