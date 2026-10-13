<!-- markdownlint-disable MD012 -->
<!-- ExecPlans require two blank lines after headings. -->

# Create the canonical Markdown contract corpus


Status: DRAFT — awaiting explicit approval before implementation.

Roadmap task: **1.1.3**. Prerequisite: **1.1.2**, completed at baseline
`c19afee8ed735dffa6262cf0b2e0a9ca0a5a0551`.

This execution plan is a living document. Keep its constraints, tolerances,
risks, progress, discoveries, decisions, conformance basis, verification plan,
and outcomes current at every milestone. Publication of this plan does not
approve its implementation.

## Purpose / big picture


Create a small, reviewable specification corpus that gives later parser and
canonicalizer work an independent expected result. A contributor should be able
to find the exact input, expected canonical JSON, and reason why a
representation difference disappears or a structural distinction survives.
Every rule in technical design §8 and accepted ADR-004 must have a named case.

Success for this task means complete, internally consistent fixtures with
meaningful integrity tests. It does **not** mean Markdown serialization is
implemented. The current extension deliberately raises `NotImplementedError`;
parsing, canonicalization, writing, and native Syrupy integration belong to
later roadmap tasks. Preserve this distinction in test names and completion
claims. Future implementation tests must consume these expected results rather
than regenerate them from the implementation under test.

## Constraints


- Obtain explicit approval of this plan before changing fixtures, tests, or
  implementation. This planning pull request changes documentation only.
- Accepted [ADR-004](../adr-004-parser-profile-and-normalization.md) governs
  parser construction, normalization, and normative fixtures (NF-1 to NF-13).
  [ADR-003](../adr-003-snapshot-version-policy.md) governs versioning. Preserve
  contract version 1, its no-marker policy, and its comparison scope.
- Keep the Python-only package boundary. Do not introduce a Rust extension,
  JavaScript oracle, parser dependency, production canonicalizer, writer, or
  changes under `syrupy_mdast/`. Do not implement later roadmap tasks early.
- Keep source bytes, array order, and authored expected payloads intact.
  No formatting, newline conversion, sorting, or snapshot update command may
  silently change fixture semantics.
- Put tests and test support beneath `tests/`; keep each Python file below
  400 lines. Use precise types, narrow errors, and no generic plugin framework.
- Run format, type, lint, test, and audit gates sequentially before each code
  commit; run Markdown and Mermaid gates for documentation. Never overlap gates
  or interfere with another agent's processes or build admission.
- Mark roadmap 1.1.3 done only after implementation acceptance, not when this
  plan is published or approved.

## Tolerances (exception triggers)


Stop, record evidence and options in the decision log, set status to `BLOCKED`,
and seek explicit direction if any of these conditions occurs:

- A normative expected result contradicts accepted ADR-004, or satisfying a
  case requires a new comparison rule, public interface, or runtime dependency.
- Work requires modifying production modules, CI, Makefile recipes, or adding
  any dependency. Neither a second canonicalizer nor compatibility shims are
  permitted as a shortcut to a green corpus suite.
- The implementation needs more than four new Python files or 600 total new
  Python lines, excluding fixtures and documentation. Split data by concern; do
  not hide executable logic in data. More than 100 named cases requires a scope
  review; the matrix below is mandatory and may not be trimmed to fit.
- A failing gate remains unexplained after three targeted repair attempts.
  An infrastructure failure is not evidence of a source defect. Preserve the
  log and wait for recovery rather than bypassing the standard tool.
- An upstream version, profile, or Unicode behaviour changes an expected
  result. ADR-003's upgrade policy applies; do not refresh fixtures blindly.

There is no elapsed-time deadline. A slow shared compiler or package-cache lock
is not a reason to cancel, duplicate, or bypass a gate.

## Risks


- **False confidence from self-comparison (high impact, medium likelihood).**
  Integrity checks can show that fixtures agree with each other, not that a
  future implementation is correct. Author expected payloads from ADR-004,
  review concrete field assertions, and label all remaining parser and
  canonicalizer obligations as deferred.
- **Whitespace corruption (high impact, medium likelihood).** Markdown
  formatters and universal-newline reads can erase the distinction under test.
  Use `.txt` source fixtures, byte reads followed by strict UTF-8 decoding, and
  Git attributes that disable newline conversion for corpus data.
- **Overbroad cases (medium impact, medium likelihood).** One large document can
  conceal which rule failed. Use focused cases; the one all-node document is
  supplementary coverage, never the sole evidence for a rule.
- **Design drift (high impact, known).** Design §8 omits the accepted
  `merge-plain-text` rule. ADR-004 takes precedence. Reconcile §8 without
  inventing new semantics or reopening the accepted choice.
- **Parser provenance (medium impact, medium likelihood).** Wenmode 0.15.2 is
  ADR-004's evidence baseline, not a claim about every allowed 0.15.x release.
  Distinguish authored canonical expectations from observed raw parser output.

## Progress


- [x] (2026-10-13 22:46Z) Read repository guidance; verify clean baseline and
  completed prerequisite 1.1.2.
