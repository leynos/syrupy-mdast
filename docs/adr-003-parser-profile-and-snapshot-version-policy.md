# Architectural decision record (ADR) 003: Snapshot contract v1 — parser profile and snapshot-version policy

## Status

Proposed.

## Date

2026-10-10.

## Context and problem statement

Raw Markdown snapshots report changes to delimiters, wrapping, and source
positions even when the interpreted document structure is unchanged. That noise
trains reviewers to accept broad snapshot updates and makes meaningful changes
harder to identify. `syrupy-mdast` instead compares a canonical,
mdast-compatible abstract syntax tree (AST) and stores it as readable JSON.

The [technical design](syrupy-mdast-design.md) §11 requires an explicitly
versioned ADR before implementation or fixture changes. The record must state
the parser profile, normalization policy, comparison contract, snapshot-version
policy, Wenmode release policy, and normative fixtures. Until now, the exact
meaning of the snapshot version, Wenmode release, and fixture decisions was
open. This proposal fixes contract v1 as a complete record and manifest so
future implementation and review can be checked against one source.

Wenmode is beta software, and its AST is the persisted snapshot format. The
maintainer has selected the bounded requirement `>=0.15.2,<0.16.0`. The 0.15.2
release is the reproducible evidence baseline for this proposal; the finite
probe does not establish identical output for every later release allowed by
that range.

## Decision Drivers

- Reviewability: suppress source-notation noise while preserving meaningful
  structure and readable diffs, as required by design §1.
- Determinism: define parser construction, normalization order, member order,
  JSON spelling, and the bytes passed to Syrupy.
- Wenmode beta churn: make parser moves visible and classify payload changes
  before they reach snapshots.
- Python-only boundary: keep parsing, canonicalization, packaging, and failure
  handling within the Python package and process.
- Conservative equivalence: promise byte equality only for the same installed
  package and Wenmode versions, parser profile, and interpreter environment.
- Protection from automatic dependency updates: keep the repository's Wenmode
  updates under explicit review.

## Requirements

### Functional requirements

- Treat equivalent Markdown notation, source positions, and line-ending
  variants as equivalent where the normative fixtures specify.
- Preserve structural distinctions that can affect interpretation or
  rendering, including hard breaks, code whitespace, list structure, table
  alignment, footnotes, and raw HTML.
- Produce deterministic, reviewable `.mdast.json` payloads for the fixed v1
  profile.
- Make payload changes visible through ordinary Syrupy diffs and release notes.

### Technical requirements

- Use Wenmode's GitHub profile through one fresh parser per call, with source
  positions disabled and no plugins or custom rule registration.
- Specify the complete normalization sequence, preferred member order, and
  canonical JSON writer in one machine-readable manifest.
- Keep the runtime and wheel Python-only; introduce no JavaScript runtime,
  package, or process boundary.
- Classify every repository-resolved Wenmode move with a corpus diff and an
  upgrade report, and prevent automatic repository updates from bypassing
  review.
- Make no promise of byte compatibility with unified, remark, or
  `mdast-util-from-markdown`, or across different parser/interpreter versions.

## Options considered

Two independent decisions are considered here: how the payload communicates its
contract version, and whether canonicalization preserves Wenmode's text
segmentation.

### Option A: No version marker

Keep the payload as the canonical tree alone and retain the `.mdast.json`
suffix. Ordinary Syrupy diffs show affected snapshots, while the package's
release notes and users' guide map package releases to contract versions. This
avoids changing every payload on each contract-version increment.

### Option B: In-payload version member

Add a contract-version member to every serialized tree. This makes the version
visible in each file, but changes every snapshot at every version increment
even when the tree itself is unchanged. It also adds a member that is not part
of Wenmode's canonical tree.

### Option C: Versioned file suffix

Change the extension to include the contract version. This keeps version
metadata outside the payload, but changes every snapshot path at each version
increment and risks leaving old snapshots that Syrupy reports as unused.

