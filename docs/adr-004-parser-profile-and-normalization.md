# Architectural decision record (ADR) 004: Parser profile and normalization

## Status

Proposed.

## Date

2026-10-11.

## Context and problem statement

`Syrupy-mdast` compares Markdown through a canonical, mdast-compatible abstract
syntax tree (AST) rather than raw source text. Its parser profile,
normalization rules, and JSON writer determine snapshot payload bytes and need
one explicit, machine-readable contract.

The [technical design](syrupy-mdast-design.md) §11 requires a versioned record
of the parser, normalization policy, comparison contract, and normative
fixtures before implementation or fixture changes. This record defines those
payload details. [ADR-003](adr-003-snapshot-version-policy.md) separately
defines how contract and package versions govern payload changes, and how
Wenmode upgrades are reviewed.

Wenmode is a pure-Python Markdown parser whose `to_ast()` interface emits
mdast-compatible dictionaries. Its GitHub profile provides CommonMark and
GitHub Flavoured Markdown (GFM) extensions. Because parser behaviour
contributes to persisted snapshots, the selected bounded requirement is
`>=0.15.2,<0.16.0`; 0.15.2 is the empirical evidence baseline. The finite probe
below verifies named cases only and does not claim identical output for every
later release allowed by the range.

## Decision Drivers

- Determinism: fix parser construction, normalization order, member order, and
  JSON spelling.
- Reviewability: remove only specified representation differences and retain
  structural distinctions that affect parsed content.
- Conservative equivalence: limit byte-equality claims to the same installed
  syrupy-mdast and Wenmode versions, profile, and interpreter environment.
- Python-only boundary: keep parsing, canonicalization, packaging, and failure
  handling within the Python package and process.
- Wenmode beta churn: make observed parser behaviour reviewable through a
  normative corpus and explicit upgrade reports.

## Requirements

### Functional requirements

- Treat the notation differences named by NF-1 to NF-3, and line-ending
  variants named by NF-8, as equivalent after normalization.
- Preserve the structural distinctions named by NF-4 to NF-7 and NF-9 to
  NF-13.
- Emit a deterministic `.mdast.json` payload without a version marker.
- Keep the normative parser and normalization contract machine-readable and
  discoverable from the documentation index.

### Technical requirements

- Construct a fresh Wenmode parser for each call using the GitHub profile and
  disabled positions.
- Apply the ordered normalization rules recursively to mappings and lists.
- Serialize the accepted value domain with the manifest's JSON writer and
  require strict UTF-8 encoding before passing payloads to Syrupy.
- Do not add JavaScript runtime, packages, or process boundaries.
- Make no compatibility promise with unified, remark, or
  `mdast-util-from-markdown` output.

## Options considered

The text-segmentation choice is independent of ADR-003's snapshot-version
marker decision.

### Option F: Retain Wenmode's text segmentation

Preserve every text-node boundary from Wenmode's `to_ast()` output. This is the
most literal reading of the initial design's transformations, but entity
references and backslash escapes can produce different payloads from equivalent
plain text when Wenmode splits a text run.

### Option G: Merge adjacent plain text nodes

Merge a run of adjacent sibling nodes only when every node has exactly `type`
and `value` members and `type` is `text`. This removes tokenizer boundary
variation while preserving nodes with extra metadata and every non-text
distinction. The rule runs before line-ending normalization. The maintainer
selected this direction on 2026-10-11; this ADR remains Proposed until its
written text is explicitly accepted.

| Factor                                          | Option F | Option G |
| ----------------------------------------------- | -------- | -------- |
| Insulates snapshots from tokenizer segmentation | No       | Yes      |
| Equates `a & b` with `a &amp; b`                | No       | Yes      |
| Merges nodes carrying additional members        | No       | No       |
| Adds a normalization rule beyond design §8      | No       | Yes      |

_Table 1: Text segmentation options._

## Decision outcome / proposed direction

Use the parser profile and canonicalization contract below. Option G is the
maintainer-selected text segmentation policy: merge exact-shape adjacent plain
text siblings before line-ending normalization. The payload has no version
marker and keeps the `.mdast.json` suffix, as decided in ADR-003.

### Contract manifest