- [x] (2026-10-13 22:48Z) Obtain two Wyvern reconnaissance reports, shared
      through
  context pack `pk_gadsijjx`; establish absent parser and corpus infrastructure.
- [x] (2026-10-13 22:50Z) Check primary format documentation using Firecrawl;
  resolve reference terminology and parser-level code-span whitespace rules.
- [x] (2026-10-13 22:55Z) Complete all six community-of-experts perspectives
  and reconcile source-witness, newline, schema, and red-stage findings.
- [x] (2026-10-13 22:57Z) Validate the documentation-only plan: formatting,
  type checking, linting, 103 tests, Markdown, and Mermaid all passed.
- [ ] Receive explicit plan approval.
- [ ] EP-M1: establish the corpus format and focused seed cases.
- [ ] EP-M2: complete every normative fixture and integrity assertion.
- [ ] EP-M3: reconcile documentation, validate, and mark 1.1.3 done.

## Surprises & discoveries


- `syrupy_mdast/_extension.py::MarkdownAstSnapshotExtension.serialize` only
  validates input and raises `NotImplementedError` for task 2.3.1.
  `pyproject.toml` contains Syrupy, but no Wenmode runtime dependency. There is
  no callable parser or canonicalizer for an honest integration assertion yet.
- The current suite has pytest and Hypothesis but no pytest-bdd feature files
  or dependency and no Markdown snapshots. Corpus testing must not pretend an
  existing serialization pipeline is available.
- ADR-004 adds exact-shape adjacent plain-text merging before line-ending
  normalization. Design §8's older four-rule list needs reconciliation. Its
  older parser spelling `Parser(github, ...)` also differs from the accepted
  `Parser(github(), positions=False)` construction; use the ADR.
- `docs/repository-layout.md`, referenced by repository guidance, does not
  exist at this baseline. Use `docs/contents.md` and the paths below; do not
  expand this task into a repository-documentation rewrite.
- Firecrawl's initial structured extraction of the GFM specification omitted
  reference details and misstated code-span whitespace. Reading the full
  primary text resolved this: line endings become spaces in code spans, and
  paired edge spaces can be stripped by parsing. Preservation fixtures must
  compare different **parsed values**, not assume all source whitespace
  survives parsing.

## Decision log


- **D1 — specification before implementation.** Proposed 2026-10-13. Author
  source and expected-output fixtures now, with integrity checks. Defer actual
  parser and canonicalizer consumption to tasks 1.2.3 and 2.1.1–2.1.2. This
  preserves roadmap dependencies and prevents a test-only implementation from
  becoming its own oracle.
- **D2 — byte-preserving source files.** Proposed 2026-10-13. Store Markdown as
  `.txt`, canonical payloads as `.json`, and case metadata as TOML. These are
  standard-library-readable formats; no new schema library is needed. The
  developer guide will document that `.txt` contains Markdown deliberately.
- **D3 — finite verification.** Proposed 2026-10-13. Use named pytest examples
  and parametrization for the normative corpus. No normalization algorithm or
  all-input theorem is introduced here. Generated invariants, substantive
  formal proofs, and live snapshot lifecycle tests remain with the executable
  features that can discharge them. A Rust proof extension would contradict the
  accepted Python-only boundary and would prove no corpus property that needs
  it.
- **D4 — authoritative reconciliation.** Proposed 2026-10-13. Update design §8
  to reflect ADR-004, including merge order and preservation exceptions, and
  correct the nearby parser construction example during EP-M3. Record the
  corpus format and reuse policy there and in the developer guide. No new ADR
  is required for a test-data organization choice that changes no contract. Any
  actual semantic departure requires a separate accepted decision.

## Outcomes & retrospective


The plan and six-perspective review are complete, and the requested baseline
gates passed. No implementation, corpus verification, or runtime behaviour has
been delivered. Explicit approval and all implementation milestones remain
outstanding. The draft PR metadata records publication separately.

At completion, record fixture counts by obligation, named negative-control
results, command logs, final commit, and the documentation reconciliation.
Explain that passing corpus integrity tests are not parser-conformance proof.
Do not set this plan to `COMPLETE` while a normative fixture, acceptance gate,
or upstream-document reconciliation remains outstanding.

## Context and orientation


An abstract syntax tree (AST) represents parsed document structure as nested
mappings and arrays. A canonical tree removes only the differences approved in
ADR-004. A golden payload is a checked-in expected JSON result authored and
reviewed independently of the future implementation. An equivalence group
contains distinct sources with one expected payload; a distinction pair has two
sources and different expected payloads.

Read these repository documents before implementation:

- [Documentation index](../contents.md), [roadmap](../roadmap.md), and
  [technical design](../syrupy-mdast-design.md), especially §§2–4, 7–8, 11, 13.
- [ADR-003](../adr-003-snapshot-version-policy.md) and
  [ADR-004](../adr-004-parser-profile-and-normalization.md), including the
  contract manifest, normative fixtures, and raw-parser probe limitations.
