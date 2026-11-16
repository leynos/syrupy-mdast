"""Shared documents and recording doubles for the internal Wenmode adapter.

The seam under test is ``syrupy_mdast._wenmode.parse_markdown``. The doubles
here are installed over that module's own ``Parser`` and ``github`` names, so
a test observes the adapter's boundary instead of reaching inside Wenmode.
They are test machinery: the package exposes no injection point for them.
"""

from __future__ import annotations

import dataclasses
import enum
import threading
import typing as typ

from wenmode import Parser
from wenmode.presets import github

import syrupy_mdast._wenmode as wenmode_adapter

if typ.TYPE_CHECKING:
    import collections.abc as cabc

    import pytest
    from wenmode.presets import PresetFactory
    from wenmode.rules import Rule

# The rule source accepted by Wenmode's parser constructor, named once so the
# doubles forward exactly what the adapter passed instead of restating it.
type RuleSource = cabc.Iterable[type[Rule] | Rule] | PresetFactory

DEFINITION_DOCUMENT = (
    "See [key] and a footnote[^note].\n"
    "\n"
    "[key]: https://example.com/first\n"
    "[^note]: First footnote text.\n"
)
"""Document that defines one ordinary reference and one footnote."""

UNRESOLVED_DOCUMENT = "See [key] and a footnote[^note].\n"
"""Document that uses those labels without defining them."""

REDEFINITION_DOCUMENT = (
    "See [key] and a footnote[^note].\n"
    "\n"
    "[key]: https://example.com/second\n"
    "[^note]: Second footnote text.\n"
)
"""Document that redefines both labels with different contents."""

UNRESOLVED_TEXT = "See [key] and a footnote[^note]."
"""Text Wenmode emits when a reference and footnote are unresolved."""


class UpstreamSentinelError(RuntimeError):
    """Stand-in for a Wenmode failure at a named adapter stage."""


class FailureStage(enum.StrEnum):
    """Points in one adapter call where a recording double can fail."""

    CONSTRUCT = "construct"
    PARSE = "parse"
    TO_AST = "to_ast"


def parse_directly(source: str) -> dict[str, object]:
    """Parse Markdown with a fresh parser, bypassing the adapter seam.

    Adapter tests compare their result with this independent expectation, so
    the expected value never comes from the code under test.

    Parameters
    ----------
    source
        Markdown text to parse with the GitHub profile and no positions.

    Returns
    -------
    dict[str, object]
        Wenmode's mdast-compatible root node.

    Examples
    --------
    >>> parse_directly("# Title")["children"][0]["depth"]
    1
    """
    return Parser(github(), positions=False).parse(source).to_ast()


def _walk(node: object) -> cabc.Iterator[dict[str, object]]:
    """Yield every mapping node in a Wenmode AST in document order."""
    if not isinstance(node, dict):
        return
    yield node
    children = node.get("children")
    if isinstance(children, list):
        for child in children:
            yield from _walk(child)


def reference_urls(tree: dict[str, object]) -> list[str]:
    """Return every ordinary-reference destination in document order.

    Parameters
    ----------
    tree
        Wenmode root node to search.

    Returns
    -------
    list[str]
        Destinations of resolved links, in document order. Unresolved
        references contribute nothing because Wenmode leaves them as text.
    """
    return [
        str(node["url"])
        for node in _walk(tree)
        if node.get("type") == "link" and "url" in node
    ]


def footnote_texts(tree: dict[str, object]) -> list[str]:
    """Return each footnote definition's flattened text in document order.

    Parameters
    ----------
    tree
        Wenmode root node to search.

    Returns
    -------
    list[str]
        Text values of every ``footnoteDefinition`` payload, in document
        order, with payload fragments concatenated per definition.
    """
    return [
        "".join(str(part.get("value", "")) for part in _walk(node))
        for node in _walk(tree)
        if node.get("type") == "footnoteDefinition"
    ]


def plain_text_root(source: str) -> dict[str, object]:
    """Return the tree expected when no label in ``source`` is defined.

    Wenmode leaves an unresolved reference or footnote as literal text, so a
    single-paragraph document with no definitions must produce exactly one text
    node carrying the source without its trailing newline.

    Parameters
    ----------
    source
        Markdown text whose labels are all undefined.

    Returns
    -------
    dict[str, object]
        The expected root node containing one plain-text paragraph.

    Examples
    --------
    >>> tree = plain_text_root("See [key].")
    >>> tree["children"][0]["children"][0]["value"]
    'See [key].'
    """
    return {
        "type": "root",
        "children": [
            {
                "type": "paragraph",
                "children": [{"type": "text", "value": source.removesuffix("\n")}],
            }
        ],
    }


@dataclasses.dataclass(frozen=True, slots=True)
class _ConfiguredFailure:
    """One stage/error pair a recording double should raise."""

    stage: FailureStage
    error: BaseException


class RecordingDocument:
    """Document double that records whether ``to_ast()`` was used."""

    def __init__(self, recorder: RecordingAdapter, source: str) -> None:
        """Record conversions for ``source`` against ``recorder``."""
        self._recorder = recorder
        self.source = source
        self.ast_result: dict[str, object] = {"type": "root", "source": source}
        self.to_ast_calls = 0

    def to_ast(self) -> dict[str, object]:
        """Record the call and return this document's one result object."""
        self.to_ast_calls += 1
        self._recorder.events.append(("to_ast", self.source))
        failure = self._recorder.failure
        if failure is not None and failure.stage is FailureStage.TO_AST:
            raise failure.error
        return self.ast_result