This is the single normative manifest for snapshot contract v1. Its Wenmode
requirement, parser construction, normalization sequence, member order, and
writer settings are authoritative here; ADR-003 refers to this record rather
than copying the manifest.

```toml
[snapshot-contract]
contract-version = 1
wenmode = ">=0.15.2,<0.16.0"
parser = "Parser(github(), positions=False)"
file-extension = "mdast.json"
normalization = [
  "remove-position", "remove-empty-data", "merge-plain-text", "normalize-line-endings", "order-members",
]
key-order = [
  "type", "depth", "ordered", "start", "spread", "checked", "align", "lang", "meta",
  "url", "title", "alt", "identifier", "label", "value", "data", "children",
]

[snapshot-contract.json-writer]
encoding = "utf-8"
byte-order-mark = false
ensure-ascii = false
indent = 2
item-separator = ","
key-separator = ": "
allow-nan = false
sort-keys = false
trailing-newline = true
```

### Parser profile

The v1 construction is exactly
`Parser(github(), positions=False).parse(source).to_ast()`. Every call creates
a fresh parser. There are no plugins, `create_preset` calls, or custom rule
registrations, and this construction must emit no warnings. The GitHub profile
supplies CommonMark plus GFM tables, strikethrough, task lists, extended
autolinks, footnotes, and GitHub's disallowed-HTML policy. Frontmatter, math,
directives, and Markdown JSX (MDX) remain outside v1.

### Wenmode release

The requirement is `>=0.15.2,<0.16.0`, as directed by the maintainer on
2026-10-10. Wenmode 0.15.2 was released on 2026-10-01, is licensed under
BSD-3-Clause, and provides a pure-Python `py3-none-any` wheel for Python 3.10
and later. The wheel archive SHA-256 is
`a1be9a2d91ef7f5020148daf615edca0c9a4a6d54d074a808e6d5e9de95726f6`. This
baseline does not establish output equivalence for later 0.15.x versions in the
bounded requirement. ADR-003 owns the upgrade workflow and downstream
reproducibility policy.

### Normalization policy

Apply the manifest's rules recursively to every mapping and list, including
inside `data`, in this order:

1. `remove-position`: delete every member named `position`.
2. `remove-empty-data`: delete a `data` member whose value is an empty mapping.
3. `merge-plain-text`: replace each run of adjacent sibling nodes whose members
   are exactly `type` and `value`, with `type` equal to `text`, by one node
   whose `value` is their concatenation.
4. `normalize-line-endings`: replace CRLF, then bare CR, with LF in every
   string value, not in member names.