- [Developer guide](../developers-guide.md), [user guide](../users-guide.md),
  [documentation style](../documentation-style-guide.md), and
  [complexity guidance](../complexity-antipatterns-and-refactoring-strategies.md).
- `.rules/python-00.md`, `.rules/python-typing.md`,
  `.rules/python-exception-design-raising-handling-and-logging.md`, and the
  remaining `.rules/python-*.md` relevant to edited code. Read
  `docs/scripting-standards.md` before adding any script; no script is planned.

Load `$execplans`, `$codegraph-mcp`, and `$python-router`; route the finite
test work to `python-testing`. Use CodeGraph for structural questions, and
`$firecrawl-mcp` for remote documentation gaps. Consult `hypothesis` or
`python-verification` only if a discovery introduces an actual open-domain
invariant; revise this plan before expanding verification scope. Use the
`commit-message` and `pr-creation` skills for publication. Teams exchange
source references through `context_pack`; `scrutineer` alone runs full gates.

Existing package contract tests include `tests/test_public_api_contract.py`,
`tests/test_core_import_boundary.py`, and
`tests/test_package_manifest_contract.py`. Keep them passing without relaxing
the `NotImplementedError` expectation. Existing test support is in
`tests/support/`; no equivalent corpus loader exists at the baseline.

## Conformance basis


The immutable repository baseline is
`c19afee8ed735dffa6262cf0b2e0a9ca0a5a0551`. All document revisions below mean
those files at that commit. There is no separate Terms of Reference document.
The technical design is a proposed living design, subordinate to accepted
ADR-003 and ADR-004 (accepted 2026-10-11). The roadmap records 1.1.2 complete.

Use these selective trace identifiers:

- **R-CORPUS:** roadmap 1.1.3's equivalences, distinctions, ordinary-reference
  forms, and complete design §8 coverage → EP-M1/EP-M2 → A-COVERAGE/A-CASES.
- **R-NORMALIZE:** design §8 as amended by ADR-004's five ordered rules →
  EP-M2 → A-SYNTHETIC and A-GOLDEN.
- **R-PRESERVE:** design §8's preserved values, order, omissions, footnotes,
  and HTML plus NF-1–NF-13 → EP-M2 → A-CASES/A-SYNTHETIC.
- **R-BOUNDARY:** design §§2–5 and roadmap dependency order → every milestone
  → unchanged production API/dependency contracts and explicit deferred tests.
- **R-MAINTAIN:** repository documentation and completion requirements → EP-M3
  → A-DOCS and the gated roadmap checkbox.

### Normative fixture matrix


Each row below is a family, not permission to combine independent distinctions
into one opaque fixture. Assign stable case IDs within each family and put
those IDs beside their assertions. Expected results must be fully specified
canonical root trees, not just equality labels. For synthetic data, retain
root-shaped inputs and place unusual values in unknown fields or `data`.