### Option D: Header with taint

Add a serializer-version header that marks snapshots with an unfamiliar version
as tainted. Syrupy's amber serializer uses this model, but a tainted snapshot
fails comparison even when the content is identical. It would force broad
updates and does not match the current single-file extension's comparison
behaviour.

### Option E: Informational header ignored by comparison

Add a version header that does not affect comparison, as in tools that treat
metadata as informational. This avoids taint but still adds parser and writer
policy outside the canonical tree, and a future metadata change would need
separate comparison semantics.

| Factor                                  | Option A | Option B | Option C            | Option D       | Option E                   |
| --------------------------------------- | -------- | -------- | ------------------- | -------------- | -------------------------- |
| Payload remains the canonical tree      | Yes      | No       | Yes                 | No             | No                         |
| Changes all snapshots on a version bump | No       | Yes      | Paths change        | Yes            | Header changes             |
| Compatible with ordinary Syrupy diffs   | Yes      | Yes      | Risk of stale paths | No             | Requires custom comparison |
| Adds comparison or storage machinery    | No       | No       | No                  | Taint handling | Header handling            |

_Table 1: Payload versioning options._

### Option F: Retain Wenmode's text segmentation

Preserve every text node boundary from `to_ast()`. This is the most literal
interpretation of the original design's listed transformations, but makes
entity references and backslash escapes differ from equivalent plain text when
Wenmode splits a text run.

### Option G: Merge adjacent plain text nodes

Merge a run of adjacent sibling nodes only when each node has exactly `type` and
`value` members and `type` is `text`. This removes the tokenizer boundary
variation while preserving nodes with extra metadata and every non-text
distinction. The rule must run before line-ending normalization.

| Factor                                          | Option F | Option G |
| ----------------------------------------------- | -------- | -------- |
| Insulates snapshots from tokenizer segmentation | No       | Yes      |
| Equates `a & b` with `a &amp; b`                | No       | Yes      |
| Merges nodes carrying additional members        | No       | No       |
| Adds a normalization rule beyond design §8      | No       | Yes      |

_Table 2: Text segmentation options._

## Decision outcome / proposed direction

Adopt Option A for payload versioning and Option G for text segmentation,
subject to acceptance of this ADR. The payload remains the canonical tree. The
normalization policy merges only adjacent plain text siblings with the exact
two-member shape before normalizing line endings.

### Contract manifest

The following is the single normative manifest for snapshot contract v1:

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

The v1 parser construction is exactly
`Parser(github(), positions=False).parse(source).to_ast()`. Each call creates a
fresh parser. There are no plugins, `create_preset` calls, or custom rule
registrations. The parser must emit no warnings. The GitHub profile supplies
CommonMark plus GitHub Flavoured Markdown (GFM) tables, strikethrough, task
lists, extended autolinks, footnotes, and GitHub's disallowed-HTML policy.
Frontmatter, math, directives, and Markdown JSX (MDX) remain outside v1.

### Wenmode release

The proposed requirement is `>=0.15.2,<0.16.0`, as directed by the maintainer
on 2026-10-10. Wenmode 0.15.2 is the empirical evidence baseline: it was
released on 2026-10-01, is licensed under BSD-3-Clause, and provides a pure
Python `py3-none-any` wheel for Python 3.10 and later. The wheel's SHA-256 is
`a1be9a2d91ef7f5020148daf615edca0c9a4a6d54d074a808e6d5e9de95726f6`. The
evidence baseline does not claim that later 0.15.x releases allowed by the
requirement have identical output. An exact pin would constrain this
repository's resolution more tightly, but the maintainer explicitly selected
the bounded requirement. Consumers who need reproducible parser output should
lock their test dependencies.

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

The key order groups node type, structural scalars, link and footnote fields,
value, data, and children. The probe confirms coverage of direct node-member
names observed in its 22-type GitHub-profile input. This version preserves
`False`, `0`, empty arrays, empty strings, non-empty `data`, unknown fields, and
`null` array elements. It does not synthesize `null` members for fields
Wenmode omits.

