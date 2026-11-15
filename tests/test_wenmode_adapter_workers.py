"""Per-call parser allocation inside each pytest-xdist worker process.

Run this module with ``-n 2 --dist=each`` so both workers execute it. Object
identities are compared only inside one process; worker ids and process ids are
reported as evidence and never used to compare instances across processes.
"""

from __future__ import annotations

import os
import typing as typ

import syrupy_mdast._wenmode as wenmode_adapter
from tests.support.wenmode_adapter import (
    DEFINITION_DOCUMENT,
    REDEFINITION_DOCUMENT,
    RecordingAdapter,
    footnote_texts,
    parse_directly,
    reference_urls,
)

if typ.TYPE_CHECKING:
    import pytest


def _evidence(worker_id: str, parsed_documents: int) -> str:
    """Return worker and process identity evidence for an assertion."""
    return f"worker={worker_id} pid={os.getpid()} parsed_documents={parsed_documents}"


def test_each_call_allocates_its_own_parser_in_this_worker(
    monkeypatch: pytest.MonkeyPatch, worker_id: str
) -> None:
    """One worker retains two distinct parsers, each bound to its own source."""
    recorder = RecordingAdapter()
    recorder.install(monkeypatch)

    first = wenmode_adapter.parse_markdown(DEFINITION_DOCUMENT)
    second = wenmode_adapter.parse_markdown(REDEFINITION_DOCUMENT)

    evidence = _evidence(worker_id, len(recorder.parsers))
    assert len(recorder.parsers) == 2, evidence
    first_parser, second_parser = recorder.parsers
    assert first_parser is not second_parser, evidence
    assert first_parser.sources == [DEFINITION_DOCUMENT], evidence
    assert second_parser.sources == [REDEFINITION_DOCUMENT], evidence
    assert first is first_parser.documents[0].ast_result, evidence
    assert second is second_parser.documents[0].ast_result, evidence
    print(evidence)


def test_worker_keeps_reference_and_footnote_state_independent(worker_id: str) -> None:
    """The worker's real parse preserves each document's own labels."""
    first = wenmode_adapter.parse_markdown(DEFINITION_DOCUMENT)
    second = wenmode_adapter.parse_markdown(REDEFINITION_DOCUMENT)

    evidence = _evidence(worker_id, 2)
    assert first == parse_directly(DEFINITION_DOCUMENT), evidence
    assert second == parse_directly(REDEFINITION_DOCUMENT), evidence
    assert reference_urls(first) == ["https://example.com/first"], evidence
    assert reference_urls(second) == ["https://example.com/second"], evidence
    assert footnote_texts(first) == ["First footnote text."], evidence
    assert footnote_texts(second) == ["Second footnote text."], evidence
    print(evidence)