5. `order-members`: emit members in the manifest's `key-order`, then remaining
   members ordered by Unicode code point (Python's default `str` ordering, not
   JavaScript's UTF-16 ordering).

The preferred order groups node type, structural scalars, link and footnote
fields, value, data, and children. The probe confirms coverage of direct
node-member names observed in its 22-type GitHub-profile input. Normalization
preserves `False`, `0`, empty arrays, empty strings, non-empty `data`, unknown
fields, and `null` array elements. It does not synthesize `null` members for
fields Wenmode omits.

### Canonical JSON writer

The writer emits UTF-8 without a byte-order mark, unescaped Unicode, two-space
indentation, a comma item separator, a colon followed by one space as the key
separator, `allow_nan = false`, and one trailing LF. It does not sort keys
because normalization has already ordered them. The reference expression is:

```python
json.dumps(tree, ensure_ascii=False, indent=2, separators=(",", ": "),
           allow_nan=False) + "\n"
```

The value domain is mappings with string keys, lists, strings of Unicode scalar
values, integers, booleans, and `null`; validators check booleans before
integers. Values outside that domain are an `ast-shape` failure. The payload
must encode as strict UTF-8 before it is handed to Syrupy so a failure cannot
truncate a snapshot file. This record governs the string passed to Syrupy. Its
on-disk line ending remains a decision for before the first release whose
`serialize()` writes payloads; LF is recommended.

With `ensure_ascii = false`, the standard JSON writer escapes quotation marks,
backslashes, and U+0000 through U+001F (using short escapes where available and
lowercase `\u00xx` otherwise). It emits other Unicode literally, including
U+007F, C1 controls, U+2028, U+2029, and bidirectional controls. This escape
set is intentional; no custom encoder is introduced.

### Comparison contract

Two inputs are equivalent precisely when the same installed syrupy-mdast
version, Wenmode version, and parser profile produce byte-identical payloads in
the same interpreter environment. The integer contract version is a migration
signal, not the equivalence key. A bounded requirement permits several parser
versions; it does not prove their outputs identical. Python Unicode database
differences also limit promises across interpreter versions. ADR-003 defines
how payload differences affect package releases.

### Snapshot-version policy

ADR-003 is the source of truth for the no-marker decision, unchanged suffix,
contract-version lifecycle, release rules, and parser upgrade reports. This
record owns the bytes and profile to which that policy applies.

### Normative fixture decisions

"Equal" means the two inputs must produce byte-identical payloads; "distinct"
means they must not. The probe in `### Evidence` grounds the raw parser
observations for each item. It does not run canonicalization or establish the
canonical payload outcomes: merging text, normalizing line endings, and
ordering members remain obligations for the later corpus and canonicalizer
verification.

- NF-1. Emphasis delimiter spelling: `*a*` and `_a_`, and `**b**` and `__b__`,
  are equal.
- NF-2. Ordinary references: direct, full, collapsed, and shortcut forms are
  equal when destination, title, and children agree. A definition before its
  use resolves; label matching is case-insensitive while link text keeps its
  case; unused definitions leave no trace; unresolved references stay literal
  text. Reference images resolve to `image` with `url`, `alt`, and `title` when
  present.
- NF-3. Footnotes: `footnoteReference` and `footnoteDefinition` carry
  `identifier` and `label`, both case-folded by Wenmode, so `[^F]` and `[^f]`
  are equal. Definitions stay at their source position; moving one is distinct.
  Unused definitions are retained, repeated references repeat, and undefined
  references stay literal text.
- NF-4. Omitted nullable members: absent `title`, `lang`, `meta`, `checked`
  (non-task items), and `start` (bullet lists) stay absent; no `null` member is
  synthesized.
- NF-5. `null` array elements: an unaligned table column is `null` inside
  `align` and is preserved; alignment changes are distinct.
- NF-6. Raw HTML: `html` nodes keep their `value`. Tags on GitHub's disallowed
  list are rewritten by Wenmode to a leading `&lt;` with
  `data: {"escaped": true}`; this non-empty `data` is preserved, so filtered
  and unfiltered HTML are distinct.
- NF-7. Known divergence: CommonMark type-1 HTML blocks whose tag is on the
  disallowed list (`<script`, `<style`, `<textarea`) are not tag-filtered in
  0.15.2 and are ratified as observed. Other disallowed tags, including
  `<title>`, `<iframe>`, `<xmp>`, and `<plaintext>`, are filtered. An upstream
  fix is a payload change under ADR-003's upgrade policy. No upstream report is
  filed; the maintainer judged the divergence irrelevant to this implementation.
- NF-8. Line endings: LF, CRLF, and CR inputs produce equal payloads after
  `normalize-line-endings`, including in text, code values, and titles. Parsed
  structure (paragraphs and hard breaks) is already equal.
- NF-9. Positions: payloads never contain `position`. The parser uses
  `positions=False`, and `remove-position` removes it if a future parser emits
  it anyway.
- NF-10. Preserved distinctions: hard break versus soft line break; code
  whitespace, `lang`, and `meta`; list `ordered`, `start`, `spread`, item
  `checked`, and item order; table cell content and alignment; raw HTML
  spelling.
- NF-11. Text segmentation: Wenmode splits text at entity references and
  backslash escapes; `merge-plain-text` rejoins adjacent plain text nodes.
  Therefore `a & b` equals `a &amp; b`, and `a*b` equals `a\*b`. A text node
  with any member besides `type` and `value` is never merged.
- NF-12. Key order and coverage: every emitted mapping's members follow the
  manifest's `key-order`, then remaining members by code point. Every member
  name observed directly on the 22 node types in the probe is in `key-order`; a
  contract fixture pins one node of every type.
- NF-13. Numeric character references: `&#0;` becomes U+FFFD;
  `&#xD800;` and `&#x110000;` stay literal text; no lone surrogate reaches a
  payload.

### Evidence

The following self-checking probe records Wenmode's raw output. The normative
fixture policy above includes canonicalization rules applied after this output.
The probe does not execute text merging, line-ending normalization, member
ordering, or the JSON writer. Its key check collects direct node-member names
from its 22-type input, not nested metadata names such as `data.escaped`. Those
remaining outcomes are verified by later corpus, canonicalizer, and writer
tests.

```python
"""Self-checking probe of Wenmode's GitHub profile for ADR-003 (contract v1)."""

import json
from importlib.metadata import version

from wenmode import Parser
from wenmode.presets import github

KEY_ORDER = (
    "type", "depth", "ordered", "start", "spread", "checked", "align", "lang", "meta",
    "url", "title", "alt", "identifier", "label", "value", "data", "children",
)
NODE_TYPES = (
    "blockquote", "break", "code", "delete", "emphasis", "footnoteDefinition",
    "footnoteReference", "heading", "html", "image", "inlineCode", "link", "list",
    "listItem", "paragraph", "root", "strong", "table", "tableCell", "tableRow", "text",
    "thematicBreak",
)
ESCAPED = {"escaped": True}


def ast(source: str) -> dict:
    """Parse one source with the v1 construction."""
    return Parser(github(), positions=False).parse(source).to_ast()


def kids(source: str) -> list:
    """Return the root children for one source."""
    return ast(source)["children"]


def para(*children: dict) -> dict:
    """Build a paragraph node."""
    return {"type": "paragraph", "children": list(children)}


def text(value: str) -> dict:
    """Build a text node."""
    return {"type": "text", "value": value}


def html(value: str, *, escaped: bool = False) -> dict:
    """Build an html node, marked escaped when Wenmode's tag filter applied."""
    return {"type": "html", "data": ESCAPED, "value": value} if escaped else {"type": "html", "value": value}


def check(label: str, *conditions: bool) -> None:
    """Print one verdict and fail loudly on any mismatch."""
    if not all(conditions):
        raise SystemExit(f"{label} FAILED")
    print(label, "ok")


LINK = {"type": "link", "children": [text("x")], "url": "/u", "title": "t"}
REF = {"type": "footnoteReference", "identifier": "f", "label": "f"}
DEF = {"type": "footnoteDefinition", "children": [para(text("d"))], "identifier": "f", "label": "f"}
REFERENCE_FORMS = (
    '[x](/u "t")\n', '[x][r]\n\n[r]: /u "t"\n', '[x][]\n\n[x]: /u "t"\n',
    '[x]\n\n[x]: /u "t"\n', '[r]: /u "t"\n\n[x][r]\n',
)
TYPE_ONE_BLOCKS = ("<script>x</script>\n", "<style>p{}</style>\n", "<textarea>\nq\n</textarea>\n")
EVERY_NODE = (
    "# h\n\n> q\n\n- [ ] t\n1. o\n\n```py m\nc\n```\n\n    i\n\n***\n\n<div>\n</div>\n\n"
    'a `c` **s** *e* ~~d~~ [l](/u "t") ![i](/p "t") <span> www.x.y  \nz[^n]\n\n'
    "| a |\n|:-|\n| b |\n\n[^n]: f\n\n<iframe>\n"
)

check("NF-1 emphasis", kids("*a* **b**\n") == kids("_a_ __b__\n"))
check(
    "NF-2 references",
    all(kids(source) == [para(LINK)] for source in REFERENCE_FORMS),
    kids("[x][nope]\n") == [para(text("[x][nope]"))],
    kids("text\n\n[u]: /unused\n") == [para(text("text"))],
    kids("[Foo]\n\n[FOO]: /u\n")[0]["children"][0]["children"] == [text("Foo")],
    kids("![alt][i]\n\n[i]: /i.png\n") == [para({"type": "image", "url": "/i.png", "alt": "alt"})],
)
check(
    "NF-3 footnotes",
    kids("[^f]: d\n\nr[^f]\n") == [DEF, para(text("r"), REF)],
    kids("r[^f]\n\n[^f]: d\n") == [para(text("r"), REF), DEF],
    kids("r[^F]\n\n[^f]: d\n") == kids("r[^f]\n\n[^f]: d\n"),
    kids("x\n\n[^u]: d\n")[1]["type"] == "footnoteDefinition",
    kids("x[^u]\n") == [para(text("x[^u]"))],
    [node["type"] for node in kids("a[^f] b[^f]\n\n[^f]: d\n")[0]["children"]].count("footnoteReference") == 2,
)
check(
    "NF-4 omitted members",
    kids("[x](/u)\n") == [para({"type": "link", "children": [text("x")], "url": "/u"})],
    kids("```\nc\n```\n") == [{"type": "code", "value": "c\n"}],
    "checked" not in kids("- a\n")[0]["children"][0],
    "start" not in kids("- a\n")[0],
)
check("NF-5 null elements", kids("| a | b |\n|---|:-:|\n| 1 | 2 |\n")[0]["align"] == [None, "center"])
check(
    "NF-6 disallowed html",
    kids("<iframe src=a></iframe>\n") == [html("&lt;iframe src=a>&lt;/iframe>\n", escaped=True)],
    kids("x <script>y</script>\n")[0]["children"][1] == html("&lt;script>", escaped=True),
    kids("<title>t</title>\n") == [html("&lt;title>t&lt;/title>\n", escaped=True)],
    kids("<div>\nhi\n</div>\n") == [html("<div>\nhi\n</div>\n")],
)
check("NF-7 type-1 divergence", all(kids(source) == [html(source)] for source in TYPE_ONE_BLOCKS))
check(
    "NF-8 line endings survive into strings",
    kids("a\r\nb\r\n") == [para(text("a\r\nb"))],
    kids("a\rb\r") == [para(text("a\rb"))],
    kids("```\r\nx\r\n```\r\n") == [{"type": "code", "value": "x\r\n"}],
    kids('[x](/u "a\r\nb")\n')[0]["children"][0]["title"] == "a\r\nb",
    kids("a\r\rb\r") == kids("a\n\nb\n"),
    len(kids("a  \r\nb\r\n")[0]["children"]) == 3,
)
check("NF-9 no positions", "position" not in json.dumps(ast("# T\n\n- a\n")))
check(
    "NF-10 preserved distinctions",
    kids("a  \nb\n") != kids("a\nb\n"),
    kids("```py x\n  c \n```\n") == [{"type": "code", "value": "  c \n", "lang": "py", "meta": "x"}],
    kids("3. a\n")[0]["start"] == 3,
    kids("- [x] a\n")[0]["children"][0]["checked"] is True,
)
check(
    "NF-11 text segmentation",
    kids("&amp; &copy;\n") == [para(text("&"), text(" "), text("©"))],
    kids("\\*x\\*\n") == [para(text("*"), text("x"), text("*"))],
    kids("a & b\n") == [para(text("a & b"))],
)

seen: dict[str, set[str]] = {}


def collect(node: dict) -> None:
    """Record member names per node type, recursing through children."""
    seen.setdefault(node["type"], set()).update(node)
    for child in node.get("children", []):
        collect(child)


collect(ast(EVERY_NODE))
check("NF-12 key coverage", set(seen) == set(NODE_TYPES), set().union(*seen.values()) <= set(KEY_ORDER))
check(
    "NF-13 numeric references",
    kids("&#0;\n") == [para(text("�"))],
    kids("&#xD800;\n") == [para(text("&#xD800;"))],
    kids("&#x110000;\n") == [para(text("&#x110000;"))],
)
print("version", version("wenmode"))
```

Run the probe with Wenmode 0.15.2 and warnings treated as errors:

```bash
mkdir -p /tmp/wenmode-probe
cd /tmp/wenmode-probe && uv run --no-project --with wenmode==0.15.2 python -W error probe.py
```

Expected output, exactly (apart from an optional `uv` installation line):

```plaintext
NF-1 emphasis ok
NF-2 references ok
NF-3 footnotes ok
NF-4 omitted members ok
NF-5 null elements ok
NF-6 disallowed html ok
NF-7 type-1 divergence ok
NF-8 line endings survive into strings ok
NF-9 no positions ok
NF-10 preserved distinctions ok
NF-11 text segmentation ok
NF-12 key coverage ok
NF-13 numeric references ok
version 0.15.2
```

The probe was run on 2026-10-10 against Wenmode 0.15.1 and 0.15.2 under
`-W error`; all thirteen checks passed on both. The final version line differed
as expected. These named cases do not classify all upstream changes or prove
payload neutrality outside the tested inputs. The 0.15.2 wheel hash and release
details were checked against
[PyPI release metadata](https://pypi.org/pypi/wenmode/0.15.2/json) on
2026-10-10, selecting `urls[].digests.sha256` for the wheel archive; the
distinct `core-metadata.sha256` describes the metadata file, not the archive.
The policy is informed by Wenmode's
[compatibility documentation](https://wenmode.lepture.com/compatibility/) and
[changelog](https://wenmode.lepture.com/changelog/), and the
[GFM specification](https://github.github.com/gfm/).

### Versioning policy

[ADR-003](adr-003-snapshot-version-policy.md) defines package releases,
contract-version changes, and the Wenmode upgrade workflow. It owns versioning
policy independently of this normalization record.

### Amendments

Before the first release whose `serialize()` writes payloads, a correction to
the v1 payload definition may be recorded here as a dated amendment. After that
release, a payload-definition change requires a new normalization ADR, which
supersedes this record. Changes to snapshot-version policy belong in ADR-003
and do not by themselves supersede this record.

## Goals and non-goals

- Goals:
  - Define one complete, versioned source for the v1 parser profile,
    normalization, comparison, and canonical writer.
  - Suppress only representation differences named by the normative fixtures.
  - Preserve structural distinctions that can affect parsed content or
    rendered output.
  - Keep parsing, canonicalization, packaging, and failure handling within the
    Python package and process.
- Non-goals:
  - Guarantee byte compatibility with unified, remark, or
    `mdast-util-from-markdown`.
  - Prove that equivalent payloads render to identical Hypertext Markup
    Language (HTML).
  - Parse raw HTML nodes into a Hypertext Abstract Syntax Tree (hast).
  - Collapse general whitespace, rewrite footnote identifiers, or preserve
    ordinary reference source structure.
  - Expose user-defined normalizers, parser profiles, or plugins in v1.
  - Compare caller-supplied AST objects or provide process isolation and a hard
    wall-clock timeout for hostile input.
  - Promise byte-identical files on disk across platforms; the on-disk line
    terminator remains a separate decision.

## Migration plan

1. Accept ADR-003 and this ADR before committing implementation or fixture
   changes.
2. Add the lasting contract corpus and parser probes, with each fixture linked
   to an NF identifier and with the 22 node types represented.
3. Implement the per-call parser, recursive normalization, key ordering, and
   canonical writer to match this record and its manifest.
4. Add the manifest and source-contract checks, then decide the on-disk line
   ending before the first release whose `serialize()` writes payloads.
5. Follow ADR-003's dedicated Wenmode upgrade report for any requirement or
   repository-resolved release change.

## Known risks and limitations

- **Beta parser behaviour.** Wenmode may change AST output for inputs outside
  the probe and committed corpus. ADR-003's upgrade report classifies corpus
  diffs and upstream changelog entries, but finite fixtures cannot establish
  universal parser stability.
- **GFM divergence.** The type-1 HTML behaviour in NF-7 differs from GFM's
  disallowed-tag filtering. An upstream fix changes payloads; the maintainer
  decided no upstream report should be filed.
- **On-disk line terminators.** Syrupy 5 and 6 open single-file snapshots in
  text mode without a `newline` argument, so Windows may write CRLF while CI
  runs on Ubuntu. Decide the on-disk line ending before the first payload
  release; LF is recommended.
- **Interpreter Unicode data.** Python Unicode database versions can affect
  label case folding and punctuation classification for emphasis flanking. The
  same package and parser versions may produce different bytes across
  interpreters for exotic input; the contract makes no general
  cross-interpreter promise where Unicode data affects parsing.
- **Writer escapes.** C1 controls, U+2028, U+2029, and bidirectional controls
  are emitted literally. This follows the standard-library writer settings, but
  such values may not be visually harmless in every diff viewer.
- **Formatter changes.** JSON formatters may rewrite snapshots, including
  sorting keys, and cause assertion failures. Snapshot files must be excluded
  from formatters that rewrite the contract's JSON text.
- **Exact-shape text merging.** Merging insulates snapshots from Wenmode's
  segmentation at entities and escapes, but only when nodes have exactly the
  `type` and `value` members.

## Outstanding decisions

None. The maintainer selected Option G on 2026-10-11. The written record
remains Proposed until it is explicitly accepted.