| Family / authority                 | Required focused sources or synthetic inputs                                                                                                                             | Observable expected evidence                                                                                                                  |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Emphasis / NF-1                    | `*a*` versus `_a_`; `**b**` versus `__b__`                                                                                                                               | Separate emphasis and strong equivalence groups                                                                                               |
| Ordinary links / NF-2              | Direct, full `[x][r]`, collapsed `[x][]`, shortcut `[x]`; definitions before and after use; label case changes                                                           | Same children, destination, and title yield one payload; source forms and definitions disappear                                               |
| Link distinctions / NF-2           | Change destination, title, or child text individually; absent versus present title; unresolved full, collapsed, shortcut forms; unused definitions                       | Changed resolved fields remain distinct; unresolved text stays literal; unused definitions leave no trace                                     |
| Reference images / NF-2            | Direct, full, collapsed, shortcut images, forward definition, unresolved and unused image labels                                                                         | Resolved `image` has expected `url`, `alt`, optional `title`; unresolved syntax stays literal                                                 |
| Footnotes / NF-3                   | Case-folded `[^F]` and `[^f]`; forward definition; definition before/after text; unused definition; repeated reference; undefined reference; changed identifier and body | Folded labels agree; definitions remain in source order, unused definitions remain, repeated references repeat, unresolved text stays literal |
| Omitted fields / NF-4              | Untitled link/image; code without language or metadata; non-task list item; unordered list                                                                               | No synthetic `title`, `lang`, `meta`, `checked`, or `start` null members                                                                      |
| Tables / NF-5, NF-10               | Unaligned, left, centre, right columns; change one cell or one alignment                                                                                                 | Preserve `null` array elements; cell content and alignment distinguish payloads                                                               |
| Raw HTML / NF-6, NF-7, NF-10       | Change raw spelling; allowed HTML; filtered tags such as `<title>` and `<iframe>`; separate type-1 `<script>`, `<style>`, `<textarea>` blocks                            | Preserve exact parsed `value` and non-empty `data.escaped`; pin 0.15.2's accepted type-1 divergence without claiming sanitization             |
| Line endings / NF-8                | Literal LF, CRLF, CR sources for paragraphs, hard breaks, fenced code, multiline titles                                                                                  | Three encodings per context; one canonical expected payload; input bytes independently checked                                                |
| Positions / NF-9                   | Synthetic nested `position` members in root, children, arrays, and non-empty `data`                                                                                      | Authored output has all position members removed without losing sibling data                                                                  |
| Breaks / NF-10                     | Soft newline versus two-space hard break; backslash hard-break spelling                                                                                                  | Hard and soft remain distinct; equivalent hard-break forms have expected `break` nodes                                                        |
| Code / NF-10                       | Fenced and inline code values with meaningful whitespace changes; change fenced `lang` and `meta` independently                                                          | Preserve parsed spaces and tabs and code values; parser-level code-span trimming is not a canonicalizer rule                                  |
| Lists / NF-10                      | Ordered/unordered, start number, tight/loose `spread`, checked/unchecked/plain items, swapped item order                                                                 | Isolate each scalar or ordering distinction; retain explicit `false`                                                                          |
| Plain text / NF-11                 | `a & b` versus `a &amp; b`; `a*b` versus `a\*b`; synthetic adjacent runs, metadata-bearing text, intervening non-text node                                               | Merge only exact `type`/`value` text siblings; do not cross metadata or non-text boundaries                                                   |
| Key order / NF-12                  | Scrambled known keys plus unknown keys including U+E000 and U+10000; nested metadata; a string key containing CR                                                         | Preferred keys then Unicode code points, not UTF-16 units; never normalize member names                                                       |
| Node coverage / NF-12              | One supplementary all-node document plus focused GFM strikethrough, task, table, extended autolink, footnote, heading, quote, image, thematic-break cases                | Explicitly cover the 22 node types listed below and direct node-member names                                                                  |
| Numeric references / NF-13         | `&#0;`, `&#xD800;`, `&#x110000;`, ordinary non-ASCII text                                                                                                                | U+FFFD for zero; invalid scalar references literal; strict UTF-8 payloads                                                                     |
| Recursive preservation / design §8 | Nested false, zero, empty string, empty array, null array item, non-empty `data`, unknown field; empty `data` versus `data: []`, `data: null`, `data: false`             | Delete only empty mapping `data`; retain all other named values and array order                                                               |
| Rule interaction / ADR-004 order   | Adjacent text values ending CR and starting LF; position removal exposing exact-shape text; empty-data removal exposing exact-shape text                                 | Removal then merging then newline normalization; CR plus LF across merged siblings becomes one LF                                             |
| Writer shape / design §8, ADR-004  | Small golden root with Unicode, quotes, backslash, control escapes, ordered keys                                                                                         | Two spaces, unescaped Unicode, strict UTF-8, no BOM, exactly one trailing LF; no version marker                                               |

_Table 1: Required corpus families and their expected contracts._

The explicit node-type set is `blockquote`, `break`, `code`, `delete`,
`emphasis`, `footnoteDefinition`, `footnoteReference`, `heading`, `html`,
`image`, `inlineCode`, `link`, `list`, `listItem`, `paragraph`, `root`,
`strong`, `table`, `tableCell`, `tableRow`, `text`, and `thematicBreak`. Keep
targeted assertions for each semantic distinction even when the all-node
fixture contains the same type.

## Interfaces and dependencies


Create `tests/fixtures/markdown_contract/README.md` and `manifest.toml`, with
`sources/`, `synthetic/`, and `expected/` subdirectories. Source `.txt` files
are raw UTF-8 Markdown. Synthetic `.json` files contain input root trees;
expected `.json` files contain authored canonical payloads. Use descriptive
filenames such as `emphasis-asterisk.txt` and `emphasis.json`. The README maps
case IDs to design rules and explains visible notation for invisible bytes.

The accepted `rules` vocabulary is `NF-1` through `NF-13`, plus
`remove-position`, `remove-empty-data`, `merge-plain-text`,
`normalize-line-endings`, `order-members`, `preserve-values`, and
`writer-format`. The five operation names mean the ordered ADR-004 rules;
`preserve-values` means design §8's falsy, unknown-field, and array-order
contract; `writer-format` means ADR-004's JSON writer settings. Store this
small vocabulary in the test support module and document it in the README.
Tests still require explicit case-to-rule assignments rather than accepting any
case that merely carries a required tag.

The TOML manifest has `corpus_version = 1`, `contract_version = 1`,
`wenmode_evidence_version = "0.15.2"`, and `[[cases]]` records. Each record has
`id`, `rules` (non-empty rule-ID array), `reason`, `kind` (`markdown` or
`synthetic`), `input`, and `expected` (relative paths). Markdown records also
have `line_endings` (`lf`, `crlf`, `cr`, or `none`). For mixed-newline
examples, use a synthetic JSON string rather than adding an ambiguous source
category.

Separate `[[relations]]` records contain `id`, `relation` (`equal` or
`distinct`), and `cases` (at least two existing case IDs). Equal groups share
one expected file; distinct groups require pairwise distinct expected bytes. Do
not duplicate a golden file merely to assert equality. Multiple records can
reuse a source when testing independent relationships.

