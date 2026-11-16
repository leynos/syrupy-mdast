"""Property evidence that adapter results never depend on earlier documents.

Each generated document is compared with a fresh direct Wenmode parse of that
same source. Because the expected tree is produced independently for every
document, any parser or state reuse that leaks a label across documents changes
the adapter result and fails the comparison. Earlier results are kept as deep
copies so a later call cannot mutate them unnoticed.
"""

from __future__ import annotations

import copy

from hypothesis import event, example, given, settings
from hypothesis import strategies as st

import syrupy_mdast._wenmode as wenmode_adapter
from tests.support.wenmode_adapter import (
    DEFINITION_DOCUMENT,
    REDEFINITION_DOCUMENT,
    UNRESOLVED_DOCUMENT,
    parse_directly,
    plain_text_root,
)

_LABELS = st.sampled_from(["a", "b", "c"])
_TARGETS = st.text(alphabet="xyz", min_size=1, max_size=4)
_FOOTNOTE_TEXT = st.text(alphabet="pqrs ", min_size=1, max_size=8)


@st.composite
def _documents(draw: st.DrawFn) -> list[tuple[str, tuple[str, ...]]]:
    """Draw 1-8 short documents and the labels each one defines.

    Returns
    -------
    list[tuple[str, tuple[str, ...]]]
        One ``(source, defined labels)`` pair per document. Each document uses
        an ordinary reference and a footnote; some also define them, so a
        sequence naturally mixes definitions, unresolved uses, and
        redefinitions to different destinations and texts.
    """
    count = draw(st.integers(min_value=1, max_value=8))
    documents = []
    for _ in range(count):
        label = draw(_LABELS)
        footnote_label = draw(st.one_of(st.just(label), _LABELS))
        source = f"See [{label}] and a footnote[^{footnote_label}]."
        if draw(st.booleans()):
            target = draw(_TARGETS)
            footnote = draw(_FOOTNOTE_TEXT)
            source += (
                f"\n\n[{label}]: https://example.com/{target}\n"
                f"[^{footnote_label}]: Footnote {footnote}."
            )
            documents.append((source + "\n", (label, footnote_label)))
        else:
            documents.append((source + "\n", ()))
    return documents


def _classify(documents: list[tuple[str, tuple[str, ...]]]) -> None:
    """Record which document-order classes this example exercises."""
    seen: set[str] = set()
    redefined = False
    defines_labels = False
    for _source, labels in documents:
        redefined = redefined or bool(seen.intersection(labels))
        seen.update(labels)
        defines_labels = defines_labels or bool(labels)
    event(f"sequence redefines a label: {redefined}")
    event(f"sequence defines any label: {defines_labels}")


@given(documents=_documents())
@settings(max_examples=50, deadline=None)
@example(
    documents=[
        (DEFINITION_DOCUMENT, ("key", "note")),
        (UNRESOLVED_DOCUMENT, ()),
    ]
)
@example(
    documents=[
        (DEFINITION_DOCUMENT, ("key", "note")),
        (REDEFINITION_DOCUMENT, ("key", "note")),
    ]
)
@example(documents=[(UNRESOLVED_DOCUMENT, ()), (UNRESOLVED_DOCUMENT, ())])
def test_each_result_equals_the_fresh_parse_of_its_own_document(
    documents: list[tuple[str, tuple[str, ...]]],
) -> None:
    """Every document in a sequence parses as if it were parsed alone."""
    _classify(documents)
    results: list[dict[str, object]] = []
    snapshots: list[dict[str, object]] = []

    for source, labels in documents:
        result = wenmode_adapter.parse_markdown(source)

        assert result == parse_directly(source), (
            "an adapter result must not depend on any earlier document"
        )
        assert results == snapshots, (
            "an earlier result must not change after a later adapter call"
        )
        if not labels:
            assert result == plain_text_root(source), (
                "a document without definitions must not resolve earlier labels"
            )

        results.append(result)
        snapshots.append(copy.deepcopy(result))

    assert len(results) == len(documents), (
        "every generated document must produce exactly one result"
    )
