"""Internal Wenmode adapter: one independent parser per Markdown document.

Wenmode parser instances are reusable, but a comparison result must not depend
on which document was parsed first. This module therefore owns the smallest
possible seam: every call constructs its own GitHub-profile parser, parses once,
and returns Wenmode's ``to_ast()`` mapping unchanged. Nothing here caches a
parser, a profile, or a result, and nothing shares state between calls, threads,
or worker processes.

The underscore-prefixed module name keeps the seam internal to the later
application pipeline (design section 7); it is not part of the public package
surface. Wenmode failures propagate unchanged. Categorizing them as
``MarkdownAstError`` belongs to the pipeline that can describe the failing
operation, so this boundary stays thin and inspectable.
"""

from __future__ import annotations

from wenmode import Parser
from wenmode.presets import github


def parse_markdown(source: str) -> dict[str, object]:
    """Parse Markdown with a fresh GitHub-profile parser and no positions.

    Parameters
    ----------
    source
        Markdown text to parse. Ordinary reference links, images, footnotes,
        tables, task lists, strikethrough, and extended autolinks follow the
        GitHub profile; frontmatter, math, directives, and Markdown JSX are
        outside the supported profile.

    Returns
    -------
    dict[str, object]
        Wenmode's mdast-compatible root node, returned unchanged. Values are
        plain strings, numbers, lists, and nested dictionaries; shapes are not
        validated here and canonicalization remains future work.

    Notes
    -----
    Wenmode failures while constructing the parser, parsing the source, or
    converting the document propagate unchanged: this seam never translates,
    wraps, or swallows them, and a later call always starts from a new parser.

    Examples
    --------
    >>> parse_markdown("# Title")["children"][0]["depth"]
    1
    """
    return Parser(github(), positions=False).parse(source).to_ast()