For example, a seed manifest contains these complete records:

```toml
corpus_version = 1
contract_version = 1
wenmode_evidence_version = "0.15.2"

[[cases]]
id = "emphasis-asterisk"
rules = ["NF-1"]
reason = "Asterisk emphasis has the same structure as underscore emphasis."
kind = "markdown"
input = "sources/emphasis-asterisk.txt"
expected = "expected/emphasis.json"
line_endings = "lf"

[[cases]]
id = "emphasis-underscore"
rules = ["NF-1"]
reason = "Underscore emphasis removes delimiter spelling as a distinction."
kind = "markdown"
input = "sources/emphasis-underscore.txt"
expected = "expected/emphasis.json"
line_endings = "lf"

[[relations]]
id = "emphasis-delimiters"
relation = "equal"
cases = ["emphasis-asterisk", "emphasis-underscore"]
```

The source bytes are respectively `b"*a*\n"` and `b"_a_\n"`. Their shared
`expected/emphasis.json` contains the following, with exactly one final LF:

```json
{
  "type": "root",
  "children": [
    {
      "type": "paragraph",
      "children": [
        {
          "type": "emphasis",
          "children": [
            {
              "type": "text",
              "value": "a"
            }
          ]
        }
      ]
    }
  ]
}
```

Add one test-only support module, `tests/support/markdown_contract.py`, with
small typed records and these functions:

```python
def load_corpus(root: Path) -> ContractCorpus: ...
def read_source(path: Path) -> str: ...
```

`ContractCorpus` holds ordered tuples of case and relation records. Keep this
interface internal to tests. It loads metadata and paths; it never parses
Markdown, normalizes trees, or computes canonical expectations. Resolve paths
relative to the supplied corpus directory. Reject absolute paths, parent
escapes, missing files, duplicate IDs, unknown kinds or relations, unknown rule
IDs, and dangling relations with `ValueError` messages naming the case or
relation. Catch only specific decoding or format exceptions when adding
context. Do not add an error hierarchy or compatibility wrappers.

`read_source` uses `Path.read_bytes().decode("utf-8")`; no `read_text()`
universal-newline conversion. Use a local recursive JSON type for decoded
fixture values only where needed; reject floats and invalid scalar strings when
checking expected goldens. Expected checks are assertions on the corpus, not
production AST validation. Never coerce booleans to integers.

Add `.gitattributes` entries with `-text` for corpus source `.txt`, synthetic
`.json`, and expected `.json` paths to prevent checkout newline conversion. If
`.gitattributes` already exists at implementation time, append narrow patterns.
Do not disable formatting for the rest of the repository.

No new dependency is planned. `tomllib`, `json`, `pathlib`, pytest, and
existing Syrupy availability suffice. Do not use the unimplemented custom
extension.

## Verification plan


There is no new normalization algorithm, contractual business algorithm, or
universal lemma in this task. The deliverable is a finite specification with
small test-data loading behaviour. Exhaustively enumerate its required families
and malformed metadata partitions. This does not prove parser correctness over
arbitrary Markdown or canonicalizer properties over arbitrary trees; those are
explicit future obligations, not assumed results.

**External assumptions:** Python's standard-library TOML/JSON decoding and
strict UTF-8 decoding follow their documented interfaces; pytest collects the
named tests; Git honours the narrow attributes. ADR-004's finite Wenmode probe
is historical evidence for 0.15.2, not a live integration result in this task.
Do not verify those third-party implementations or use a current upstream
release as an oracle for a different version.

- **A-COVERAGE — complete finite coverage.** In
  `tests/test_markdown_contract.py`, explicitly require every matrix subcase,
  all NF identifiers, the five transformations, and the 22 node types.
  Non-empty case counts alone are insufficient. Associate required case IDs
  with their expected rule and relation, so relabelling an unrelated case
  cannot fill a gap. Delete one required case in a temporary copied corpus:
  `test_missing_required_case_is_rejected` must fail the integrity check for
  that ID. Discharge when the committed corpus covers every listed obligation.
- **A-CASES — meaningful relations and expected fields.** Parameterize by
  stable case IDs and assert the specific node, value, omission, and order
  described in Table 1. Also assert the source witness for each case: literal
  delimiters, reference form, definition-before/after-use ordering, exact
  invisible bytes, and the changed field's source spelling as appropriate.
  These checks identify the named examples; they must not become a Markdown
  parser. Replacing a full-reference source with the direct source, or deleting
  an unused definition, must fail the witness assertion even though the shared
  golden remains unchanged. Read complete expected bytes for relation checks;
  dictionary equality cannot verify key order. Swapping two list children or
  replacing a distinct expected file with its partner in a temporary copy must
  be detected. Include unresolved references and non-task items as ordinary
  valid inputs, not parser exceptions. Discharge when every family has a
  focused semantic assertion and equal/distinct relations are non-empty.