class RecordingParser:
    """Parser double that records construction, sources, and documents."""

    def __init__(
        self, recorder: RecordingAdapter, rules: RuleSource, *, positions: bool
    ) -> None:
        """Retain the construction arguments and start empty call records."""
        self.recorder = recorder
        self.rules = rules
        self.positions = positions
        self.parse_calls = 0
        self.sources: list[str] = []
        self.documents: list[RecordingDocument] = []

    def parse(self, source: str) -> RecordingDocument:
        """Record the forwarded source and return a recording document."""
        self.parse_calls += 1
        self.recorder.events.append(("parse", source))
        failure = self.recorder.failure
        if failure is not None and failure.stage is FailureStage.PARSE:
            raise failure.error
        self.sources.append(source)
        document = RecordingDocument(self.recorder, source)
        self.documents.append(document)
        return document


class RecordingAdapter:
    """Replace the adapter module's ``Parser`` and ``github`` names.

    Examples
    --------
    >>> recorder = RecordingAdapter()
    >>> recorder.install(monkeypatch)
    >>> parse_markdown("# Title")["source"]
    '# Title'
    """

    def __init__(self) -> None:
        """Start with no recorded calls and no configured failure."""
        self.profile_sentinel = object()
        self.profile_calls = 0
        self.parsers: list[RecordingParser] = []
        self.events: list[tuple[str, str]] = []
        self.failure: _ConfiguredFailure | None = None

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Patch the adapter module's profile and parser for one test."""
        monkeypatch.setattr(wenmode_adapter, "github", self.profile)
        monkeypatch.setattr(wenmode_adapter, "Parser", self)

    def profile(self) -> object:
        """Return the sentinel profile while recording its construction."""
        self.profile_calls += 1
        self.events.append(("profile", ""))
        return self.profile_sentinel

    def __call__(self, rules: RuleSource, *, positions: bool) -> RecordingParser:
        """Construct a recording parser, honouring a construction failure."""
        self.events.append(("construct", ""))
        failure = self.failure
        if failure is not None and failure.stage is FailureStage.CONSTRUCT:
            raise failure.error
        parser = RecordingParser(self, rules, positions=positions)
        self.parsers.append(parser)
        return parser

    def fail_at(self, stage: FailureStage, error: BaseException) -> None:
        """Configure the next call at ``stage`` to raise ``error``."""
        self.failure = _ConfiguredFailure(stage, error)

    def clear_failure(self) -> None:
        """Stop configured failures so a later call can succeed."""
        self.failure = None


class SynchronizedParser:
    """Wrap one real parser and publish its parse entry and release points."""

    def __init__(
        self, controls: OverlapControls, rules: RuleSource, *, positions: bool
    ) -> None:
        """Build the real parser this wrapper publishes parse events for."""
        self._controls = controls
        self._delegate = Parser(rules, positions=positions)
        self.sources: list[str] = []

    def parse(self, source: str) -> object:
        """Block at the shared barrier, then parse once after release."""
        self._controls.entered[source].set()
        self._controls.barrier.wait(timeout=self._controls.bound_seconds)
        self._controls.passed[source].set()
        if not self._controls.release[source].wait(
            timeout=self._controls.bound_seconds
        ):
            message = f"{source!r} was not released within the bounded wait"
            raise AssertionError(message)
        self.sources.append(source)
        return self._delegate.parse(source)


@dataclasses.dataclass(slots=True)
class OverlapControls:
    """Synchronization points shared by wrapped parsers and the test thread."""

    sources: tuple[str, ...]
    bound_seconds: float
    barrier: threading.Barrier
    entered: dict[str, threading.Event] = dataclasses.field(
        init=False, default_factory=dict
    )
    passed: dict[str, threading.Event] = dataclasses.field(
        init=False, default_factory=dict
    )
    release: dict[str, threading.Event] = dataclasses.field(
        init=False, default_factory=dict
    )

    def __post_init__(self) -> None:
        """Create one event per source for entry, barrier passage, and release."""
        for source in self.sources:
            self.entered[source] = threading.Event()
            self.passed[source] = threading.Event()
            self.release[source] = threading.Event()

    def abort(self) -> None:
        """Break the barrier and release every waiter during cleanup."""
        self.barrier.abort()
        for event in self.release.values():
            event.set()


class SynchronizedAdapter:
    """Factory double that wraps every adapter parser in a real parser."""

    def __init__(self, controls: OverlapControls) -> None:
        """Retain the shared controls and start with no wrapped parsers."""
        self.controls = controls
        self.parsers: list[SynchronizedParser] = []

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Patch the adapter module's parser for one test."""
        monkeypatch.setattr(wenmode_adapter, "Parser", self)

    def __call__(self, rules: RuleSource, *, positions: bool) -> SynchronizedParser:
        """Wrap a real parser with the shared synchronization controls."""
        parser = SynchronizedParser(self.controls, rules, positions=positions)
        self.parsers.append(parser)
        return parser