### Canonical JSON writer

The writer emits UTF-8 without a byte-order mark, with unescaped Unicode,
two-space indentation, separators `,` and `:`, `allow_nan = false`, and one
trailing LF. It does not sort keys because normalization has already ordered
members. The reference expression is:

```python
json.dumps(tree, ensure_ascii=False, indent=2, separators=(",", ": "),
           allow_nan=False) + "\n"
```

The accepted value domain is mappings with string keys, lists, strings of
Unicode scalar values, integers, booleans, and `null`; validators check
booleans before integers. Values outside that domain are an `ast-shape`
failure. Before handing the payload to Syrupy, encode it as strict UTF-8 so a
failure cannot truncate a snapshot file. The contract ends at the string handed
to Syrupy. Its on-disk line ending remains a decision for before the first
release whose `serialize()` writes payloads; LF is recommended.

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
differences also limit promises across interpreter versions.

### Snapshot-version policy

The payload carries no version marker and its suffix remains `.mdast.json`.
Payload changes appear as ordinary Syrupy diffs of affected snapshots, with the
reason explained in release notes. The users' guide maps package releases to
contract versions. Adding a marker later is itself a payload change.

The contract version is an integer beginning at 1. Before the first release
whose `serialize()` writes payloads, contract v1 may be corrected in place by
dated entries under `### Amendments`. After that release, editorial
clarifications and requirement changes classified as payload-neutral may be
dated amendments, with `## Date` meaning "last updated". Any change to the
definition of the payload requires a new contract version in a new ADR; this
ADR then becomes `Superseded (YYYY-MM-DD) by ADR-NNN.`

Deliberate syrupy-mdast code changes are evaluated with the same installed
parser. A knowingly adopted Wenmode requirement or repository-resolved release
move is compared across the old and new parser releases. Any known payload
difference, whether caused by a contract change, canonicalizer conformance fix,
or non-neutral parser move, follows these release rules:

1. Deliberate syrupy-mdast patch-release changes, evaluated with the same
   installed parser, never knowingly change a payload. A downstream parser
   update within the approved range can change payloads without a syrupy-mdast
   release; this policy cannot freeze unlocked consumer installations.
2. Before 1.0.0, a payload change requires a minor release
   (`0.y.z` to `0.(y+1).0`); from 1.0.0, it requires a major release. Release
   notes list affected constructs and the
   review-then-`pytest --snapshot-update` step.
3. A contract-version increment signals a change to the payload definition,
   including the parser profile, normalization rules, key order, or writer. It
   is not the equivalence key.
4. Every change to the Wenmode requirement or repository-resolved release
   lands in a dedicated pull request with the roadmap 3.2.1 upgrade report. The
   report compares the corpus and classifies every intervening Wenmode
   changelog entry as an addition, parser fix, intentional migration, or
   regression. Each entry that can affect GitHub-profile `to_ast()` output gets
   a fixture. A move is payload-neutral only when the corpus diff is empty and
   every relevant entry has a fixture with no change. Any warning from the v1
   construction under `-W error` blocks the move.
5. Dependabot does not propose Wenmode updates. The pip block gains an
   `ignore` entry for `wenmode`; roadmap 1.2.1 adds this protection and a
   contract check.
6. Upgrade evaluation is triggered by a new Wenmode release, Wenmode 1.0, a
   Wenmode security advisory, or a newly supported Python minor version. A
   security advisory ships promptly under the applicable version rule and is
   named in the release notes.