- **A-SYNTHETIC — independent transformation examples.** Inspect before/after
  trees and assert named witnesses: removed positions, only empty-mapping
  `data` removed, preserved falsy values, member-name CR retained, text with
  metadata unmerged, and cross-sibling CRLF merged in the accepted order. Store
  outputs by hand. Do not execute a reference canonicalizer to produce them.
  Include a nested `data` mapping containing only `position`: after the
  recursive removals its expected parent has no `data`. If the implementor
  finds the ADR's recursive ordering ambiguous, stop and record the ambiguity
  rather than selecting a different ordering. A seeded retained position or lost
  `false` in a copied expected file must be rejected by its assertion. This
  discharges fixture intent only; future task 2.1.2 must run the real
  canonicalizer against these pairs.
- **A-GOLDEN — payload representation.** Read expected files as bytes; check
  strict UTF-8, no byte-order mark, the ADR's member order, one final LF, and
  formatting against the manifest's standard-library `json.dumps` expression.
  This is a format check on authored files, not an implementation of the
  production writer. Use an explicitly ordered key list from ADR-004, inspect
  decoded member order recursively, and reject duplicate JSON keys rather than
  accepting last-key-wins decoding. Mutate indentation, trailing newline, key
  order, and a duplicate member separately in temporary copies. Each must be
  rejected for the intended reason. Discharge when every expected file passes
  and the representative faults are caught.
- **A-LOAD — byte preservation and useful failures.** In
  `tests/test_markdown_contract_loading.py`, load named LF, CRLF, and CR source
  witnesses and compare `read_source(...).encode("utf-8")` with their original
  bytes. Independently compare every source's actual delimiters with its
  manifest classification: LF allows no CR; CRLF requires every CR and LF to
  belong to a CRLF pair; CR allows no LF; `none` allows neither. Each of the
  first three classes must contain at least one delimiter. Convert a copied
  CRLF source to LF without changing its metadata: the check must reject it.
  This catches already-corrupted fixtures as well as corrupting readers. Check
  malformed TOML, invalid UTF-8, duplicate case/relation IDs, dangling
  relations, invalid paths, empty groups, and missing files with
  `pytest.raises(ValueError, match=...)` where the loader translates errors. For
  `read_source`, retain `UnicodeDecodeError` rather than translating it
  unnecessarily. Substitute a newline-normalizing read in a local negative
  experiment; CRLF and CR assertions must fail. No generated property is needed
  for a direct standard-library delegation plus these finite policies.
- **A-DOCS — honest completion.** Design §8 and developer documentation link
  the corpus and describe its use; the user guide retains its explicit
  unimplemented-serialization limitation. The roadmap checkbox changes only
  after A-COVERAGE through A-LOAD and all commit gates pass.

The focused command for A-COVERAGE through A-LOAD is:

```bash
uv run pytest -v tests/test_markdown_contract.py tests/test_markdown_contract_loading.py
```

Run with clean Git-related environment variables as prescribed by `AGENTS.md`.
Expected evidence is named passing cases plus explicit negative-control
results; record actual counts rather than inventing a target count now.

### Behavioural, snapshot, property, and end-to-end scope


Pytest examples cover the contributor-facing corpus-loading behaviour. No
pytest-bdd dependency is introduced solely to restate those unit tests, and no
Syrupy snapshot of a golden file is added merely to duplicate the oracle. There
is no application behaviour, public API, persistent consumer format, or
installed-package integration change in 1.1.3. Therefore live BDD, multivariant
Syrupy output snapshots, and installed-wheel end-to-end tests are not
applicable to this bounded corpus milestone. Adding a new such boundary
triggers revision of this plan and the corresponding tests before
implementation.

Retain this concrete behavioural handoff for task 2.1.2; its future path is
`tests/features/markdown_contract.feature`, bound by
`tests/test_markdown_contract_behaviour.py` using pytest-bdd:

```gherkin
Feature: Canonical Markdown comparison follows the approved corpus
  Scenario: Ordinary reference notation is immaterial
    Given the direct and full-reference inputs from the approved corpus
    When the production pipeline canonicalizes both inputs
    Then both payloads equal the independently authored expected payload

  Scenario: Hard breaks remain structural
    Given the soft-break and hard-break inputs from the approved corpus
    When the production pipeline canonicalizes both inputs
    Then each payload equals its authored expected payload
    And the payloads differ

  Scenario: An unresolved ordinary reference remains literal
    Given the unresolved-reference input from the approved corpus
    When the production pipeline canonicalizes the input
    Then its text nodes equal the authored literal-text expectation
```

Do not add unbound feature files, skipped integration tests, or
expected-failure placeholders to make this task appear integrated. Later task
2.1.2 adds Hypothesis tests for idempotence, position invariance, and newline
invariance against the real canonicalizer; task 2.2.1 checks exact writer
bytes; tasks 2.3.1 and 2.4.1 add Syrupy lifecycle snapshots and installed-wheel
assertions. Those tests must fail against broken implementations, not only
broken data.

## Plan of work and milestones


### EP-M1 — establish a usable corpus format


