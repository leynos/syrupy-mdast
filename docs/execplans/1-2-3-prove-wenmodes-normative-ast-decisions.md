# Prove Wenmode's normative AST decisions (1.2.3)

This ExecPlan (execution plan) is a living document. The sections `Constraints`,
`Tolerances`, `Risks`, `Progress`, `Surprises & discoveries`, `Decision log`,
`Outcomes & retrospective`, `Conformance basis`, and `Verification plan` must
be kept up to date as work proceeds.

Status: DRAFT (expert-panel review applied; awaiting user approval).
Implementation must not begin until the user explicitly approves this plan,
including the ADR-004 amendment text in `Decision log` D2.

Branch: `1-2-3-prove-wenmodes-normative-ast-decisions`

Roadmap item: `1.2.3` in `docs/roadmap.md`.

## Purpose / big picture

`syrupy-mdast` will store Markdown snapshots as canonical JSON derived from the
abstract syntax tree (AST) that the Python parser Wenmode produces. An AST is
the nested tree of mappings that describes a parsed document; Wenmode's trees
follow mdast, the Markdown AST format used by the unified ecosystem. Because
Wenmode's output *is* the snapshot format, four parser behaviours were ratified
as contract decisions in
[ADR-004](../adrs/adr-0004-parser-profile-and-normalization.md) before any
parsing feature was built:

1. Ordinary reference links and images are resolved: `[x][r]` with `[r]: /u`
   becomes a plain `link` node, and no `definition`, `linkReference`, or
   `imageReference` node remains (NF-2).
2. Footnotes stay structural: `footnoteReference` and `footnoteDefinition`
   nodes keep `identifier`, `label`, children, and document order (NF-3).
3. Nullable members are omitted, not set to `null`: a link without a title has
   no `title` member, and a bullet list has no `start` member. The only `null`
   values are unaligned table columns inside `align` (NF-4 and NF-5).
4. Raw HTML stays an `html` node. Wenmode escapes GitHub's disallowed tags and
   marks the node with `data: {"escaped": true}`. CommonMark type-1 HTML blocks
   (`<script>`, `<style>`, `<textarea>`, and `<pre>` at block start) are not
   filtered in Wenmode 0.15.2, and that divergence is ratified as observed
   (NF-6 and NF-7).

Today nothing in the repository runs the parser against these decisions. The
ADR's self-checking probe exists only as text in the ADR. The
[canonical Markdown contract corpus](../../tests/fixtures/markdown_contract/README.md)
is validated for integrity only; its README says it "does not run Wenmode". A
Wenmode upgrade that quietly changed one of the four decisions, for example by
keeping `definition` nodes or by synthesizing `"title": null`, would pass every
current test.

After this change, `make test` does three things. It runs the 48 corpus cases
tagged NF-2 to NF-7 through the internal seam
`syrupy_mdast._wenmode.parse_markdown` and compares each result strictly with
its reviewed golden. It runs a small catalogue of hand-authored probes for the
ratified behaviours the corpus does not cover. And it checks generated and
exhaustively enumerated documents against the decisions' universal rules. If a
parser upgrade changes a ratified decision, the suite fails and attributes the
failure to the violated clause, or reports unclassified drift:

```plaintext
FAILED tests/test_wenmode_normative_decisions.py::test_corpus_case_matches_raw_parse[link-title-absent]
AssertionError: corpus case 'link-title-absent' violates NF-4.omitted:
root.children[0].children[0].title is null
```

This closes roadmap item 1.2.3. It also gives roadmap 2.1.1 (GitHub-profile
parsing) and 3.2.1 (the Wenmode upgrade report) an executable oracle for the
four decisions. No public API or user-visible behaviour changes.

## Constraints

- Implement only roadmap 1.2.3, and only after the user explicitly approves
  this plan. Approval of this plan includes acceptance of the ADR-004 amendment
  text in `Decision log` D2. If the user approves the plan but not that text,
  the plan is `BLOCKED` until the amendment is agreed.
- Do not modify production code under `syrupy_mdast/`. The seam
  `syrupy_mdast/_wenmode.py` stays exactly as delivered by 1.2.2. If a probe
  appears to need a production change, stop and escalate.
- Keep the exact pin `wenmode==0.15.2` (`pyproject.toml` line 15, ADR-005). Do
  not add runtime or development dependencies. `pytest`, `pytest-bdd`,
  `pytest-xdist`, `pytest-timeout`, and `hypothesis>=6,<7` are already in the
  `dev` dependency group.
- Expected trees are hand-authored, reviewed data. Tests must never
  regenerate, rewrite, or "accept" them from parser output. Do not edit corpus
  goldens under `tests/fixtures/markdown_contract/expected/`. The only
  permitted corpus edit is the D2 correction of two `reason` strings in
  `manifest.toml`.
- Do not implement canonicalization, shape validation, the JSON writer, input
  limits, or error translation. Those belong to roadmap 2.1.1, 2.1.2, 2.2.1,
  and later. Tests compare raw `to_ast()` output with order-insensitive strict
  JSON equality and must not contain a partial canonicalizer.
- Keep every Python file at or below 400 lines (`max-module-lines = 400`;
  `AGENTS.md`). `tests/test_markdown_contract_loading.py` (400 lines),
  `tests/test_markdown_contract.py` (398), and
  `tests/support/markdown_contract_loading.py` (398) must not grow.
- Lint obligations: keep Ruff `max-complexity = 8`. Keep 100% `interrogate`
  docstring coverage, which includes nested test doubles and their methods.
  Pylint's `too-many-arguments` and `too-many-positional-arguments` limits (4)
  apply under `tests/`, so bundle parameters into case dataclasses. The
  df12-python-lints pass requires a message on every `assert`, including in BDD
  steps. Ruff's `PLR6301` applies in `tests/support/`. Use en-GB-oxendict
  spelling in comments and documentation.
- Place all tests under the top-level `tests/` tree. Do not register new
  pytest markers, and do not use the expensive session `wheelhouse` fixture.
- Historical documents stay untouched: completed ExecPlans, ADR-003, ADR-005,
  and ADR-004's existing decision body and 2026-10-30 addendum. ADR-004 may
  change in exactly three places: the new `## Amendment (2026-11-16)` section,
  inserted before the `[maintainer-acceptance]:` link definition; a one-line
  pointer added to its `## Status` section; and its `## Date` line (see D2).
- Observe Wenmode only through `parse_markdown` and Wenmode's public modules
  (`wenmode`, `wenmode.presets`). Never import private Wenmode modules.
- Run gates sequentially, logging to `/tmp/<action>-syrupy-mdast-<branch>.out`.
  `/tmp` holds logs and scratch text only, never a build target or virtual
  environment. Do not commit a failing candidate.

## Tolerances (exception triggers)

The comparison base is the merge base with `origin/main` (currently `16f99f4`).
Count only committed changes (`$base..HEAD`) so new files are included.
ExecPlan files under `docs/execplans/` are excluded from every count. Each
counted file belongs to exactly one category, by this whole-file rule:

```bash
base=$(git merge-base HEAD origin/main)
git diff --numstat "$base" HEAD -- . ':(exclude)docs/execplans/**' | awk '
  { net = $1 - $2; f = $3; files += 1 }
  f ~ /\.md$/                         { docs += net; next }
  f ~ /^tests\/fixtures\//            { data += net; next }
  f ~ /^tests\/.*\.(py|feature)$/     { code += net; next }
                                      { config += net }
  END { printf "files=%d code=%d data=%d config=%d docs=%d\n", files, code, data, config, docs }'
```

- Code (Python and Gherkin under `tests/`): at most 2,800 net lines (additions
  minus deletions).
- Fixture data (non-Markdown files under `tests/fixtures/`): at most 900 net
  lines. These files are test artefacts, but pretty-printed JSON inflates line
  counts, so they have their own limit that does not share capacity with code.
- Configuration (everything else that is not Markdown): at most 20 net lines.
  The expected value is zero.
- Documentation (Markdown outside `docs/execplans/`): at most 500 net lines.
- Files: at most 28 changed non-ExecPlan files.

Each category is enforced independently; spare capacity in one never offsets
another.

Budget evidence (re-priced after review):

- The planned modules are the strict-JSON module (about 120 lines), the
  shared field readers (about 10 net, since they move), the catalogue model and
  loader (about 320), the clause classifiers (about 230), strategies (about
  230), and the controls table (about 130). Tests come to about 1,500: the
  strict-JSON tests (about 160), catalogue integrity (about 300), conformance
  (about 260), the HTML grid (about 200), properties (about 330), BDD steps
  (about 230), and the feature file (about 80). The total is about 2,550 lines.
- Comparable modules: `tests/support/markdown_contract_loading.py` is 398
  lines and `tests/test_markdown_contract_loading.py` is 400, so loader
  estimates are priced at that scale. Fixture data is about 16 probes at about
  30 lines each (corpus goldens average 26 lines) plus a registry of about 22
  clauses at about 9 lines each: about 680 lines. Documentation is about 70
  lines for the ADR amendment, 40 for the design document, 110 for the
  developers' guide, 70 for the two fixture READMEs, and 15 for roadmap and
  contents: about 305 lines.
- Historical comparison: 1.2.2 started at 16 files and 900 net lines and
  overran by about 75% to 1,596 lines, because its verification suite was
  under-counted. It was raised to 24 files and 2,400 lines, and finished at 21
  files and 1,755. 1.1.3 overran its 600-line cap by about 35% (813 lines), and
  the maintainer waived the cap without a replacement. 1.2.1 had no numeric
  budget. Both overruns were missed verification scope, so these limits price
  every verification artefact and keep about 10% (code), 30% (data), and 60%
  (documentation) contingency. Under-run is expected if the attribution and
  control code consolidates well.

Other triggers:

- Interface: any change to `syrupy_mdast/` or `syrupy_mdast.__all__` stops
  work.
- Dependencies: any new dependency or changed pin stops work.
- Architecture: a need to canonicalize, to edit corpus goldens, or to amend
  ADR-004 beyond the D2 text stops work.
- Decision drift: if any probe or corpus case disagrees with the ADR-004 or
  D2 statement it pins under Wenmode 0.15.2, stop and record the evidence. Do
  not "fix" the expectation to match the parser.
- Control prediction: if a real-preset control (EP-M3) violates a different
  set of clauses than its recorded prediction, stop and record it before
  adjusting the prediction.
- Iterations: if the same gate failure survives three targeted fixes, stop and
  reassess rather than weakening an assertion.
- Time: if a single milestone exceeds one working day of active effort, record
  progress and reassess scope.
- Ambiguity: if a ratified clause admits two readings that give different
  expected trees, stop and present both.

## Risks