The current requirement allows a later parser patch to reach unlocked
installations before a syrupy-mdast release. The repository's Dependabot ignore
protects this repository's reviewed updates; it does not freeze downstream
resolution. Consumers should lock their test dependencies when they need to
reproduce parser output. A downstream lock refresh may change payload bytes
without a syrupy-mdast package release, producing ordinary Syrupy diffs.
Installing syrupy-mdast in a test-only dependency group limits conflicts with
other Wenmode requirements. No runtime version-enforcement mechanism or extra
dependency is introduced.

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
  fix is a payload change under this policy. No upstream report is filed; the
  maintainer judged the divergence irrelevant to this implementation.
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
fixture policy above also includes canonicalization rules applied after this
output. The probe does not execute text merging, line-ending normalization,
member ordering, or the JSON writer. Its key check collects direct node-member
names from its 22-type input, not nested metadata names such as `data.escaped`.
Those remaining outcomes are verified by later corpus, canonicalizer, and
writer tests.

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
as expected. This verifies the named cases only; it does not classify all
upstream changes or prove payload neutrality outside those examples. The 0.15.2
wheel hash and release details above were checked against
[PyPI release metadata](https://pypi.org/pypi/wenmode/0.15.2/json) on that
date, selecting `urls[].digests.sha256` for the wheel archive; the distinct
`core-metadata.sha256` describes the metadata file, not that archive. The
policy is informed by Wenmode's
[compatibility documentation](https://wenmode.lepture.com/compatibility/) and
[changelog](https://wenmode.lepture.com/changelog/), and the
[GFM specification](https://github.github.com/gfm/).

### Amendments

No amendments are recorded. Before the first release whose `serialize()` writes
payloads, dated pre-release corrections may be recorded here. After that
release, `## Date` means the last update date, and any change to the payload
definition requires a new, superseding contract ADR.

## Goals and non-goals

- Goals:
  - Define one complete, versioned source for v1 parser, normalization,
    comparison, and snapshot-version policy.
  - Suppress representation noise while preserving the structural distinctions
    named by NF-1 to NF-13.
  - Keep snapshot generation within the Python package and process.
- Non-goals:
  - Guarantee byte compatibility with unified, remark, or
    `mdast-util-from-markdown`.
  - Prove that equivalent payloads render to identical HTML.
  - Preserve ordinary reference-link syntax or unused ordinary definitions.
  - Parse raw HTML into a Hypertext Abstract Syntax Tree (hast).
  - Collapse general whitespace or rewrite footnote identifiers.
  - Expose custom parser profiles, normalizers, or plugins in v1.
  - Compare caller-supplied ASTs or provide process isolation and a hard
    wall-clock timeout for hostile input.
  - Add opt-in frontmatter, math, directive, or MDX profiles; policy switches
    such as ignored table alignment; preservation of ordinary reference source
    structure; HTML-to-hast normalization; or a Python worker for hostile-input
    isolation and timeouts.
  - Promise byte-identical files on disk across platforms; on-disk line
    terminators are outside the current payload contract.

## Migration plan

The proposal is implemented only after ADR acceptance. Pull request A carries
the plan and this proposed ADR and merges after explicit acceptance. Pull
request B starts from the updated `main` after A merges and carries the guard
and document reconciliation. Roadmap tasks own the changes and fixtures in this
sequence:

1. **Roadmap 1.1.3:** add the lasting normative corpus, with each fixture
   identifying the NF rule it discharges. The optional
   `mdast-util-from-markdown` differential run remains unshipped and outside CI.
2. **Roadmap 1.2.1:** declare the exact manifest requirement
   `>=0.15.2,<0.16.0`; configure Dependabot to ignore Wenmode; add a contract
   that checks the requirement against this manifest.
3. **Roadmap 1.2.2:** implement the per-call parser construction and require
   it to agree with the manifest.
4. **Roadmap 1.2.3:** commit the parser probes and verify key coverage against
   the GitHub-profile node model.
5. **Roadmap 2.1.1:** update the parser-construction wording to the exact v1
   profile.
6. **Roadmap 2.1.2:** implement the recursive normalization sequence and
   preferred member order; check canonicalizer invariants with property and
   symbolic tests where appropriate.
7. **Roadmap 2.2.1:** implement the canonical writer and reject payloads that
   cannot encode as strict UTF-8 before passing them to Syrupy.
8. **Roadmap 2.3.1:** decide the on-disk line ending before the first release
   whose `serialize()` writes payloads.
9. **Roadmap 3.2.1:** maintain the dedicated Wenmode upgrade report, classify
   corpus changes and upstream changelog entries, add fixtures for relevant
   behaviour changes, and block a move that emits a warning under `-W error`.

Every pull request changing the Wenmode requirement or repository-resolved
release must stand alone and include that upgrade report. Consumer lockfiles
are recommended for reproducibility but are not a production restriction.

## Known risks and limitations

1. **Beta parser changes.** A later Wenmode release may change AST output for
   inputs outside the corpus, so a parser move that appears neutral on current
   fixtures can alter user payloads. This risk is high severity and medium
   likelihood: 0.15.1 changed list tightness and autolink boundaries. The
   dedicated upgrade report must classify changelog entries as well as corpus
   diffs, add fixtures for behaviour-changing entries, and require explicit
   review.
2. **Automatic updates.** Severity high; likelihood high once Wenmode is a
   dependency. Dependabot's pip grouping and automerge path could silently
   upgrade Wenmode. The repository will ignore Wenmode updates and require an
   executable contract for that policy.
3. **GFM divergence.** Severity medium; likelihood medium. The ratified
   type-1 HTML behaviour differs from GFM's disallowed-tag filtering. An
   upstream fix changes payloads. The maintainer judged this divergence
   irrelevant to the implementation, so no upstream report is filed.
4. **Formatter changes.** Severity medium; likelihood medium. JSON formatters
   may rewrite snapshots, including sorting keys, after which assertions fail.
   Snapshot files must be excluded from such formatters; the canonical JSON
   text comparison intentionally surfaces rewrites.
5. **On-disk line terminators.** Severity medium; likelihood medium. Syrupy 5
   and 6 open single-file snapshots in text mode without a `newline` argument,
   so Windows may write CRLF while CI runs on Ubuntu. The on-disk line ending
   must be decided before the first release that writes payloads; LF is
   recommended.
6. **Interpreter Unicode data.** Severity low; likelihood low. Python Unicode
   database versions can affect case folding of labels and punctuation
   classification for emphasis flanking. The same package and parser versions
   may produce different bytes across interpreters for exotic input. The
   contract makes no general cross-interpreter promise where Unicode data
   affects parsing.
7. **Bounded range exposure.** Severity medium; likelihood low. The approved
   range can conflict with a downstream project's other Wenmode requirements,
   and a security fix outside the range requires a syrupy-mdast release. Fixes
   within the range can reach consumers on lock refresh. Upgrade reports and a
   test-only dependency group reduce, but do not remove, that exposure.
8. **Warnings become errors.** Severity low; likelihood medium. Wenmode uses
   `DeprecationWarning` to signal API changes. User suites may treat warnings
   as errors. The probe runs with `-W error`, and any warning from the v1
   parser construction blocks a move.
9. **Unlocked downstream resolution.** An unlocked consumer may resolve a
   later allowed parser patch without a syrupy-mdast release and observe
   ordinary snapshot diffs. The repository's Dependabot ignore protects this
   repository only. Locking test dependencies is the recommended way to
   reproduce parser output; no runtime version enforcement is introduced.

The exact-shape merge rule equates plain text split by entity and escape
tokenization, but never merges text nodes carrying extra members. The writer
also emits C1 controls, U+2028, U+2029, and bidirectional controls literally.
These are deliberate limitations of the standard-library JSON writer, not
claims that such values are visually harmless in every diff viewer.

## Outstanding decisions

None. The maintainer settled the three previously open questions on 2026-09-28:
merge adjacent plain text nodes, omit a payload version marker, and do not file
an upstream report about the GFM tag-filter divergence. The maintainer's
2026-10-10 requirement direction resolves the Wenmode release choice. This ADR
remains Proposed until its written text is explicitly accepted.