Assigned requirements: R-CORPUS, R-BOUNDARY; acceptance A-LOAD and seed
portions of A-CASES/A-GOLDEN. Re-read the approved plan, prerequisite, and
current repository state. Add the loader tests first, showing that a missing
manifest, invalid relation, and newline-corrupting read are detected. Red
failures must exercise the intended missing behaviour, not an accidental import
error. For an initially absent loader, add a typed stub, call it from the
tests, and record its deliberate `NotImplementedError` as the red result.
Data-coverage red tests must instead fail on the intended missing case or
field; do not commit it until the green implementation is complete.

Add the small loader, fixture README, manifest, attributes, emphasis equality,
and hard/soft distinction seed cases. Author expected roots independently. Keep
the complete required-case inventory test for EP-M2 so this plateau can pass
honestly without ignoring known incomplete coverage. Refactor only after
focused tests are green; then run every applicable gate and commit the plateau.

End state: a functioning, tested corpus format with useful seed data, not a
claim that 1.1.3 is finished. Check that no production code or dependency
changed, the tests never invoke a canonicalizer, and all seed trace links are
valid. Recovery: correct only the failed step, rerun affected evidence and then
gates; revert only this owned commit if necessary. Remaining gap: complete
matrix coverage. No compatibility machinery is needed for this test-only API.

### EP-M2 — complete the normative matrix


Assigned requirements: R-CORPUS, R-NORMALIZE, R-PRESERVE, R-BOUNDARY;
acceptance A-COVERAGE/A-CASES/A-SYNTHETIC/A-GOLDEN. Add the full explicit
inventory and semantic assertions, run them against the seed corpus, and
capture the red missing-case/field failures. Add focused source files,
synthetic inputs, expected payloads, and relations until every required subcase
passes.

Review each golden beside its Markdown or synthetic input and its ADR clause.
Check source reference placement explicitly: a forward reference has its
**definition after use**; include the before-use case separately. Keep child
text unchanged when testing case-insensitive labels. Pin footnote labels and
identifiers according to Wenmode's case folding, not the design's older broad
wording about identifier distinctions.

Run named negative controls on copies, never the committed fixtures in place.
Do not auto-approve output from a parser or update command. If an unfamiliar
raw AST shape needs empirical confirmation, reuse ADR-004's isolated 0.15.2
probe instructions and record the exact version and observation. This is an
authoring investigation, not a new required runtime or CI dependency. Never
claim it verifies canonicalization, which that probe does not execute.

End state: all matrix subcases present, independently reviewed, and passing
integrity checks; full gates pass and this plateau is committed. Conformance
check: every rule traces to a fixture and assertion; no new rule, API,
dependency, or persisted consumer format; historical and live evidence remain
separate. Recovery: restore erroneous authored data from the last good commit,
repair the precise case, rerun its negative control and full gates. Remaining
gap: documentation and roadmap closeout. No compatibility layer is needed.

### EP-M3 — document and close the corpus task


Assigned requirements: R-MAINTAIN and final conformance of all other
requirements; acceptance A-DOCS plus all prior evidence. Update design §8 to
name the accepted five-rule sequence and link the corpus; correct the nearby
parser example to the accepted `github()` call. Document test-only loader
scope, fixture editing, byte-preserving reads, golden review, and later
consumer seams in `docs/developers-guide.md`. Link the corpus README from
`docs/contents.md` and add a short user-guide pointer describing the normative
comparison examples while preserving the current serialization limitation.

Review ADR-004 for conflicts; record any substantive new decision in an ADR
referenced by the design before proceeding. Pure synchronization with the
already accepted ADR needs no new decision. Do not rewrite unrelated old
pinning language or generated scaffolding as part of this task.

After all evidence passes, mark only roadmap item 1.1.3 done. Update this
plan's outcomes, progress, trace links, and revision note. Run final gates with
the checkbox and documentation included and commit. Final conformance checks
confirm all matrix obligations, unchanged architecture, valid assumptions,
current trace links, and no unresolved deviation. Recovery: leave the roadmap
unchecked until the failed gate is repaired; never weaken a gate to close it.
The remaining parser and serializer gaps stay visibly assigned to their
existing roadmap tasks.

## Concrete steps and validation


Run commands from the repository root on
`1-1-3-canonical-markdown-contract-corpus`. First record `git status --short`,
`git branch --show-current`, and `git rev-parse HEAD`. Preserve unrelated work.
Follow `AGENTS.md`'s clean environment for Git-backed dependency fetches and
standard `/usr/bin/gh` identity checks. Never print credential values.

For each red/green iteration, use the focused pytest command above with
`set -o pipefail` and `tee` to a unique `/tmp` log. During EP-M1, run only the
file/tests that already exist; EP-M2 introduces the full inventory. Record the
actual failing assertion, then the same command's passing result. Negative
control tests must pass by demonstrating that the altered copy is rejected. No
permanent skip or xfail is an acceptance substitute.

Delegate full milestone gates to `scrutineer`, with one command at a time. For
each command, use a separate log, for example:

```bash
set -o pipefail
make check-fmt 2>&1 | tee /tmp/check-fmt-syrupy-mdast-1-1-3-EP-M1-attempt1.out
```