- Risk: an upgrade changes something unrelated to the ratified decisions (for
  example, a new member on paragraphs), so many strict tests fail and an
  upgrader is tempted to paste parser output into the fixtures. Severity: high.
  Likelihood: medium. Mitigation: failures are attributed by clause classifiers
  or reported as "unclassified drift" with the first differing path, so the
  3.2.1 report can separate decision changes from drift. The developers' guide
  rule (EP-M6) says that changing an existing `expected` value requires an
  ADR-004 amendment or a superseding ADR, cited in the commit.
- Risk: Hypothesis grammars generate Markdown that triggers unrelated syntax,
  such as merged lists, lazy continuation, setext headings, tables absorbing
  lines, or text merging around undefined footnotes. This would make properties
  fail for reasons outside the decisions. Severity: medium. Likelihood: medium.
  Mitigation: the grammar rules in EP-M4, which were derived from observed
  counterexamples during review. Any failing example is promoted to an
  `@example` before the grammar or model is fixed.
- Risk: label case folding varies across Python Unicode databases (ADR-004,
  "Interpreter Unicode data"). Severity: low. Likelihood: low. Mitigation: all
  generated and probe labels are ASCII.
- Risk: the user or maintainer rejects the D2 amendment text. Severity:
  medium. Likelihood: low. Mitigation: EP-M1 commits only the amendment, so the
  plan blocks before any fixture exists.
- Risk: a malformed catalogue raises during collection, and under
  pytest-xdist that aborts the whole `make test` session. Severity: medium.
  Likelihood: low. Mitigation: catalogue-driven parametrization catches loader
  errors and yields a single failing parameter that carries the located error
  (EP-M3).
- Risk: corpus growth in 2.1.1 changes the selected subset. Severity: low.
  Likelihood: high. Mitigation: assert a minimum count and that every clause's
  named corpus cases are selected, not an exact count. Selection also has a
  structural guard (`L-SELECT`), so a case that needs canonicalization is
  rejected with a message telling its author to tag it.
- Risk: the Wenmode public preset API used by the real-preset controls
  (`presets.streaming`, `presets.commonmark`, `create_preset`) changes on
  upgrade. Severity: low. Likelihood: medium. Mitigation: the controls are
  pinned to 0.15.2 like everything else. On upgrade, they fail with a clear
  message, and the 3.2.1 report re-derives them.
- Risk: CodeScene code-health findings on test-support modules, as happened in
  1.1.3 (loader complexity 4.38 against a threshold of 4) and 1.2.1
  (duplication). Severity: medium. Likelihood: medium. Mitigation: move the
  shared field readers instead of copying them, split `first_difference` by
  kind, keep functions small, and run `cs delta` at each milestone.

## Progress

- [x] (2026-11-16 10:40Z) Branch renamed to
  `1-2-3-prove-wenmodes-normative-ast-decisions`; Lody session titled.
- [x] (2026-11-16 11:30Z) Reconnaissance by a Wyvern team: ADR decisions,
  seam and test infrastructure, historical ExecPlan budgets, and gates.
- [x] (2026-11-16 11:45Z) Raw Wenmode 0.15.2 probing, corpus subset analysis,
  and an upgrade drill against 0.15.3 and 1.0.0rc1 (see Surprises).
- [x] (2026-11-16 12:30Z) Initial draft committed (`f5364ba`).
- [x] (2026-11-16 13:50Z) Expert-panel design review (verification rigour,
  contracts and ADR governance, and maintainability with pre-mortem and
  alternatives). All three returned "proceed with changes". Their findings were
  verified against the parser and applied in this revision (D12 to D18).
- [ ] Plan approved by the user.
- [ ] `EP-M1` ADR-004 amendment, design wording, and corpus `reason`
  correction.
- [ ] `EP-M2` shared readers refactor, strict JSON comparison, and catalogue
  model with the corpus-backed registry.
- [ ] `EP-M3` clause classifiers, probes, parser conformance, and controls.
- [ ] `EP-M4` generated and exhaustive invariants.
- [ ] `EP-M5` behavioural contract scenarios.
- [ ] `EP-M6` upgrade drill, documentation, and roadmap closure.

## Surprises & discoveries

- Observation: ADR-004 NF-3 says footnote `identifier` and `label` are "both
  case-folded by Wenmode". Wenmode 0.15.2 case-folds only `identifier`. A
  definition's `label` keeps its source spelling, and every reference that
  resolves to it repeats the first matching definition's spelling. Evidence:
  `x[^f]\n\n[^F]: n\n` gives `{"identifier": "f", "label": "F"}` on both nodes;
  `x[^a]\n\n[^A]: one\n[^a]: two\n` gives the reference and first definition
  `label: "A"` and the second definition `label: "a"`, all with
  `identifier: "a"`. No corpus source has an upper-case definition, so neither
  the ADR probe nor the corpus could see this. Impact: D2 corrects the text
  before any fixture lands.
- Observation: 84 of the 94 Markdown corpus cases strictly equal raw Wenmode
  0.15.2 output, ignoring key order. All 48 cases tagged NF-2 to NF-7 match,
  and 17 corpus relation groups lie wholly inside that subset. None of the 48
  raw outputs has a mergeable text run, an empty `data`, or a CR. Evidence: a
  scratch comparison under `/tmp/probe-123/`, re-run independently by a panel
  reviewer. Impact: D3 runs the subset against the parser without a
  canonicalizer.
- Observation: of the 10 non-matching cases, 9 differ only through
  canonicalization rules (`normalize-line-endings`, `merge-plain-text`).
  `list-loose` (NF-10) is a genuine disagreement: Wenmode gives the second item
  of `- a\n\n- b\n` `"spread": false`, while the golden says `true`. Impact: it
  is outside 1.2.3's areas. It is recorded for roadmap 2.1.1 and raised with
  the maintainer in the pull request (D8).
- Observation: Wenmode 0.15.3 (2026-10-19) and 1.0.0rc1 (2026-10-21) are on
  PyPI. 0.15.3 matches 0.15.2 on the whole corpus. 1.0.0rc1 keeps all 48 NF-2
  to NF-7 cases but changes NF-13: `&#xD800;` and `&#x110000;` now become
  U+FFFD instead of staying literal. Impact: a real upstream change that the
  corpus detects; it is useful evidence for 3.2.1 and the EP-M6 drill.
- Observation: HTML filtering is decided per `html` node, not per tag.
  Evidence:
  - `<pre>\n<iframe>\n</pre>\n` and `<script>\n<iframe>\n</script>\n` stay
    one unescaped node: type-1 blocks, including `<pre>`, suppress filtering
    of nested tags.
  - `<div>\n<script>\n</div>\n`, `<!-- <iframe> -->\n`, and
    `<a href="<iframe>">` are escaped as whole nodes.
  - Inline `<script>`, `<style>`, and `<textarea>` are escaped.
  - `<iframes>` and `<titlex>` are not escaped.
  - Block forms: `<T>\nb\n</T>\n` is one node with a trailing newline for
    every tested tag. Inline forms give one node per tag, without the
    newline.

  Impact: the draft's per-tag `INV-HTML` was false. It is restated per node
  (D13), and D2 records the scope.
- Observation: decision-relevant behaviours that ADR-004 does not state:
  - The first ordinary definition wins (`[a]: /u\n[a]: /v\n\n[a]\n` gives url
    `/u`).
  - Duplicate footnote definitions are all retained in source order with one
    shared `identifier`.
  - A footnote definition with an empty body has `children: []`.
  - An explicitly empty title is `""`, which differs from an absent title.
  - Image `alt` is always present and may be `""`.
  - Labels match across case and internal whitespace (`[a  b]` resolves
    against `[A B]: /u (t)`).
  - `start: 0` and `checked: false` are present, not dropped.
  - A definition inside a block quote leaves
    `{"type": "blockquote", "children": []}`.

  Impact: D2 records the first five as clarifications. The rest are pinned
  under existing clauses (the matching rules under NF-2, and the falsy values
  under NF-4). The empty block quote is recorded for 2.1.1 and not pinned (D9).
- Observation: Wenmode's public presets give genuine alternative parsers:
  - `presets.streaming()` leaves references and footnotes literal and does not
    escape `<iframe>`.
  - `presets.commonmark()` leaves footnotes and tables as paragraphs and does
    not escape `<iframe>`.
  - `create_preset(github(), replace=[RawHtml(), HtmlBlock()])` changes only
    HTML escaping.

  None of them warns under `-W error`. Impact: they provide falsifiable red
  controls (D14).
- Observation: the CodeGraph MCP server failed to connect during planning, so
  reconnaissance used file reads and `grep`. Impact: none on the plan;
  implementers should retry CodeGraph first.
- Observation: `uv export` writes ANSI colour codes when stdout is redirected
  in this environment; `-o FILE` avoids that. `uv pip install` spells the flag
  `--overrides`. Impact: the drill (EP-M6) uses `uv export -o` and
  `uv run --isolated --with-requirements`, with no project install.

## Decision log

- D1. Decision: the four roadmap areas map to ADR-004 NF-2 (references), NF-3
  (footnotes), NF-4 and NF-5 (nullable members and `null` array elements), and
  NF-6 and NF-7 (raw HTML). NF-5 is included because "omitted nullable fields"
  only has meaning alongside the one place where `null` *is* preserved.
  Rationale: the roadmap names areas, not identifiers. NF-1 and NF-8 to NF-13
  stay with roadmap 2.1.x. Date/Author: 2026-11-16, planning agent; confirmed
  by panel review.