Run the following sequence before every implementation commit:

```bash
make fmt
make check-fmt
make typecheck
make lint
make test
make audit
make markdownlint
make nixie
```

Wrap **each** command with the same `pipefail`/`tee` pattern and its own action
name, milestone, and attempt number; never overwrite previous evidence. Record
log paths together with the candidate SHA and the working-tree diff being
validated. `make fmt` can modify other tracked Markdown: inspect `git diff` and
retain only task-owned changes, preserving any pre-existing edits. If tooling
removes the ExecPlan's required heading spacing, restore two blank lines after
headings and use a file-local, explained MD012 allowance for this plan only. Do
not modify repository-wide lint policy to accommodate a plan.

Expected result: zero exit status from every command; tests report the actual
passing count; no formatting, typing, or lint errors; no unreviewed fixture
changes. `make test` requires `makeutil` on `PATH`; use the developer guide's
installation instructions if missing. `WITH_ACT=1` is unnecessary without
workflow changes. Treat disk exhaustion or build-admission refusal according to
`AGENTS.md`, with logs and no unauthorized workaround.

For the documentation-only planning commit, run `make fmt`, `make check-fmt`,
`make markdownlint`, and `make nixie`; also record the requested type, lint,
and test gate results when preparing this plan for review. These results are
baseline evidence, not execution of EP-M1 or approval of implementation.

## Idempotence and recovery


Loading and checking the corpus must not modify it. Temporary negative-control
copies belong under pytest's `tmp_path`; logs belong in `/tmp`, never build
artifacts. Re-running gates should produce the same fixture bytes. Use stable
IDs for readable pytest reports; do not depend on filesystem enumeration order.

Commit each coherent milestone only after its gates pass. A later repair
invalidates affected candidate evidence: rerun the relevant gates before the
next commit. Avoid broad resets or restoring other agents' work. Roll back an
owned published milestone with a targeted revert, preserving later unrelated
commits; do not rewrite shared history without authority.

## Artefacts and notes


Primary-source research on 2026-10-13 used Firecrawl to read
[Wenmode compatibility](https://wenmode.lepture.com/compatibility/) and the
[GFM specification](https://github.github.com/gfm/). Wenmode documents its beta
status and GitHub preset; live documentation does not supersede ADR-004's
recorded 0.15.2 outcomes. GFM's
[reference links](https://github.github.com/gfm/#reference-link) and
[code spans](https://github.github.com/gfm/#code-spans) explain source syntax
and code-span whitespace. GFM 0.29 does not define the footnote contract;
ADR-004 remains authoritative. No third-party conformance corpus is copied.

The two Wyvern reports are research evidence, not formal approval. Community
review used all six Logisphere perspectives in three agent pairs. Pandalump and
Wafflecat confirmed the scope and requested an explicit rule vocabulary and
worked example. Telefono and Dinolump requested source-witness checks so shared
goldens cannot conceal a corrupted input. Those revisions are included;
Doggylump required newline declarations to be checked against actual bytes, and
Buzzy Bee required unique logs per milestone and attempt. Both are included.
The key trade-off is retaining independent static expectations while honestly
deferring runtime conformance. No reviewer requested a runtime implementation.
Planning validation on 2026-10-13: `make fmt`, `make check-fmt`,
`make typecheck`, `make lint`, `make test` (103 passed), `make markdownlint`,
and `make nixie` all passed sequentially. The candidate was baseline `c19afee8`
plus this new document; no production or test files changed. The final
evidence-only document update receives a further documentation check before
commit. These baseline passes do not discharge the future A-COVERAGE through
A-DOCS implementation obligations.

The formatting log is `/tmp/fmt-syrupy-mdast-113-planning-attempt1.out`. Other
initial logs use `/tmp/<gate>-<suffix>.out`, where `<gate>` is `check-fmt`,
`typecheck`, `lint`, `test`, `markdownlint`, or `nixie`, and the exact suffix
is:

```plaintext
20a71b31-681e-4958-9441-c58e2162a9c2-1-1-3-canonical-markdown-contract-corpus-planning
```

Final documentation checks use
`/tmp/<gate>-syrupy-mdast-113-planning-final-attempt2.out`. The first
evidence-update check required paragraph rewrapping; `make fmt` repairs that
formatting before the final rerun. The draft PR records publication and final
gate results without claiming plan approval. Implementation remains prohibited
until explicit approval.

Revision note (2026-10-13): initial plan separates authored corpus evidence
from future runtime conformance, includes synthetic witnesses for rules that
Markdown cannot expose, and retains an explicit implementation approval gate.

Revision note (2026-10-13): expert review added an explicit rule registry, a
worked fixture example, source and newline corruption controls, the recursive
position/empty-data interaction, and precise red-stage and evidence retention
instructions. The implementation scope and approval gate are unchanged.

Revision note (2026-10-13): record successful baseline validation and expert
review completion. Publication is recorded in the draft PR metadata, approval
remains outstanding, and all implementation milestones remain unstarted.