- D2. Decision: add a dated amendment to ADR-004. It corrects NF-3's label
  wording, clarifies NF-2 to NF-7 where review showed gaps, and leaves the
  contract version at 1. Legitimacy: ADR-004 `### Amendments` and ADR-003
  ("Before the first release whose `serialize()` writes payloads, a correction
  to the v1 definition may be made in ADR-004 with a dated amendment") allow
  it, and `serialize()` still raises `NotImplementedError`. This is a
  pre-release correction to the v1 definition, not a payload-neutral
  clarification: under the old wording, `[^F]:` and `[^f]:` definitions would
  be equal. No committed golden changes. Following the repository precedent
  (`docs/adrs/adr-0001-python-lint-architecture.md` line 74, and the
  documentation style guide's amendment banner rule), EP-M1 makes three edits:
  - Add to ADR-004 `## Status` the line
    `Amended (2026-11-16): see [the footnote-label and HTML-scope amendment](#amendment-2026-11-16-footnote-labels-and-html-filtering-scope).`
  - Change `## Date` to `2026-11-16 (last updated).`
  - Insert the following section immediately before the
    `[maintainer-acceptance]:` link definition:

  ```markdown
  ## Amendment (2026-11-16): footnote labels and HTML filtering scope

  This pre-release amendment corrects one clause of NF-3 and clarifies NF-2 to
  NF-7, as the `### Amendments` section and ADR-003 permit before the first
  release whose `serialize()` writes payloads. Snapshot contract v1 keeps
  contract version 1. No committed corpus golden changes. Every other
  statement above continues to apply.

  - NF-3 correction. Wenmode case-folds a footnote `identifier`, but not its
    `label`. A `footnoteDefinition` keeps its own source spelling as `label`,
    and every `footnoteReference` that resolves to it repeats the first
    matching definition's `identifier` and `label`. References spelled `[^F]`
    and `[^f]` are therefore equal when they resolve to the same definition,
    while definitions spelled `[^F]:` and `[^f]:` are distinct.
  - NF-2 clarification. When several definitions share a normalized label, the
    first definition in source order wins, as CommonMark specifies.
  - NF-3 clarification. Duplicate footnote definitions are all retained in
    source order; they share one `identifier` and each keeps its own `label`.
    A definition with an empty body keeps an empty `children` array.
  - NF-4 clarification. An explicitly empty title, as in `[x](/u "")`, is the
    empty string, which is distinct from an absent `title`. An image's `alt`
    is always present and may be empty.
  - NF-6 and NF-7 clarification. Filtering applies per `html` node. Wenmode
    escapes a node when its value contains an opening or closing tag on
    GitHub's disallowed list, in any letter case and including inside
    attributes and comments. Escaping replaces the `<` of each such tag with
    `&lt;` and adds `data: {"escaped": true}`. CommonMark type-1 HTML blocks,
    which begin with `<script`, `<style`, `<textarea`, or `<pre`, are never
    escaped, including disallowed tags nested inside them. The same tags are
    escaped in inline positions. Tag names match exactly, so `<iframes>` and
    `<titlex>` are not escaped.
  ```

  Rationale: pinning observed behaviour against an ADR that says otherwise
  would leave two contradictory sources of truth. The draft's "lasting
  evidence" bullet was dropped because it would have been false until EP-M3,
  and amendments cannot be edited later. The developers' guide links to the
  amendment instead. Approving authority: the user (maintainer), as part of
  plan approval. Date/Author: 2026-11-16, planning agent (proposed), revised
  after the contracts review.
- D3. Decision: two oracles. First, run the existing corpus cases tagged NF-2
  to NF-7 through `parse_markdown` and compare them strictly with their
  canonical goldens (48 cases today). Second, add a small catalogue of probes
  only for behaviours that no corpus case exercises. Rationale: for these
  cases, the canonical form differs from raw output only in member order, and
  strict JSON equality ignores order. Reusing the reviewed corpus avoids a
  second golden per behaviour. The panel's strongest alternative, adding the
  uncovered behaviours as ordinary corpus cases, was weighed in D16.
  Date/Author: 2026-11-16, planning agent; revised after the maintainability
  review removed duplicated probes.
- D4. Decision: the catalogue is one strict JSON file,
  `tests/fixtures/wenmode_decisions/probes.json`. It holds a clause registry
  (each clause's ADR source, statement, classifier, probe IDs, and corpus case
  IDs) and probe records. Rationale: `AGENTS.md` asks for large test data in
  external files. JSON matches the goldens and reuses `read_expected_payload`'s
  duplicate-key and scalar checks. A separate catalogue keeps the corpus
  canonical-only and avoids growing files at the 400-line cap. Date/Author:
  2026-11-16, planning agent.
- D5. Decision: move `_strict_json_equal` out of
  `tests/support/markdown_contract.py` into a new
  `tests/support/strict_json.py` as `strict_json_equal(actual, expected)`,
  defined as `first_difference(actual, expected) is None`. Update its four
  callers (all inside `markdown_contract.py`) in the same commit, with no
  alias. The new module also holds `first_difference`, split into one helper
  per JSON kind, and `as_json_value(value: object) -> JSONValue`, which runs
  the existing scalar checks and then narrows. Rationale: Python `==` treats
  `True == 1` and `False == 0`, so plain equality would miss `checked: false`
  becoming `0`. Defining equality through the difference function makes "equal
  if and only if no difference" hold by construction. `parse_markdown` returns
  `dict[str, object]`, which is not assignable to the recursive `JSONValue`
  alias, so `ty` needs the narrowing helper. This is a test-only API, so no
  shim is needed. Date/Author: 2026-11-16, planning agent; revised after the
  maintainability review.
- D6. Decision: no Syrupy snapshot files. Rationale: the oracle must be
  independent and hand-reviewed. A Syrupy snapshot of parser output would be
  generated by the system under test and could be accepted with
  `--snapshot-update`, laundering exactly the change this task must catch. The
  project's own Markdown extension cannot serialize yet (roadmap 2.3.1).
  Consistency across variants is checked more strongly by strict equality,
  corpus relation groups, and the reference-form property. Date/Author:
  2026-11-16, planning agent; endorsed by panel review.
- D7. Decision: no Rust extension, Verus or Kani proof, or CrossHair run.
  Rationale: this task introduces no repository-owned business logic or axiom
  of its own. Its obligations are claims about a third-party parser, which are
  observed at the boundary as axioms. A Verus proof would have to assume
  Wenmode's behaviour and then restate it. The repository-owned logic (strict
  comparison, difference reporting, catalogue validation, selection, and clause
  classifiers) is small and covered by parametrized tests, a Hypothesis
  property, and seeded faults; CrossHair would add no reachable-path evidence
  beyond that. Date/Author: 2026-11-16, planning agent; endorsed by panel
  review.
- D8. Decision: leave `list-loose` and the 1.0.0rc1 NF-13 change out of scope.
  Add a note under roadmap 2.1.1 in EP-M6, and raise `list-loose` with the
  maintainer in the pull request description now. Rationale: the roadmap scopes
  1.2.3 to four areas, and correcting a golden needs its own review under
  ADR-004. Date/Author: 2026-11-16, planning agent.
- D9. Decision: do not pin the empty `blockquote` left by a definition inside
  a block quote. Rationale: no ADR clause addresses it, and pinning it would
  ratify a shape by stealth. Record it under roadmap 2.1.1 in EP-M6.
  Date/Author: 2026-11-16, planning agent.
- D10. Decision: Red-Green-Refactor applies as follows. For repository-owned
  support code, write failing tests first in the usual way. For parser
  characterization, the red stage is the real-preset controls (D14). Each
  control's *predicted* set of violated clauses is written into the controls
  table before the control is first run. Then each control is run under a
  known-different parser and must fail exactly as predicted, before the
  GitHub-profile probes are run green. Probe expectations are authored from ADR
  text before they are run. A mismatch is evaluated against the ADR, never
  silently copied. Rationale: the production code does not change, so a
  conventional red stage would be theatre. The preset controls give a
  falsifiable red run. Date/Author: 2026-11-16, planning agent; revised after
  the verification review.
- D11. Decision: the catalogue records `wenmode_evidence_version`. The loader
  requires it to equal the corpus manifest's `wenmode_evidence_version`. A
  single test, `test_evidence_version_matches_installed_wenmode`, compares that
  shared value with `importlib.metadata.version("wenmode")`. Rationale: one
  source of evidence-version truth, not two that can drift. It forces a
  deliberate review in the ADR-003 upgrade pull request, and the loader does
  not depend on the installed version, so the drill can show probes passing
  while only the tripwire fails. Date/Author: 2026-11-16, planning agent;
  revised after the contracts review.
- D12. Decision: attribute failures through clause classifiers. Each clause
  names at most one classifier from a closed set. Each classifier is a pure
  function over a raw tree, returning violation paths:
  - `reference-resolution` checks that no `definition`, `linkReference`, or
    `imageReference` node exists, and that no `link` or `image` has
    `identifier`, `label`, or `referenceType`.
  - `footnote-members` checks the exact member sets, and that a definition's
    `identifier` equals the ASCII-lower-cased `label`.
  - `footnote-label-provenance` checks that each reference's `identifier` and
    `label` equal those of the first definition with the same `identifier`.
  - `no-null-members` checks that no mapping member is `None`.
  - `image-alt-present` checks that every `image` has a string `alt`.
  - `align-elements` checks that `align` holds only `None`, `"left"`,
    `"center"`, or `"right"`, with one entry per cell of the first row.
  - `html-escape-scope` applies the per-node rule from D2.

  On a strict mismatch, `decision_mismatch(probe, actual)` runs the classifiers
  of the probe's clauses on the actual tree. It reports each violated clause
  with its paths, or, if none is violated, reports "unclassified drift" with
  the first differing path and the declared clauses as candidates. The same
  classifiers run on corpus cases (as clause evidence) and in the properties.
  Rationale: the draft could only repeat a probe's declared clauses, so "the
  check names NF-4" was nearly vacuous. Clauses without a tree-level rule (for
  example `NF-2.first-wins`) fall back honestly to drift with a path.
  Date/Author: 2026-11-16, planning agent, from the verification, contracts,
  and maintainability reviews.
- D13. Decision: `INV-HTML` is stated per `html` node (D2 wording). It is
  verified by an exhaustively parametrized grid, with Hypothesis used only for
  mixed-case spellings. Rationale: the space is finite (12 tags × 3 fixed
  spellings × 2 positions = 72 cases). `sampled_from` with 100 examples would
  not guarantee every class, which would make an "every event seen" check
  flaky. Date/Author: 2026-11-16, planning agent, from the verification and
  maintainability reviews.
- D14. Decision: patch `syrupy_mdast._wenmode.github` to provide real-preset
  red controls:
  - `presets.streaming` is predicted to violate the NF-2, NF-3, and NF-6
    evidence.
  - `presets.commonmark` is predicted to violate the NF-3, NF-5, and NF-6
    evidence, while NF-2 evidence passes.
  - `create_preset(github(), replace=[RawHtml(), HtmlBlock()])` is predicted
    to violate only `NF-6.escaped` and `NF-6.case` evidence.

  Synthetic regression doubles (a null title, kept definitions, folded labels,
  a dropped `data`) wrap the real parser and must each change the tree and
  violate exactly their own clause. Rationale: controls that mutate the
  *expected* tree only exercise the comparator. Alternative parsers exercise
  the whole pipeline. Date/Author: 2026-11-16, planning agent, from the
  verification review.
- D15. Decision: no checksum of `probes.json` in the ADR. Rationale: a
  checksum would force an ADR edit for every new probe, and amendments cannot
  be edited later. Instead:
  - each clause records `adr_source`, either an NF identifier or
    `Amendment 2026-11-16`;
  - an integrity test checks that the cited heading or NF bullet exists in
    the ADR file;
  - the developers' guide states that changing an existing `expected` value
    requires an ADR amendment or a superseding ADR, cited in the commit.

  Date/Author: 2026-11-16, planning agent.
- D16. Decision: keep the separate catalogue rather than the panel's "corpus
  as the only oracle" alternative. Adopt that alternative's core instead: no
  duplicated goldens, and corpus IDs treated as first-class evidence that BDD
  steps can name. Rationale: the alternative would add about 24 fixture files
  and force edits to `tests/test_markdown_contract.py` (398 lines) and
  `tests/support/markdown_contract_loading.py` (398 lines), both at the cap. It
  would also lose clause-level attribution. Date/Author: 2026-11-16, planning
  agent.
- D17. Decision: corpus selection uses the rule tags plus a structural guard
  that is independent of the tags. A selected case must have `line_endings` of
  `lf` or `none`, and its golden must contain no CR, no `position`, no empty
  `data`, and no adjacent exact-shape plain-text siblings. A violation is a
  loader error telling the author to add the transformation tag. Tests assert a
  minimum of 48 selected cases and that every clause-named corpus case is
  selected. Rationale: corpus tags mean "rule demonstrated", not
  "transformation needed", and the tag-based exclusion removes zero cases
  today. An exact count would break on the first 2.1.1 addition. Date/Author:
  2026-11-16, planning agent, from the contracts and maintainability reviews.
- D18. Decision: move `_table`, `_string`, and `_string_tuple` from
  `tests/support/markdown_contract_loading.py` into a new
  `tests/support/strict_fields.py` as public helpers, used by both loaders.
  This is a separate atomic refactor commit at the start of EP-M2. Rationale:
  it avoids a CodeScene duplication finding and keeps
  `markdown_contract_loading.py` under the cap (it shrinks). Date/Author:
  2026-11-16, planning agent, from the maintainability review.

## Outcomes & retrospective

Not started. Complete this section at each milestone and at completion. Before
the status becomes `COMPLETE`, reconcile every discovery with ADR-004, ADR-003,
and the design document.

## Context and orientation

Inspected base revision: `16f99f4` ("Define the internal Wenmode seam (1.2.2)
(#79)"). Line numbers below refer to that revision; relocate symbols with
`grep -n '<symbol>' <path>`.

The package is `syrupy_mdast/`. Its public surface is `MarkdownAstError` and
`MarkdownAstSnapshotExtension` (`syrupy_mdast/__init__.py`). The private module
`syrupy_mdast/_wenmode.py` (52 lines) defines the only parser entrypoint:

```python
def parse_markdown(source: str) -> dict[str, object]:
    return Parser(github(), positions=False).parse(source).to_ast()
```

It builds a fresh GitHub-profile parser per call, returns Wenmode's
mdast-shaped mapping unchanged, and lets Wenmode exceptions propagate. Nothing
in the package calls it yet. Tests may patch the module's `Parser` and `github`
names; 1.2.2's `tests/support/wenmode_adapter.py` (`RecordingAdapter`) does
this. Skylos excludes `tests/`, so new test helpers need no Skylos entries.

Raw Wenmode 0.15.2 output facts used here, all observed directly:

- Member order is `type`, `children`, then other members.
- `None`-valued members are omitted.
- `link` and `image` carry `url`, an optional `title`, and, on images, `alt`,
  but never `identifier` or `label`.
- Footnote nodes carry `identifier` and `label`.
- A filtered node looks like
  `{"type": "html", "data": {"escaped": true}, "value": "&lt;iframe ..."}`.

`wenmode.presets` publicly exports `github`, `commonmark`, `streaming`,
`create_preset`, the rule classes (`RawHtml`, `HtmlBlock`, and others), and
`GFM_DISALLOWED_HTML_TAGS`. In 0.15.2 that is the nine GFM tags: `iframe`,
`noembed`, `noframes`, `plaintext`, `script`, `style`, `textarea`, `title`, and
`xmp`.

The corpus lives in `tests/fixtures/markdown_contract/`. Its `manifest.toml`
opens with `corpus_version = 1`, `contract_version = 1`, and
`wenmode_evidence_version = "0.15.2"`, followed by 101 `[[cases]]`. Each case
has these fields:

- `id`
- `rules`: NF and transformation identifiers
- `reason`
- `witness`
- `kind`: `markdown` or `synthetic`
- `input`: a file under `sources/`
- `expected`: a file under `expected/`
- `line_endings`

The 36 `[[relations]]` have `id`, `relation` (`equal` or `distinct`), and
`cases`. Expected file names do not match case IDs, so always resolve through
the manifest. The loader is in `tests/support/markdown_contract_loading.py`:
`load_corpus(root) -> ContractCorpus`, with the evidence-version check at lines
183-185. The model is in `tests/support/markdown_contract.py`: `CaseRecord`,
`RelationRecord`, `ContractCorpus`, `read_source`, `read_expected_payload`,
`_strict_json_equal` (lines 159-183), `_assert_json_scalars`, `JSONValue`, and
`RULE_IDS`. The integrity tests are `tests/test_markdown_contract.py` and
`tests/test_markdown_contract_loading.py`.

The existing Wenmode tests from 1.2.1 and 1.2.2 set the patterns to follow:

- `tests/test_wenmode_adapter.py`: unit tests with recording doubles.
- `tests/test_wenmode_adapter_bdd.py` with
  `tests/features/wenmode_adapter.feature`: `scenarios(str(_FEATURE))`, a
  `scenario_state` dict fixture, and steps in the same module.
- `tests/test_wenmode_adapter_properties.py`: an `st.composite` strategy,
  `event()`, `@settings(max_examples=50, deadline=None)`, and `@example`.
- `tests/test_wenmode_adapter_concurrency.py` and
  `tests/test_wenmode_adapter_workers.py`.

The installed-wheel probe `tests/support/wenmode_runtime_probe.py` defines the
installation contract and must not be extended here.

The gates, from the `Makefile`, are as follows:

- `make check-fmt`: Ruff format check and `mdtablefix --check`.
- `make typecheck`: `ty check syrupy_mdast tests`.
- `make lint`: Ruff, `interrogate --fail-under 100`, two Pylint passes,
  `ambrleaks tests`, and Skylos.
- `make test`: `pytest -v -n auto`.
- `make markdownlint` and `make nixie`, for Markdown.
- `make fmt`, to apply formatting.

`make all` omits `markdownlint` and `nixie`, so run them explicitly. The
CodeScene CLI (`cs`) is installed at `~/.local/bin/cs`. Hosted CodeScene checks
pull-request code health, including test-support files.

Budget survey (feeds `Tolerances`):

- `tests/support/wenmode_adapter.py`: 354 lines.
- `tests/support/markdown_contract.py`: 335.
- `tests/support/markdown_contract_loading.py`: 398.
- `tests/test_markdown_contract_loading.py`: 400.
- `tests/test_wenmode_adapter_bdd.py`: 169.
- `tests/test_wenmode_adapter_properties.py`: 117.
- Corpus goldens average 26 lines (2,018 lines over 77 files).

Historical ExecPlans: 1.2.2 raised its budget after a 75% verification overrun,
1.1.3 waived its cap after a 35% overrun, and 1.2.1 set no budget.

Documentation to read before implementing:

- `AGENTS.md`.
- `docs/syrupy-mdast-design.md`, sections 7, 8, and 11.
- `docs/adrs/adr-0004-parser-profile-and-normalization.md`: NF-2 to NF-7,
  `### Evidence`, and `### Amendments`.
- `docs/adrs/adr-0003-snapshot-version-policy.md`: the "Wenmode upgrade
  workflow" and its versioning items 1 to 3.
- `docs/adrs/adr-0005-exact-wenmode-runtime-dependency.md`.
- `docs/adrs/adr-0001-python-lint-architecture.md` (the amendment format).
- `docs/developers-guide.md`: corpus workflow, "Upgrade Wenmode", and "Verify
  the internal Wenmode seam".
- `docs/complexity-antipatterns-and-refactoring-strategies.md`.
- `docs/documentation-style-guide.md`, including ADR amendments.
- `.rules/python-00.md`, `.rules/python-typing.md`,
  `.rules/python-return.md`,
  `.rules/python-exception-design-raising-handling-and-logging.md`, and
  `.rules/python-generators.md`.
- `tests/fixtures/markdown_contract/README.md`.

Skills to load:

- `execplans`, for this plan.
- `python-router`, routing to:
  - `python-testing`, for parametrization and pytest-bdd;
  - `hypothesis`, for EP-M4;
  - `python-data-shapes`, for the frozen dataclasses;
  - `python-types-and-apis`, for `JSONValue` narrowing;
  - `python-errors-and-logging`, for loader errors.
- `python-verification`, which confirms that CrossHair and mutmut are not
  warranted.
- `codescene-cli`, for `cs delta`.
- `codegraph-mcp`, retried, since it was unavailable during planning.
- `leta`, for navigation.
- `en-gb-oxendict-style`, for prose.
- `commit-message` and `pr-creation`.

Use the `scrutineer` agent to run full gates.

## Conformance basis

Upstream artefacts and revisions, all at `16f99f4`:

- Technical design: `docs/syrupy-mdast-design.md`.
  - Section 7: the parser profile and seam.
  - Section 8: the canonicalization contract, and its reference, footnote,
    and HTML paragraphs.
  - Section 11: Table 3's rows "Reference semantics", "Footnote structure",
    and "Preservation", and the sentence "Parser conformance remains Wenmode's
    responsibility".
- ADR-004 (accepted 2026-10-11, addendum 2026-10-30): NF-2 to NF-7,
  `### Evidence`, `### Amendments`, and Migration plan step 2 ("Add the lasting
  contract corpus and parser probes, with each fixture linked to an NF
  identifier").
- ADR-003: the "Wenmode upgrade workflow" (each entry that can affect
  GitHub-profile `to_ast()` output receives a fixture), and the pre-release
  amendment clause.
- ADR-005: the exact pin `wenmode==0.15.2`.
- Roadmap: `docs/roadmap.md` item 1.2.3, which requires 1.2.2 (complete).
- No Terms of Reference document exists for this project.

Derived requirements:

- `REQ-REF`: resolved ordinary references (NF-2) are pinned by executable
  evidence. The evidence covers full, collapsed, shortcut, and forward forms;
  case- and whitespace-insensitive matching; first definition wins; unresolved
  and unused references; and image forms.
- `REQ-FN`: structural footnotes (NF-3, as corrected by D2) are pinned. The
  evidence covers node members, label provenance, order, and unused, repeated,
  undefined, duplicate, and empty definitions.
- `REQ-NULL`: omitted nullable members (NF-4) and preserved `null` alignment
  elements (NF-5) are pinned. The evidence covers absent versus empty-string
  values, the presence of `alt`, and falsy `start: 0` and `checked: false`.
- `REQ-HTML`: raw HTML (NF-6) and the type-1 divergence (NF-7) are pinned per
  node. The evidence covers all nine disallowed tags and the allowed tags,
  three spellings, block and inline positions, nesting inside type-1 and
  ordinary blocks, attributes, comments, and tag-name boundaries.
- `REQ-FAIL`: a parser change to any pinned decision makes `make test` fail.
  The failure attributes the change to the violated clause, or reports
  unclassified drift with a path.
- `REQ-SEAM`: the evidence runs through `syrupy_mdast._wenmode.parse_markdown`.
- `REQ-ORACLE`: expectations are hand-authored, reviewed data, never
  regenerated, and each clause cites an ADR source.

Observed gaps:

- `GAP-NO-RUNNER`: no test executes the parser against NF-2 to NF-7. The ADR
  probe is prose, and the corpus is integrity-only.
- `GAP-NF3-TEXT`: ADR-004 NF-3 misdescribes label case folding.
- `GAP-UNPINNED`: none of the following has a fixture:
  - the NF-7 claims about `<xmp>` and `<plaintext>`, and `<noembed>` and
    `<noframes>`;
  - per-node filtering scope, type-1 nesting, and `<pre>`;
  - tag-name case and boundaries;
  - first-wins matching, and whitespace in label matching;
  - duplicate and empty footnote definitions;
  - empty titles, empty alt text, and falsy members.

Trace links:

```plaintext
ADR-004 NF-3 -> GAP-NF3-TEXT -> D2 -> EP-M1 -> ADR-004 Amendment (2026-11-16)
ADR-004 NF-2 -> REQ-REF -> EP-M3/EP-M4 -> test_corpus_case_matches_raw_parse, test_probe_matches_ratified_decision, test_reference_forms_resolve_identically
ADR-004 NF-3 -> REQ-FN -> EP-M3/EP-M4 -> test_corpus_case_matches_raw_parse, test_probe_matches_ratified_decision, test_footnotes_stay_structural
ADR-004 NF-4/NF-5 -> REQ-NULL -> EP-M3/EP-M4 -> test_probe_matches_ratified_decision, test_nullable_members_are_omitted
ADR-004 NF-6/NF-7 -> REQ-HTML -> EP-M3/EP-M4 -> test_probe_matches_ratified_decision, test_html_escape_grid
Roadmap 1.2.3 success -> REQ-FAIL -> D12/D14 -> EP-M3 -> test_preset_control_violates_predicted_clauses, test_regression_double_violates_its_clause
Roadmap 1.2.3 success -> REQ-FAIL -> D12 -> EP-M5 -> wenmode_normative_decisions.feature
Design §7 seam -> REQ-SEAM -> EP-M3 -> test_preset_control_violates_predicted_clauses (patches the seam's github)
ADR-004 Migration step 2 -> REQ-ORACLE -> D15 -> EP-M2 -> test_wenmode_decision_catalogue.py
ADR-003 upgrade workflow -> D11 -> EP-M2/EP-M6 -> test_evidence_version_matches_installed_wenmode, drill transcript
```

## Verification plan

### Abstract model

Let `P` be `parse_markdown`, which maps a Markdown string to a JSON value: a
root `dict[str, JSONValue]`, after `as_json_value` narrowing. Let `≡` be strict
JSON equality:

- Mappings are equal when they have the same member set and each member's
  values are strictly equal.
- Lists are equal when they have the same length and their elements are
  pairwise strictly equal.
- Scalars are equal when their types are identical and their values are
  equal, so `True` is not equal to `1`.
- Member order is ignored.

A decision clause `c` (for example, `NF-4.omitted`) is a property of pairs
`(source, P(source))`. The evidence for it takes three forms:

- Finite witnesses `(s, e)`, from catalogue probes and selected corpus cases,
  with the claim `P(s) ≡ e`.
- An optional tree-level classifier `K_c(tree) -> violations`. The claim is
  that `K_c(P(s))` is empty for every witness and every generated source.
- Universally quantified properties over small grammars.

Malformed catalogue data is a loader error (`ValueError` or `TypeError`, with
the file and member location), never a skipped probe. A parser exception is a
test failure, because every source is valid Markdown.

### Invariants and lemmas

- `INV-REF` (REQ-REF). The grammar `G_ref` draws:
  - a label `L` from ASCII letters and digits;
  - a reference spelling `L′`, a case variant of `L`;
  - a destination `u` from `/[a-z0-9]{1,8}`;
  - an optional title `t` of ASCII letters and single inner spaces, delimited
    by `"…"`, `'…'`, or `(…)`;
  - link text `x`;
  - a form: direct, full, collapsed, or shortcut;
  - a link or image node;
  - a definition placed before or after the use, always separated from it by
    a blank line.

  For every source in `G_ref`, `K_reference-resolution` is empty. All forms are
  strictly equal to the direct form. In the collapsed and shortcut forms the
  link text is `L′`, the reference spelling (so `[aB]` gives text `"aB"`). An
  image's `alt` equals its bracket text. An undefined label leaves the
  paragraph's concatenated text equal to the source line.
- `INV-FN` (REQ-FN). The grammar `G_fn` draws:
  - one to three labels that are distinct after lower-casing;
  - a source spelling for each definition;
  - case-varied references;
  - definitions placed before or after their references;
  - extra unused definitions;
  - an optional undefined reference.

  All blocks are separated by blank lines. For every source in `G_fn`,
  `K_footnote-members` and `K_footnote-label-provenance` are empty. The number
  of `footnoteReference` nodes equals the number of resolved reference
  occurrences. Definitions appear in source order. Unused definitions are
  present. An undefined reference's text survives in the paragraph's
  concatenated text, without assuming it forms a separate node.
- `INV-NULL` (REQ-NULL). The grammar `G_null` draws blocks from:
  - links and images, with and without titles, including `""`;
  - fences with no info string, a language only, or a language and meta;
  - bullet lists and ordered lists, with a start from 0 to 9;
  - task items with content, and plain items;
  - tables with pipes on every row and random alignments.

  Blocks are joined by `\n\n***\n\n`, so lists, tables, and paragraphs never
  merge. For every source in `G_null`, `K_no-null-members` and
  `K_image-alt-present` are empty. `None` occurs only as an `align` element,
  and exactly where the delimiter cell has no colon. `title` is present if and
  only if the source gave one. `lang` is present if and only if there is an
  info string, and `meta` if and only if the info string has a second word.
  `checked` is present if and only if the item has a task marker, including
  `checked: false`. `start` is present if and only if the list is ordered,
  including `start: 0`.
- `INV-HTML` (REQ-HTML). Consider every `html` node `n` produced by the grid.
  The grid takes the nine disallowed tags plus `pre`, `div`, and `span`, in
  three spellings (lower, UPPER, and Title), in two positions: the block form
  `<T>\nb\n</T>\n` and the inline form `a <T>b</T> c\n`. Add the fixed scope
  cases:
  - `<pre>\n<iframe>\n</pre>\n` and `<script>\n<iframe>\n</script>\n`;
  - `<div>\n<script>\n</div>\n`;
  - `<!-- <iframe> -->\n`;
  - `a <a href="<iframe>">b</a>\n`;
  - `<iframes>\n` and `x <titlex> y\n`.

  `n` is escaped exactly when it is not a type-1 block and its value contains a
  disallowed opening or closing tag, matched case-insensitively at a name
  boundary. A type-1 block is a block-level node whose value starts with
  `<script`, `<style`, `<textarea`, or `<pre`, case-insensitively. When `n` is
  escaped, `n["data"]` strictly equals `{"escaped": True}`, and `n["value"]`
  equals the unescaped form with the `<` of each disallowed tag replaced by
  `&lt;`. When `n` is not escaped, it has no `data` member. Block values end
  with `\n`; inline values are exactly the tag text. `K_html-escape-scope`
  implements this rule over trees.
- `INV-ATTR` (REQ-FAIL). Each real-preset control violates exactly its
  predicted clause set (D14). Each synthetic regression double changes the tree
  and violates exactly its own clause. GitHub-profile output violates no clause.
- `L-STRICT` (supports REQ-FAIL). `strict_json_equal(a, a)` holds for every
  JSON value `a`. It is false for every single-site mutation `m(a)`:
  - adding a member, including a `None`-valued one;
  - deleting a member;
  - renaming a member;
  - replacing a scalar with a different value, or with an equal value of a
    different type (`True` and `1`, `False` and `0`);
  - inserting or deleting a list element;
  - swapping two list elements with distinct values.

  Each mutation first asserts `m(a) != a` structurally, so it is never a no-op.
- `L-DIFF`. `first_difference(a, b)` returns `None` exactly when `a ≡ b`,
  which holds by construction (D5). Otherwise it returns a path such that the
  two values differ at that path.
- `L-CLASSIFY`. Each classifier returns no violations on its positive
  witnesses. It returns at least one violation, at the expected path, on its
  negative witness: a hand-written tree exhibiting exactly the regression.
- `L-SELECT`. The corpus selection holds exactly the Markdown cases whose
  `rules` intersect `{NF-2, …, NF-7}`, contain no transformation identifier,
  and pass the D17 structural guard. There are at least 48 of them, all of NF-2
  to NF-7 occur, and every corpus case named by a clause is selected. A case
  that fails the structural guard is a loader error.
- `L-COVER`. These integrity rules hold:
  - Every clause has at least one probe or selected corpus case.
  - Every probe names at least one registered clause.
  - Probe and clause identifiers are unique.
  - Every clause's `adr_source` resolves to an existing ADR-004 NF bullet or
    amendment heading.
  - Every classifier name is in the closed set.
  - The catalogue's evidence version equals the corpus manifest's.

### Axioms (trusted, not verified here)

- `AXIOM-DETERMINISM`: Wenmode is deterministic for a given source, version,
  and interpreter (Wenmode documentation; 1.2.2 evidence).
- `AXIOM-SEAM`: `parse_markdown` is the v1 construction. 1.2.2's tests verify
  this.
- `AXIOM-PIN`: the installed Wenmode is 0.15.2. This is verified by
  `tests/test_package_manifest_contract.py` and by D11's tripwire.
- `AXIOM-PRESETS`: `wenmode.presets.streaming`, `commonmark`, and
  `create_preset` are public, warning-free, and behave as observed in 0.15.2.
  They are used only as alternative parsers for controls.
- `AXIOM-GFM-TAGFILTER`: the GFM specification's disallowed list is
  `title`, `textarea`, `style`, `xmp`, `iframe`, `noembed`, `noframes`,
  `script`, and `plaintext`. A cheap tripwire compares this list with
  `wenmode.presets.GFM_DISALLOWED_HTML_TAGS`. Wenmode's observed behaviour, not
  the specification, is the oracle (NF-7).
- `AXIOM-ASCII-CASEFOLD`: for ASCII labels, CommonMark label normalization
  equals Python's `str.lower()` after collapsing whitespace.
- `AXIOM-HYPOTHESIS`: Hypothesis explores the declared strategies and reports
  failures faithfully.

### Methods, artefacts, and discharge

| Obligation           | Method                          | Artefact                                                                                                                                  | Discharged when                                                       |
| -------------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `INV-REF`            | Hypothesis + witnesses          | `tests/test_wenmode_normative_decision_properties.py::test_reference_forms_resolve_identically`                                           | passes; events show every form, placement, title delimiter, and kind  |
| `INV-FN`             | Hypothesis + witnesses          | same module, `test_footnotes_stay_structural`                                                                                             | passes; events show before, after, unused, undefined, and case-varied |
| `INV-NULL`           | Hypothesis + witnesses          | same module, `test_nullable_members_are_omitted`                                                                                          | passes; events show every optional member present and absent          |
| `INV-HTML`           | exhaustive parametrization      | `tests/test_wenmode_decision_html.py::test_html_escape_grid`, `test_html_escape_scope_cases`                                              | all 72 grid cases and the scope cases pass                            |
| `INV-ATTR`           | real-preset and double controls | `tests/test_wenmode_normative_decisions.py::test_preset_control_violates_predicted_clauses`, `test_regression_double_violates_its_clause` | each control matches its recorded prediction exactly                  |
| `L-STRICT`, `L-DIFF` | Hypothesis over JSON trees      | `tests/test_strict_json.py::test_single_mutations_are_detected`                                                                           | passes; events cover every mutation kind                              |
| `L-CLASSIFY`         | named examples                  | `tests/test_wenmode_decision_catalogue.py::test_classifier_witnesses`                                                                     | every positive is clean; every negative reports the expected path     |
| `L-SELECT`           | named assertions                | `tests/test_wenmode_normative_decisions.py::test_corpus_selection_covers_every_decision`, plus guard tests                                | at least 48, all NF-2 to NF-7 present, guard errors raised            |
| `L-COVER`            | integrity tests                 | `tests/test_wenmode_decision_catalogue.py`                                                                                                | all pass; every unhappy-path loader case raises                       |
| REQ-FAIL             | BDD                             | `tests/features/wenmode_normative_decisions.feature`                                                                                      | negative scenarios report exactly the named clause                    |

*Table 1: Verification obligations, methods, and discharge conditions.*

Run every obligation with this focused command:

```bash
set -o pipefail
uv run pytest -v -n 2 \
  tests/test_strict_json.py \
  tests/test_wenmode_decision_catalogue.py \
  tests/test_wenmode_normative_decisions.py \
  tests/test_wenmode_decision_html.py \
  tests/test_wenmode_normative_decision_properties.py \
  tests/test_wenmode_normative_decisions_bdd.py \
  --hypothesis-show-statistics 2>&1 | tee /tmp/test-syrupy-mdast-1-2-3-focused.out
```

### Non-vacuity

- `INV-REF`, `INV-FN`, and `INV-NULL`:
  - Each property carries `@example` witnesses for every class named in its
    invariant. These include `start: 0`, `checked: false`, the empty title,
    and a labels-differ-only-in-case pair.
  - Each property records `hypothesis.event()` labels.
  - Strategies build valid inputs constructively, without `assume()` or
    `.filter()`. Any "invalid" share above 5% is investigated; 1.2.2 recorded
    about 5%, all from entropy overruns.
  - Each property's check runs the same classifiers that D14's controls prove
    sensitive. A dedicated test feeds the property's check function one
    regression-double tree and requires rejection.
- `INV-HTML`: the grid is exhaustive over its finite space, so no class can be
  missed. The `create_preset(..., replace=[RawHtml(), HtmlBlock()])` control
  shows that the grid fails when escaping is absent.
- `INV-ATTR`: predictions are recorded before the first run (D10). A control
  that unexpectedly passes is a failure, not a skip.
- `L-STRICT` and `L-DIFF`:
  - Detection is asserted per mutation kind.
  - Events show that every kind occurred.
  - Named examples pin `True` against `1`, `False` against `0`, a
    `None`-valued added member, and swapped list elements.
- `L-CLASSIFY`: every classifier has at least one negative witness that must
  report a violation.
- `L-SELECT`: the minimum count, the per-rule check, and the guard's unhappy
  tests stop a manifest or selection change from silently emptying the suite.
  The tag-based exclusion removes zero cases today. This is stated in the
  developers' guide, so the filter is not mistaken for evidence.
- Upgrade drill (EP-M6): under Wenmode 1.0.0rc1 and 0.15.3, the
  evidence-version tripwire must fail and all decision evidence must pass. On
  1.0.0rc1, the whole-corpus scratch comparison must show the NF-13
  differences. Together these show that the mechanism detects real upstream
  changes.

### Residual gaps

Finite probes and bounded grammars cannot prove universal parser stability
(ADR-004, "Beta parser behaviour"). Non-ASCII labels, deep container nesting,
type-1 blocks inside block quotes or list items, and pathological inputs are
outside the grammars. Raw output is compared before canonicalization, so
canonical payload outcomes remain roadmap 2.1.2's obligation. Clauses without a
tree-level classifier (`NF-2.first-wins`, `NF-2.literal`, `NF-3.order`, and
`NF-4.empty-string`) are attributed as unclassified drift with a path rather
than by name.

## Behavioural specification and contract scenarios

These are contract scenarios for the internal parser seam, written in
behaviour-driven development (BDD) form: `Feature`, `Scenario`, `Given`, `When`,
`Then`. Like `tests/features/wenmode_adapter.feature`, they are not acceptance
tests of the public package. The phrase "decision evidence `<id>`" resolves to
a catalogue probe or a selected corpus case.

Path: `tests/features/wenmode_normative_decisions.feature`, bound by
`tests/test_wenmode_normative_decisions_bdd.py`. Milestone: EP-M5.
Requirements: REQ-REF, REQ-FN, REQ-NULL, REQ-HTML, and REQ-FAIL.

```gherkin
Feature: Wenmode's ratified GitHub-profile AST decisions
  The snapshot contract relies on four parser decisions from ADR-004. These
  scenarios parse decision evidence through the internal Wenmode seam.

  Scenario Outline: Ordinary reference forms resolve to the same link
    Given the decision evidence "<evidence>"
    When the evidence is parsed through the internal Wenmode seam
    Then the tree holds one link to "/u" titled "t"
    And the tree holds no definition, reference, identifier, or label member

    Examples:
      | evidence                   |
      | link-direct                |
      | link-full-reference-before |
      | link-full-reference-after  |
      | link-collapsed-reference   |
      | link-shortcut-reference    |

  Scenario: An unresolved reference image stays literal text
    Given the decision evidence "image-unresolved-reference"
    When the evidence is parsed through the internal Wenmode seam
    Then the tree holds no link or image node
    And the paragraph text equals the source line

  Scenario: Footnote labels keep the definition's spelling
    Given the decision evidence "footnote-label-from-definition"
    When the evidence is parsed through the internal Wenmode seam
    Then every footnote node has identifier "note" and label "Note"

  Scenario: Falsy and empty members are kept while absent ones stay absent
    Given the decision evidence "list-falsy-members"
    When the evidence is parsed through the internal Wenmode seam
    Then no member anywhere in the tree is null
    And the ordered list starts at 0 and the task item is unchecked

  Scenario: Disallowed tags nested in a type-1 block stay unescaped
    Given the decision evidence "html-type1-pre-nested-iframe"
    When the evidence is parsed through the internal Wenmode seam
    Then the tree is one unescaped html node equal to the source

  Scenario: Disallowed tags inside an allowed block escape the whole node
    Given the decision evidence "html-allowed-block-nested-script"
    When the evidence is parsed through the internal Wenmode seam
    Then the single html node is marked escaped

  Scenario Outline: A parser change to a ratified decision is attributed
    Given a parser double that <regression>
    When the decision evidence "<evidence>" is checked
    Then the check reports exactly the violated clause "<clause>"

    Examples:
      | regression                        | evidence                       | clause              |
      | synthesizes a null title on links | link-title-absent              | NF-4.omitted        |
      | keeps ordinary definition nodes   | link-full-reference-before     | NF-2.resolve        |
      | case-folds footnote labels        | footnote-label-from-definition | NF-3.label-spelling |
      | drops the escaped data marker     | html-filtered-iframe           | NF-6.escaped        |

  Scenario: Wenmode's CommonMark preset breaks the footnote and HTML decisions
    Given the internal seam uses Wenmode's CommonMark preset
    When every decision evidence item is checked
    Then the footnote, table alignment, and HTML evidence fails
    And the ordinary reference evidence passes
```

Probe IDs named here must match the EP-M3 catalogue. If EP-M3 renames a probe,
update this section in the same commit.

## Milestones and plateaus

### EP-M1: ADR amendment, design wording, and corpus reason text

Documentation and manifest metadata only. Assigned: `GAP-NF3-TEXT` and D2.

1. Apply D2's three edits to ADR-004: the Status line, the Date line, and the
   amendment section, inserted before `[maintainer-acceptance]:`.
2. In `docs/syrupy-mdast-design.md` section 8, amend the footnote paragraph:
   identifiers are case-folded while labels keep the definition's spelling.
   Amend the raw HTML paragraph to say that filtering is per node, with type-1
   blocks exempt. Cite the amendment in both.
3. In `tests/fixtures/markdown_contract/manifest.toml`, reword the `reason`
   of `footnote-case-upper` and `footnote-case-lower` from "footnote labels are
   folded" to "footnote identifiers are folded". Run
   `uv run pytest -q tests/test_markdown_contract.py tests/test_markdown_contract_loading.py`
   to confirm that the reason text is not otherwise constrained.

End state: the ratified text matches observed behaviour before any fixture
exists, as design section 11 requires. Acceptance: `make fmt`,
`make markdownlint`, `make nixie`, and the two corpus test modules pass.
Conformance check: no golden or `expected` file changes; `git diff --stat`
shows only the ADR, the design document, and `manifest.toml`. Recovery: revert
the single commit.

### EP-M2: shared readers, strict JSON, and catalogue model

Assigned: `L-STRICT`, `L-DIFF`, `L-COVER` (for corpus-backed clauses), D5, D11,
D15, D17, and D18.

1. Refactor (its own commit). Move `_table`, `_string`, and `_string_tuple`
   to `tests/support/strict_fields.py` as `table`, `string`, and
   `string_tuple`, with docstrings and examples, and update
   `markdown_contract_loading.py`. Run the two corpus test modules and the four
   gates. No behaviour changes.
2. Red. Write `tests/test_strict_json.py`: named examples, plus the
   `L-STRICT`/`L-DIFF` property over a recursive JSON strategy. Write
   `tests/test_wenmode_decision_catalogue.py` covering:
   - a valid miniature catalogue written to `tmp_path`;
   - the unhappy paths, each raising with a location: a duplicate probe or
     clause ID, an unknown clause, an unknown classifier, a clause with no
     evidence, an unselected or missing corpus case, a probe with no clause,
     an unresolvable `adr_source`, a duplicate JSON member, a float scalar, a
     non-string source, a non-root `expected`, and an evidence version that
     differs from the corpus manifest;
   - the D17 structural guard rejecting a synthetic case whose golden holds
     adjacent plain text nodes;
   - `test_evidence_version_matches_installed_wenmode`.

   Run them. They fail with `ModuleNotFoundError` for
   `tests.support.strict_json` and `tests.support.wenmode_decisions`, which is
   the expected red.
3. Green. Create `tests/support/strict_json.py` (D5), move the callers in
   `markdown_contract.py` to `strict_json_equal`, and create
   `tests/support/wenmode_decisions.py` with the interface in
   `Interfaces and dependencies`. Create
   `tests/fixtures/wenmode_decisions/probes.json` containing only the header
   and the clauses that already have corpus evidence: `NF-2.resolve`,
   `NF-2.casefold`, `NF-2.unused`, `NF-2.literal`, `NF-2.image`,
   `NF-3.structural`, `NF-3.order`, `NF-3.unused`, `NF-3.repeat`,
   `NF-3.literal`, `NF-4.omitted`, `NF-5.align-null`, `NF-6.escaped`,
   `NF-6.allowed`, and `NF-7.type-1`. Each clause in this commit lists only
   corpus case IDs, and its `classifier` is left `null` until EP-M3. Create
   `tests/fixtures/wenmode_decisions/README.md` covering the schema, the
   hand-authoring rule, how to add a probe, and the expected-change rule (D15).
4. Refactor, then run the focused tests, the four gates, and
   `cs delta origin/main`.

End state: a validated, parser-free catalogue model whose registry passes
integrity. Recovery: revert the milestone's commits.

### EP-M3: classifiers, probes, conformance, and controls

Assigned: REQ-REF, REQ-FN, REQ-NULL, REQ-HTML, REQ-SEAM, REQ-FAIL, `INV-ATTR`,
`L-CLASSIFY`, `L-SELECT`, `GAP-NO-RUNNER`, and `GAP-UNPINNED`.

1. Red for the classifiers. Write `test_classifier_witnesses`, a parametrized
   table of hand-written positive and negative trees per classifier, and see it
   fail. Then create `tests/support/wenmode_decision_rules.py` with the seven
   classifiers from D12. Each is a small function returning
   `tuple[Violation, ...]`, where `Violation` is a frozen `(clause, path)`
   pair. Fill in each registered clause's `classifier` in `probes.json`.
2. Author the probes from the ADR and D2 text before running them (D10). Add
   the clauses `NF-2.first-wins`, `NF-3.label-spelling`, `NF-3.duplicate`,
   `NF-4.empty-string`, `NF-4.alt-present`, `NF-6.case`, and
   `NF-7.type-1-nested`, each with `adr_source` set to `Amendment 2026-11-16`
   or to its NF bullet. `NF-4.empty-string` also cites ADR-004's normalization
   policy ("preserves … empty strings"). The minimum set, all non-duplicating,
   with IDs stable once committed:
   - NF-2: `reference-first-definition-wins`,
     `reference-label-whitespace-and-case` (`[a  b]` and `[A B]: /u (t)`),
     `reference-title-delimiters` (`'t'` and `(t)` forms), and
     `reference-in-footnote-body`, which also covers NF-3.
   - NF-3: `footnote-label-from-definition` (`x[^note] y[^NOTE]\n\n[^Note]:
     n\n`), `footnote-duplicate-definitions`, and
     `footnote-empty-definition`.
   - NF-4: `link-title-empty`, `image-alt-empty-title-empty`, and
     `list-falsy-members` (`0. a`, `- [ ] a`, and a plain item, separated by
     thematic breaks).
   - NF-6 and NF-7: `html-type1-pre-nested-iframe`,
     `html-type1-script-nested-iframe`, `html-type1-uppercase-script`,
     `html-allowed-block-nested-script`, `html-comment-nested-iframe`,
     `html-attribute-nested-iframe`, and `html-name-boundary` (`<iframes>`
     and inline `<titlex>`).
3. Write `tests/test_wenmode_normative_decisions.py` with these tests:
   - `test_probe_matches_ratified_decision` and
     `test_corpus_case_matches_raw_parse`. Both are parametrized from the
     catalogue and the selection. If the catalogue fails to load, a single
     `catalogue-load-error` parameter fails, carrying the located message.
     Both assert `decision_mismatch(...) is None`, using the mismatch text as
     the assertion message.
   - `test_evidence_satisfies_clause_classifiers`: every probe and selected
     corpus case passes the classifiers of every clause that names it.
   - `test_corpus_relations_hold_on_raw_parse`: for every relation whose
     cases are all selected (17 today), `equal` groups must be strictly equal
     and `distinct` groups pairwise unequal.
   - `test_corpus_selection_covers_every_decision` (`L-SELECT`).
   - `test_disallowed_tag_list_matches_gfm` (the `AXIOM-GFM-TAGFILTER`
     tripwire).
   - `test_preset_control_violates_predicted_clauses`. This is parametrized
     over a `PresetControl` dataclass table in
     `tests/support/wenmode_decision_doubles.py`: one row each for
     `streaming`, `commonmark`, and `create_preset` with `RawHtml` and
     `HtmlBlock` replaced. Each row records its predicted violated clause set
     before the first run. The test monkeypatches
     `syrupy_mdast._wenmode.github` and asserts that the set of clauses with
     failing evidence equals the prediction.
   - `test_regression_double_violates_its_clause`. This is parametrized over
     a `RegressionDouble` table that wraps the real `Parser`: a null title,
     kept definitions, folded labels, and dropped `data`. Each case asserts
     that the tree changed and that exactly its clause is reported.
4. Run the controls first and confirm the predictions (red). Then run the
   GitHub-profile evidence (green). If a probe disagrees with its authored
   expectation, apply the "Decision drift" tolerance. If a control disagrees
   with its prediction, apply the "Control prediction" tolerance.

End state: every ratified clause has parser-backed, attributable evidence.
Gates: the focused command, the four gates, and `cs delta origin/main`.
Recovery: revert the milestone's commits.

### EP-M4: generated and exhaustive invariants

Assigned: `INV-REF`, `INV-FN`, `INV-NULL`, and `INV-HTML`.

1. Create `tests/support/wenmode_decision_strategies.py` with constructive
   `st.composite` strategies, following the grammar rules in the `INV-*`
   statements:
   - Use blank lines around definitions.
   - Use labels that are distinct after lower-casing.
   - Join `G_null` blocks with `\n\n***\n\n`.
   - Put pipes on every table row.
   - Always put content after a task marker.

   Each strategy returns the source together with the model its property checks
   against.
2. Write `tests/test_wenmode_normative_decision_properties.py` with the
   reference, footnote, and nullable properties. Use
   `@settings(max_examples=100, deadline=None)`, `@example` witnesses per
   class, and `event()` labels.
3. Write `tests/test_wenmode_decision_html.py` with `test_html_escape_grid`,
   the 72 cases parametrized with `ids=` such as `iframe-upper-inline`;
   `test_html_escape_scope_cases`; and one Hypothesis test over mixed-case
   spellings.
4. If any module approaches 400 lines, split it by decision family.

End state: the universal clauses hold across generated and enumerated inputs.
Acceptance: the focused command with `--hypothesis-show-statistics` shows every
event label and an invalid share under 5%, and the four gates and `cs delta`
pass. Recovery: revert.

### EP-M5: behavioural contract scenarios

Assigned: REQ-FAIL and readable acceptance.

1. Add the feature file from
   `Behavioural specification and contract scenarios`, and
   `tests/test_wenmode_normative_decisions_bdd.py`.
2. Follow `tests/test_wenmode_adapter_bdd.py`:
   - bind with `scenarios(str(_FEATURE))`;
   - keep shared state in a `scenario_state` fixture;
   - give every step a docstring and every assert a message;
   - use `parsers.parse` for quoted arguments.
3. Reuse `tests/support/wenmode_decision_doubles.py` for the regression
   doubles and the CommonMark preset. Patch only through `monkeypatch`.

End state: reviewers can read the decisions as scenarios, and the attribution
path is exercised end to end. Gates: the focused command, the four gates, and
`cs delta origin/main`. Recovery: revert.

### EP-M6: upgrade drill, documentation, and closure

Assigned: D11 evidence, the documentation obligations, and roadmap closure.

1. Upgrade drill. This is manual evidence, not CI, because it needs the
   network and other Wenmode versions. Nothing is built or installed into the
   worktree or `/tmp`. Wenmode is pure Python, and the tests import
   `syrupy_mdast` from the repository root. `uv run --isolated` keeps its
   ephemeral environment in uv's own cache.

   ```bash
   set -o pipefail
   uv export --frozen --no-hashes --no-emit-project --no-header \
     --no-emit-package wenmode -o /tmp/drill-reqs-syrupy-mdast.txt
   for version in 1.0.0rc1 0.15.3; do
     uv run --isolated --no-project --python 3.12 \
       --with-requirements /tmp/drill-reqs-syrupy-mdast.txt \
       --with "wenmode==${version}" \
       python -m pytest -p no:cacheprovider -q \
         tests/test_wenmode_decision_catalogue.py \
         tests/test_wenmode_normative_decisions.py \
         tests/test_wenmode_decision_html.py \
       2>&1 | tee "/tmp/drill-${version}-syrupy-mdast-1-2-3.out"
   done
   git status --short   # expect no output
   ```

   Expected: `test_evidence_version_matches_installed_wenmode` fails, naming
   the drilled version, and all decision evidence passes on both versions.
   Before running the drill, confirm that this exact invocation still works, by
   running `tests/test_wenmode_adapter.py`. During planning it passed 23 tests
   under 1.0.0rc1. Paste concise transcripts into `Outcomes & retrospective`.
   Any other result goes to `Surprises & discoveries` and is evaluated under
   "Decision drift".
2. Documentation. Delegate mechanical prose edits to `scribe` where useful.
   - `docs/developers-guide.md`:
     - Add a section, "Verify Wenmode's normative AST decisions", covering:
       - the layout;
       - how to add a probe or clause;
       - the classifier set;
       - the strictness rule;
       - the selection rule and structural guard, noting that the tag-based
         exclusion removes nothing today;
       - the focused command;
       - the drill;
       - the expected-change rule (D15);
       - a link to the ADR-004 amendment.
     - Extend "Upgrade Wenmode" with the decision suites and drill, and with
       updating both evidence versions only after the ADR-003 report.
     - Warn in the corpus section that editing NF-2 to NF-7 cases now
       affects the decision suite.
     - Record the `tests/support/strict_json.py`,
       `tests/support/strict_fields.py`, and
       `tests/support/wenmode_decisions.py` re-use policy.
   - `docs/syrupy-mdast-design.md` section 8: replace "they do not run a
     parser or canonicalizer" with a statement that the NF-2 to NF-7 subset
     is also run against raw parser output.
   - `docs/syrupy-mdast-design.md` section 11: add a Table 3 row, "Parser
     decisions", with the method "Corpus subset, focused probes, clause
     classifiers, generated grammars, and real-preset controls through the
     seam" and the boundary "Raw output only; finite grammars". After
     "Parser conformance remains Wenmode's responsibility", add a sentence
     stating that this project pins the ratified decisions it depends on.
   - `tests/fixtures/markdown_contract/README.md`: replace "It is test data;
     it does not run Wenmode" with wording that names the decision suite as
     the one consumer that runs the NF-2 to NF-7 subset. Add the authoring
     rule: an NF-2 to NF-7 case without a transformation tag must equal raw
     parser output.
   - `docs/contents.md`: already indexes this ExecPlan.
   - `docs/users-guide.md`: no change, because there is no behaviour or
     public API change. Record this in `Outcomes & retrospective`.
   - `docs/roadmap.md`:
     - Mark 1.2.3 `[x]` with a one-line "Current deliverable" note naming the
       suites.
     - Under 2.1.1, note the `list-loose` disagreement (D8) and the empty
       block quote observation (D9).
3. Run `make fmt`, `make check-fmt`, `make typecheck`, `make lint`,
   `make test`, `make markdownlint`, and `make nixie` sequentially through
   `scrutineer`, then `cs delta origin/main`. Reconcile the discoveries with
   ADR-004, ADR-003, and the design document, then set the status to `COMPLETE`.

## Concrete steps and acceptance

Run every gate sequentially from the repository root and log each one:

```bash
set -o pipefail
branch=$(git branch --show-current)
make check-fmt 2>&1 | tee "/tmp/check-fmt-syrupy-mdast-${branch}.out"
make typecheck 2>&1 | tee "/tmp/typecheck-syrupy-mdast-${branch}.out"
make lint 2>&1 | tee "/tmp/lint-syrupy-mdast-${branch}.out"
make test 2>&1 | tee "/tmp/test-syrupy-mdast-${branch}.out"
make markdownlint 2>&1 | tee "/tmp/markdownlint-syrupy-mdast-${branch}.out"
make nixie 2>&1 | tee "/tmp/nixie-syrupy-mdast-${branch}.out"
cs delta origin/main 2>&1 | tee "/tmp/cs-delta-syrupy-mdast-${branch}.out"
```

Expected at completion: every target exits 0, and `cs delta` reports no
declining code health. `make test` names each probe and corpus parameter by ID,
for example `test_corpus_case_matches_raw_parse[footnote-case-upper] PASSED`.
Commit after each milestone with an imperative subject, for example "Pin
Wenmode reference and footnote decisions (1.2.3)".

Acceptance summary:

1. `make test` passes. The new suites run at least 48 corpus conformance
   cases, at least 16 catalogue probes, the 72-case HTML grid, and three
   properties.
2. Each real-preset control violates exactly its predicted clauses. Each
   regression double, and each negative BDD row, reports exactly its clause.
3. The upgrade drill shows the tripwire firing while all decision evidence
   passes on 0.15.3 and 1.0.0rc1.
4. ADR-004, the design document, the developers' guide, both fixture READMEs,
   and the roadmap are updated as described, and the corpus goldens are
   unchanged.

## Idempotence and recovery

All steps can be re-run. Tests write only to pytest's `tmp_path`. The drill
writes one requirements file and logs under `/tmp`, uses uv's cache for its
ephemeral environment, and must leave `git status --short` empty. Each
milestone consists of one or more commits that can be reverted independently,
in reverse order. EP-M1 must precede any fixture commit, and the EP-M2 refactor
commit must precede the loader. If a gate fails, read the cited `/tmp` log
rather than re-running it, and re-run only after a fix.

## Interfaces and dependencies

There are no production interface changes. The test-support interfaces are as
follows.

```python
# tests/support/strict_json.py
def first_difference(actual: JSONValue, expected: JSONValue, path: str = "root") -> str | None: ...
def strict_json_equal(actual: JSONValue, expected: JSONValue) -> bool: ...  # first_difference(...) is None
def as_json_value(value: object, location: str) -> JSONValue: ...

# tests/support/strict_fields.py (moved from markdown_contract_loading.py)
def table(value: object, location: str) -> dict[str, object]: ...
def string(value: object, location: str) -> str: ...
def string_tuple(value: object, location: str) -> tuple[str, ...]: ...

# tests/support/wenmode_decisions.py
type ClassifierName = typ.Literal[
    "reference-resolution", "footnote-members", "footnote-label-provenance",
    "no-null-members", "image-alt-present", "align-elements", "html-escape-scope",
]

@dataclasses.dataclass(frozen=True, slots=True)
class DecisionClause:
    id: str                          # for example "NF-4.omitted"
    adr_source: str                  # "NF-4" or "Amendment 2026-11-16"
    statement: str
    classifier: ClassifierName | None
    probes: tuple[str, ...]
    corpus_cases: tuple[str, ...]

@dataclasses.dataclass(frozen=True, slots=True)
class DecisionProbe:
    id: str
    clauses: tuple[str, ...]
    reason: str
    source: str
    expected: JSONValue

@dataclasses.dataclass(frozen=True, slots=True)
class DecisionCatalogue:
    catalogue_version: int
    contract_version: int
    wenmode_evidence_version: str
    clauses: tuple[DecisionClause, ...]
    probes: tuple[DecisionProbe, ...]

def load_decision_catalogue(path: Path, *, corpus: ContractCorpus) -> DecisionCatalogue: ...
def select_decision_corpus_cases(corpus: ContractCorpus) -> tuple[CaseRecord, ...]: ...
def decision_mismatch(evidence: DecisionEvidence, actual: JSONValue) -> str | None: ...

# tests/support/wenmode_decision_rules.py
@dataclasses.dataclass(frozen=True, slots=True)
class Violation:
    clause: str
    path: str

def classify(classifier: ClassifierName, clause: str, tree: JSONValue) -> tuple[Violation, ...]: ...
```

`DecisionEvidence` is a frozen dataclass holding the evidence ID, its clauses,
its source, and its expected tree. It is built from either a probe or a
selected corpus case, so `decision_mismatch` keeps two parameters.

Scope and re-use policy. These modules are test-only and own raw-parser
decision evidence. Roadmap 2.1.1 may reuse `select_decision_corpus_cases`,
`first_difference`, and the classifiers for wider corpus conformance.
Canonicalization must not be added here. The developers' guide records this
policy (EP-M6).

The catalogue schema (`tests/fixtures/wenmode_decisions/probes.json`) is:

```json
{
  "catalogue_version": 1,
  "contract_version": 1,
  "wenmode_evidence_version": "0.15.2",
  "clauses": [
    {
      "id": "NF-3.label-spelling",
      "adr_source": "Amendment 2026-11-16",
      "statement": "A footnote label keeps the first matching definition's spelling; references repeat it.",
      "classifier": "footnote-label-provenance",
      "probes": ["footnote-label-from-definition", "footnote-duplicate-definitions"],
      "corpus_cases": ["footnote-case-upper", "footnote-case-lower"]
    }
  ],
  "probes": [
    {
      "id": "footnote-label-from-definition",
      "clauses": ["NF-3.label-spelling", "NF-3.structural"],
      "reason": "Upper- and lower-case references resolve to one definition and repeat its spelling.",
      "source": "x[^note] y[^NOTE]\n\n[^Note]: n\n",
      "expected": {
        "type": "root",
        "children": [
          {
            "type": "paragraph",
            "children": [
              {"type": "text", "value": "x"},
              {"type": "footnoteReference", "identifier": "note", "label": "Note"},
              {"type": "text", "value": " y"},
              {"type": "footnoteReference", "identifier": "note", "label": "Note"}
            ]
          },
          {
            "type": "footnoteDefinition",
            "identifier": "note",
            "label": "Note",
            "children": [{"type": "paragraph", "children": [{"type": "text", "value": "n"}]}]
          }
        ]
      }
    }
  ]
}
```

The final clause registry is: `NF-2.resolve`, `NF-2.casefold`,
`NF-2.first-wins`, `NF-2.unused`, `NF-2.literal`, `NF-2.image`,
`NF-3.structural`, `NF-3.label-spelling`, `NF-3.order`, `NF-3.unused`,
`NF-3.repeat`, `NF-3.literal`, `NF-3.duplicate`, `NF-4.omitted`,
`NF-4.empty-string`, `NF-4.alt-present`, `NF-5.align-null`, `NF-6.escaped`,
`NF-6.allowed`, `NF-6.case`, `NF-7.type-1`, and `NF-7.type-1-nested`. A new
clause requires an ADR-004 statement or amendment to cite.

Dependencies: none added. The work uses `pytest`, `pytest-bdd`, `hypothesis`,
the public `wenmode` and `wenmode.presets` modules, and the standard library
(`json`, `tomllib`, `dataclasses`, `importlib.metadata`, and `re`).

## Artefacts and external references

- GFM specification, section 6.11, "Disallowed Raw HTML (extension)":
  <https://github.github.com/gfm/#disallowed-raw-html-extension->, retrieved
  2026-11-16. It lists nine tags, filtered by replacing the leading `<` with
  `&lt;`.
- mdast specification: <https://github.com/syntax-tree/mdast>, retrieved
  2026-11-16. The `Association` mixin has `identifier` and an optional `label`;
  the `Resource` mixin has `url` and an optional `title`; `ListItem.spread`
  reports whether an item's own children are separated by a blank line.
- Wenmode release history: <https://pypi.org/pypi/wenmode/json>, retrieved
  2026-11-16. It lists 0.15.2 (2026-10-01), 0.15.3 (2026-10-19), and 1.0.0rc1
  (2026-10-21).
- Expert-panel reviews (verification rigour, contracts and ADR governance,
  and maintainability with pre-mortem and alternatives), 2026-11-16. Their
  findings are recorded in D2, D5, D10 to D18, and `Risks`.
- Planning scratch scripts, not committed, are in `/tmp/probe-123/`.

## Revision notes

- 2026-11-16 (revision 2, after expert-panel review):
  - D2 becomes a dated `## Amendment` with a Status pointer, framed as a
    pre-release correction. The "lasting evidence" bullet is dropped, and
    the per-node HTML scope, duplicate and empty footnote definitions, and
    `alt` are added.
  - Probes that duplicated corpus cases are removed (D3, D16).
  - Clause classifiers attribute failures (D12).
  - Real-preset controls give a falsifiable red stage (D10, D14).
  - `INV-HTML` is restated per node and enumerated exhaustively (D13).
  - Grammar hazards found by review are designed out (EP-M4).
  - Selection gains a structural guard and a minimum count (D17).
  - Shared readers move instead of being copied (D18).
  - The strict comparator is defined through `first_difference` (D5).
  - The evidence version is tied to the corpus manifest (D11).
  - Budgets are re-priced against the history.
  - The drill runs isolated, without a build or virtual environment under
    `/tmp`.
  - CodeScene is added to the gates.

  The milestone count is unchanged. EP-M2 now registers only corpus-backed
  clauses, so it can pass integrity on its own.
