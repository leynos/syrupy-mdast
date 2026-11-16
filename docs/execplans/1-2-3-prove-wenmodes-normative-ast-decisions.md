# Prove Wenmode's normative AST decisions (1.2.3)

This ExecPlan (execution plan) is a living document. The sections `Constraints`,
`Tolerances`, `Risks`, `Progress`, `Surprises & discoveries`, `Decision log`,
`Outcomes & retrospective`, `Conformance basis`, and `Verification plan` must
be kept up to date as work proceeds.

Status: DRAFT (awaiting user approval; implementation must not begin until the
user explicitly approves this plan, including the ADR-004 addendum text in
`Decision log` D2)

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

1. Ordinary reference links and images are resolved: `[x][r]` plus `[r]: /u`
   becomes a plain `link` node. No `definition`, `linkReference`, or
   `imageReference` node remains (NF-2).
2. Footnotes stay structural: `footnoteReference` and `footnoteDefinition`
   nodes keep `identifier`, `label`, children, and document order (NF-3).
3. Nullable members are omitted, not set to `null`: a link without a title has
   no `title` member, and a bullet list has no `start` member. The only `null`
   values are unaligned table columns inside `align` (NF-4 and NF-5).
4. Raw HTML stays an `html` node, and GitHub's disallowed tags are escaped by
   Wenmode with `data: {"escaped": true}`. CommonMark type-1 blocks (`<script>`,
   `<style>`, `<textarea>` at block start) are not filtered in Wenmode 0.15.2,
   and that divergence is ratified as observed (NF-6 and NF-7).

Today nothing in the repository runs the parser against these decisions. The
ADR's self-checking probe exists only as text in the ADR, and the
[canonical Markdown contract corpus](../../tests/fixtures/markdown_contract/README.md)
is validated for integrity only; its README says it "does not run Wenmode". A
Wenmode upgrade that quietly changed one of the four decisions, for example by
keeping `definition` nodes or by synthesizing `"title": null`, would pass every
current test.

After this change, a contributor runs `make test` and a dedicated suite parses
focused Markdown probes through the internal seam
`syrupy_mdast._wenmode.parse_markdown`. It compares each result strictly with
hand-authored expectations, runs the 48 corpus cases tagged NF-2 to NF-7
through the same seam, and checks generated documents against the decisions'
universal invariants. If a parser upgrade changes a ratified decision, the
suite fails and names the decision, for example:

```plaintext
FAILED tests/test_wenmode_normative_decisions.py::test_probe_matches_ratified_decision[link-title-absent]
AssertionError: decision NF-4.omitted changed in probe 'link-title-absent':
root.children[0].children[0].title: unexpected member (value None)
```

This closes roadmap item 1.2.3 and gives roadmap 2.1.1 (GitHub-profile parsing)
and 3.2.1 (the Wenmode upgrade report) an executable oracle for the four
decisions. No public API or user-visible behaviour changes.

## Constraints

- Implement only roadmap 1.2.3 and only after explicit user approval of this
  plan. Approval of this plan includes acceptance of the ADR-004 addendum text
  quoted in `Decision log` D2; if the user approves the plan but not that text,
  the plan is `BLOCKED` until the addendum is agreed.
- Do not modify production code under `syrupy_mdast/`. The seam
  `syrupy_mdast/_wenmode.py` stays exactly as delivered by 1.2.2. If a probe
  appears to need a production change, stop and escalate.
- Keep the exact pin `wenmode==0.15.2` (`pyproject.toml` line 15, ADR-005). Do
  not add runtime or development dependencies. `pytest`, `pytest-bdd`,
  `pytest-xdist`, `pytest-timeout`, and `hypothesis>=6,<7` are already in the
  `dev` dependency group.
- Expected trees are hand-authored data. Tests must never regenerate, rewrite,
  or "accept" them from parser output, and no `--snapshot-update` style path
  may exist for them. Do not edit corpus goldens under
  `tests/fixtures/markdown_contract/expected/` to match the parser.
- Do not implement canonicalization, shape validation, the JSON writer, input
  limits, or error translation. Those belong to roadmap 2.1.2, 2.1.1, 2.2.1,
  and later. Tests compare raw `to_ast()` output only, using order-insensitive
  strict JSON equality; they must not contain a partial canonicalizer.
- Keep every Python file at or below 400 lines (`max-module-lines = 400` in
  `pyproject.toml`; `AGENTS.md`). `tests/test_markdown_contract_loading.py`
  (400 lines) and `tests/support/markdown_contract_loading.py` (398 lines) are
  at the cap and must not grow.
- Keep Ruff `max-complexity = 8`, 100% `interrogate` docstring coverage for all
  new test functions, fixtures, steps, and helpers, and the PyPy and
  df12-python-lints Pylint passes clean. Use en-GB-oxendict spelling in
  comments and documentation.
- Place all tests under the top-level `tests/` tree. Do not add pytest markers
  that are not registered, and do not depend on the expensive session
  `wheelhouse` fixture in `tests/conftest.py`.
- Historical documents stay untouched: completed ExecPlans, the body of
  ADR-003, the body and existing addendum of ADR-004, and ADR-005. ADR-004
  changes only by a new dated addendum appended after the existing
  `## Addendum (2026-10-30)` (see D2).
- Treat Wenmode internals as a third party. Do not import Wenmode's private
  modules from tests; observe only `parse_markdown` output.
- Run gates sequentially, logging to `/tmp/<action>-syrupy-mdast-<branch>.out`.
  Never use `/tmp` as a build target. Do not commit a failing candidate.

## Tolerances (exception triggers)

The comparison base is the merge base with `origin/main` (currently `16f99f4`).
ExecPlan files under `docs/execplans/` are excluded from every count, including
this file. Counting commands:

```bash
base=$(git merge-base HEAD origin/main)
git diff --numstat "$base" -- . ':(exclude)docs/execplans/**' \
  | awk '{print $1-$2, $3}'
git diff --name-only "$base" -- . ':(exclude)docs/execplans/**' | wc -l
```

Classification is by purpose with a whole-file rule:

- Code: Python under `tests/`, and Gherkin `.feature` files under
  `tests/features/`. Limit: 1,700 net lines (additions minus deletions).
- Fixture data: `tests/fixtures/wenmode_decisions/*.json`. These are test
  artefacts and therefore code by purpose, but pretty-printed JSON trees
  inflate line counts, so they carry a separate limit of 700 net lines that
  does not share capacity with the Python limit.
- Configuration: `pyproject.toml`, `Makefile`, `.github/**`, and other
  declarative settings. Limit: 20 net lines. The expected value is zero.
- Documentation: Markdown outside `docs/execplans/`, including
  `tests/fixtures/**/README.md`. Limit: 400 net lines.
- Files: at most 22 changed non-ExecPlan files.

Each category is enforced independently; spare capacity in one category never
offsets another.

Budget evidence. The surveyed estimate is: support module about 250 lines,
strategies module about 200, catalogue integrity tests about 220, conformance
tests about 220, two property modules about 350 together, BDD steps about 200,
feature file about 60, and about 10 lines of rename ripple: roughly 1,500
Python and Gherkin lines. About 20 probes at 15 to 25 lines each give roughly
450 fixture lines. Documentation is roughly 60 lines for the ADR addendum, 30
for the design document, 90 for the developers' guide, 60 for the two fixture
READMEs, and 5 for roadmap and contents: about 250 lines. Historical
comparison: 1.2.2 started at 16 files and 900 net lines, overran to 19 files
and 1,596 lines because its verification suite was under-counted, and was
raised to 24 files and 2,400 lines (finishing at 21 files and 1,755 lines).
1.1.3 stopped at 813 lines against a 600-line cap, which the maintainer waived
without a replacement. Both overruns were missed scope in verification code,
not approved growth, so these budgets price the verification suite explicitly
and keep roughly 13% to 55% contingency per category. 1.2.1 set no numeric
budgets.

Other triggers:

- Interface: any change to `syrupy_mdast/` or to `syrupy_mdast.__all__` stops
  work.
- Dependencies: any new dependency or changed pin stops work.
- Architecture: a need to canonicalize, to edit corpus goldens, or to amend
  ADR-004 beyond the D2 addendum text stops work.
- Decision drift: if any probe or corpus case disagrees with the ADR-004
  decision it pins under Wenmode 0.15.2, other than the known NF-3 label
  wording in D2, stop and record the evidence. Do not "fix" the expectation to
  match the parser.
- Iterations: if the same gate failure survives three targeted fixes, stop and
  reassess rather than weakening an assertion.
- Time: if a single milestone exceeds one working day of active effort, record
  progress and reassess scope.
- Ambiguity: if a ratified clause admits two readings that lead to different
  expected trees, stop and present both readings.

## Risks

- Risk: strict whole-tree equality in probes fails on a Wenmode change that
  does not touch a ratified decision (for example, a new member on paragraphs).
  Severity: medium. Likelihood: medium. Mitigation: this is deliberate
  fail-closed behaviour for a beta parser whose output is the snapshot format.
  The failure message names the probe's decision and the first differing path,
  so the ADR-003 upgrade report (roadmap 3.2.1) can classify the change.
- Risk: Hypothesis grammars generate Markdown that triggers unrelated syntax
  (emphasis, autolinks, entities) and makes properties flaky or vacuous.
  Severity: medium. Likelihood: medium. Mitigation: restrict alphabets to ASCII
  letters and digits for labels and to `[a-z0-9/]` for destinations, avoid
  punctuation in titles, record `hypothesis.event()` classes, and pin witness
  documents with `@example`.
- Risk: label case folding differs across Python Unicode databases (ADR-004
  "Interpreter Unicode data"). Severity: low. Likelihood: low. Mitigation: all
  generated and probe labels are ASCII.
- Risk: the user or maintainer rejects the D2 addendum text. Severity: medium.
  Likelihood: low. Mitigation: EP-M1 commits only the addendum, so the plan
  blocks before any fixture is written.
- Risk: the evidence-version tripwire (`wenmode_evidence_version`) causes
  friction on every upgrade. Severity: low. Likelihood: high on upgrade.
  Mitigation: this matches the existing corpus manifest tripwire
  (`tests/support/markdown_contract_loading.py` lines 183-185) and the ADR-003
  requirement for a dedicated upgrade pull request.
- Risk: pytest-xdist distributes parametrized probe cases across workers.
  Severity: low. Likelihood: high. Mitigation: every probe is independent and
  the seam builds a fresh parser per call (1.2.2), so ordering cannot matter.
- Risk: the 30-second per-test timeout (`pyproject.toml` `timeout = 30`) is hit
  by property tests. Severity: low. Likelihood: low. Mitigation: documents are
  tiny; use `max_examples=100` and `deadline=None`, matching
  `tests/test_wenmode_adapter_properties.py`.

## Progress

- [x] (2026-11-16 10:40Z) Branch renamed to
  `1-2-3-prove-wenmodes-normative-ast-decisions`; Lody session titled.
- [x] (2026-11-16 11:30Z) Reconnaissance by a Wyvern team: ADR decisions,
  seam and test infrastructure, historical ExecPlan budgets, gates.
- [x] (2026-11-16 11:45Z) Raw Wenmode 0.15.2 probing, corpus subset analysis,
  and an upgrade drill against 0.15.3 and 1.0.0rc1 (see Surprises).
- [x] (2026-11-16 12:30Z) Initial draft written.
- [ ] Expert-panel design review applied.
- [ ] Plan approved by the user.
- [ ] `EP-M1` ADR-004 addendum and design wording accepted and committed.
- [ ] `EP-M2` decision catalogue loader, strict comparison, and integrity
  tests.
- [ ] `EP-M3` probe catalogue content and conformance against the parser and
  the corpus subset.
- [ ] `EP-M4` generated-input invariants with Hypothesis.
- [ ] `EP-M5` behavioural contract scenarios with pytest-bdd.
- [ ] `EP-M6` upgrade drill evidence, documentation, roadmap closure.

## Surprises & discoveries

- Observation: ADR-004 NF-3 says footnote `identifier` and `label` are "both
  case-folded by Wenmode". Wenmode 0.15.2 case-folds only `identifier`. The
  `label` carries the source spelling of the first matching definition, and
  every reference repeats it. Evidence: `x[^f]\n\n[^F]: n\n` yields
  `{"type": "footnoteReference", "identifier": "f", "label": "F"}` and a
  definition with the same members; `x[^a]\n\n[^A]: one\n[^a]: two\n` gives the
  reference and first definition `label: "A"` and the second definition
  `label: "a"`. The ADR probe only tested a lower-case definition, so it could
  not see this. Impact: the ratified *payload* is unchanged (the corpus case
  `footnote-case-upper` already matches), but the ADR text is wrong. D2
  proposes a dated correction before fixtures are committed.
- Observation: 84 of the 94 Markdown corpus cases strictly equal raw Wenmode
  0.15.2 output (key order aside). Every one of the 48 cases tagged NF-2 to
  NF-7 matches, and 17 corpus relation groups lie wholly inside that subset.
  Evidence: a scratch comparison script under `/tmp/probe-123/` using `tomllib`,
  `json`, and `parse_markdown`. Impact: the corpus subset can be run against
  the parser now, with no canonicalizer, which D3 adopts.
- Observation: of the 10 non-matching cases, 9 differ only through
  canonicalization rules (`normalize-line-endings`, `merge-plain-text`), but
  `list-loose` (NF-10) is a genuine mismatch. Wenmode gives the second item of
  `- a\n\n- b\n` `"spread": false`, while the golden says `true`. Evidence: raw
  output above. Impact: outside the four 1.2.3 areas. It is recorded for
  roadmap 2.1.1, which owns corpus conformance for NF-10. This plan neither
  fixes nor excludes it (see D8).
- Observation: Wenmode 0.15.3 (2026-10-19) and 1.0.0rc1 (2026-10-21) exist on
  PyPI. Run against the corpus, 0.15.3 matches 0.15.2 exactly. 1.0.0rc1 keeps
  all 48 NF-2 to NF-7 cases but changes NF-13: `&#xD800;` and `&#x110000;` now
  become U+FFFD instead of staying literal. Evidence:
  `uv run --no-project --with wenmode==1.0.0rc1 python -I -W error ...`.
  Impact: a real upstream change already exists that the corpus detects. It is
  outside 1.2.3's areas, but it is useful evidence for the 3.2.1 upgrade report
  and for the drill in EP-M6.
- Observation: further decision-relevant behaviours that ADR-004 does not
  state explicitly but which follow from its clauses. The first ordinary
  definition wins (`[a]: /u\n[a]: /v\n\n[a]\n` gives url `/u`). Duplicate
  footnote definitions are all retained in source order. An explicitly empty
  title is the string `""` and differs from an absent title. An empty image alt
  is `"alt": ""`. Tag-name case does not affect filtering (`<IFRAME>` is
  escaped and `<SCRIPT>x</SCRIPT>` as a type-1 block is not). `<noframes>`,
  `<noembed>`, `<xmp>`, and `<plaintext>` are filtered. An ordinary reference
  inside a footnote body resolves. A definition inside a block quote leaves
  `{"type": "blockquote", "children": []}`. Impact: D2 records the first six as
  clarifications so they can be pinned. The empty block quote stays an
  unratified observation and is not pinned (D9).
- Observation: the CodeGraph MCP server failed to connect in this session
  (connection timeout), so reconnaissance used file reads and `grep`. Impact:
  none on the plan; implementers should retry CodeGraph first.

## Decision log

- D1. Decision: the four roadmap areas map to ADR-004 NF-2 (references), NF-3
  (footnotes), NF-4 and NF-5 (nullable members and `null` array elements), and
  NF-6 and NF-7 (raw HTML). NF-5 is included because "omitted nullable fields"
  is only meaningful against the one place where `null` *is* preserved.
  Rationale: the roadmap names areas, not identifiers; NF-1, NF-8 to NF-13 stay
  with roadmap 2.1.x. Date/Author: 2026-11-16, planning agent.
- D2. Decision: propose a dated ADR-004 addendum, appended after the existing
  2026-10-30 addendum, which corrects NF-3's label wording and records the
  clarifications and the location of the lasting probes. ADR-004's
  `### Amendments` section permits corrections to the v1 payload definition as
  dated amendments before the first payload-writing release, and no such
  release exists (`serialize()` still raises `NotImplementedError`). The
  correction is payload-neutral: the corpus already encodes the observed
  behaviour. Proposed text, to be committed verbatim in EP-M1 after approval:

  ```markdown
  ## Addendum (2026-11-16): footnote labels and lasting decision probes

  This addendum corrects one clause of NF-3, records clarifications that follow
  from NF-2 to NF-7, and names the lasting executable evidence for those
  decisions. It does not change the v1 payload definition: the canonical
  corpus already encodes the behaviour described here, and every other
  statement above continues to apply.

  - NF-3 correction. Wenmode case-folds a footnote `identifier`, but not its
    `label`. A `footnoteDefinition` keeps its own source spelling as `label`,
    and every `footnoteReference` that resolves to it repeats the first
    matching definition's `identifier` and `label`. References spelled `[^F]`
    and `[^f]` are therefore equal when they resolve to the same definition,
    while changing the definition's spelling, as in `[^F]:` versus `[^f]:`,
    is distinct.
  - NF-2 clarification. When several definitions share a label, the first
    definition in source order wins, as CommonMark specifies.
  - NF-3 clarification. Duplicate footnote definitions are all retained in
    source order; each keeps its own `label`.
  - NF-4 clarification. An explicitly empty title (`[x](/u "")`) is the empty
    string, which is distinct from an absent `title`. An image's `alt` is
    always present, and may be empty.
  - NF-6 and NF-7 clarification. Tag-name case does not affect filtering.
    `<noembed>` and `<noframes>` are filtered alongside `<title>`,
    `<iframe>`, `<xmp>`, and `<plaintext>`; type-1 `<script>`, `<style>`,
    and `<textarea>` blocks remain unfiltered whatever their case.
  - Lasting evidence. `tests/fixtures/wenmode_decisions/probes.json` and the
    `tests/test_wenmode_normative_decision*.py` suites are the executable form
    of the `### Evidence` probe for NF-2 to NF-7. They run on every `make
    test`, together with the corpus cases tagged with those rules. The inline
    probe remains the historical ratification record.
  ```

  Rationale: a probe suite that pinned the observed label behaviour against an
  ADR that says otherwise would leave two contradictory sources of truth. The
  strongest alternative, writing a superseding ADR, is reserved by ADR-004 for
  payload-definition changes after release, so it is disproportionate here.
  Approving authority: the user (maintainer), as part of plan approval.
  Date/Author: 2026-11-16, planning agent (proposed).
- D3. Decision: two complementary oracles. First, run the existing corpus
  cases tagged NF-2 to NF-7 that carry no canonicalization-transformation rule
  (48 cases) through `parse_markdown`, and compare them strictly with their
  canonical goldens. Second, add a small focused probe catalogue for the
  clauses the corpus does not exercise. Rationale: for these cases, the
  canonical form differs from raw output only in member order, which strict
  JSON equality ignores. Reusing the reviewed corpus avoids duplicating about
  48 golden trees, and the selection rule is declarative (by manifest `rules`).
  The rejected alternative, a probe for every clause duplicating corpus trees,
  would double the fixture budget and create two goldens per behaviour.
  Date/Author: 2026-11-16, planning agent.
- D4. Decision: the probe catalogue is one strict JSON file,
  `tests/fixtures/wenmode_decisions/probes.json`. It holds a decision-clause
  registry, with each clause's ADR anchor, statement, probe IDs, and corpus
  case IDs, followed by probe records. Rationale: `AGENTS.md` asks that large
  blocks of test data live in external files. JSON matches the corpus goldens
  and can reuse `read_expected_payload`'s duplicate-key and scalar checks. A
  separate catalogue keeps the corpus canonical-only (its README defines it as
  canonical expected JSON), so raw-parser probes do not blur that definition.
  Date/Author: 2026-11-16, planning agent.
- D5. Decision: promote `_strict_json_equal` in
  `tests/support/markdown_contract.py` to the public name `strict_json_equal`,
  updating every caller in the same commit, with no alias. Python `==` treats
  `True == 1` and `False == 0`, so `"checked": false` versus `"checked": 0`
  would pass a plain comparison. Rationale: a sweep found that this is the only
  strict comparator in the repository, and duplicating it would be the
  "duplicated code" smell. It is a test-only API, so no compatibility shim is
  warranted. Date/Author: 2026-11-16, planning agent.
- D6. Decision: no Syrupy snapshot files. Rationale: the oracle must be
  independent, hand-authored, and reviewed. A Syrupy snapshot of parser output
  would be generated by the system under test and could be "accepted" with
  `--snapshot-update`, laundering exactly the upgrade change this task must
  catch. The project's own Markdown extension cannot serialize yet (roadmap
  2.3.1). The multivariant format-consistency concern is met by strict
  structural equality plus corpus relation groups. Date/Author: 2026-11-16,
  planning agent.
- D7. Decision: no Rust extension, Verus or Kani proof, or CrossHair run.
  Rationale: this task introduces no repository-owned business logic or axiom
  of its own. The obligations are claims about a third-party parser, which the
  ExecPlan rules treat as axioms to observe at the boundary, not internals to
  verify. A Verus proof would have to assume Wenmode's behaviour and then
  restate it, which the user's own guidance forbids. The repository-owned logic
  (strict comparison, catalogue validation, corpus selection) is small and
  fully covered by parametrized tests and a Hypothesis property; CrossHair
  would add no reachable-path evidence beyond that. Date/Author: 2026-11-16,
  planning agent.
- D8. Decision: leave `list-loose` and the 1.0.0rc1 NF-13 change out of scope
  and record them for 2.1.1 and 3.2.1. The corpus selection rule excludes
  NF-10-only and NF-13 cases by construction. Rationale: the roadmap scopes
  1.2.3 to four areas, and correcting a golden needs its own review under
  ADR-004. Date/Author: 2026-11-16, planning agent.
- D9. Decision: do not pin the empty `blockquote` left by a definition inside a
  block quote. Rationale: it is a consequence of NF-2 that no ADR clause
  addresses, and pinning it would ratify a shape by stealth. It is recorded in
  Surprises for the 2.1.1 author. Date/Author: 2026-11-16, planning agent.
- D10. Decision: Red-Green-Refactor applies as follows. For repository-owned
  support code (loader, strict comparison, selection, difference reporting),
  write the failing tests first in the usual way. For parser characterization,
  author each expected tree from the ADR text *before* running it, then run it.
  A mismatch is evaluated against the ADR, never silently copied, as happened
  with NF-3 during planning. Then prove sensitivity with seeded-fault controls
  that must fail. Rationale: the production code does not change, so a
  conventional red stage for parser behaviour would be theatre. Date/Author:
  2026-11-16, planning agent.
- D11. Decision: the catalogue records `wenmode_evidence_version = "0.15.2"`,
  and a test requires it to equal the installed Wenmode version. Rationale: it
  forces a deliberate review of the decision evidence in the ADR-003 upgrade
  pull request, matching the corpus manifest's existing tripwire. Date/Author:
  2026-11-16, planning agent.

## Outcomes & retrospective

Not started. To be completed at each milestone and at completion, including
reconciliation of every discovery with ADR-004, ADR-003, and the design
document before the status becomes `COMPLETE`.

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
in the package calls it yet. Skylos keeps it alive through a typed entrypoint
rule (`pyproject.toml` lines 436-444), and Skylos excludes `tests/`, so new
test helpers need no Skylos entries. Tests may patch the module's `Parser` and
`github` names to observe the seam; 1.2.2's `tests/support/wenmode_adapter.py`
(`RecordingAdapter`) does this.

Raw Wenmode 0.15.2 output facts used by this plan, all observed directly:
member order is `type`, `children`, then other members; `None`-valued members
are omitted; `link` and `image` carry `url`, optional `title`, and `alt` for
images, but never `identifier` or `label`; footnote nodes carry `identifier` and
`label`; filtered HTML is
`{"type": "html", "data": {"escaped": true}, "value": "&lt;iframe ..."}`, with
each disallowed tag's leading `<` replaced by `&lt;`.

The canonical Markdown contract corpus lives in
`tests/fixtures/markdown_contract/`. `manifest.toml` has `corpus_version = 1`,
`contract_version = 1`, and `wenmode_evidence_version = "0.15.2"`, then 101
`[[cases]]`. Each case has `id`, `rules` (NF IDs and transformation IDs),
`reason`, `witness`, `kind` (`markdown` or `synthetic`), `input`
(`sources/*.txt`), `expected` (`expected/*.json`), and `line_endings`. The 36
`[[relations]]` records have `id`, `relation` (`equal` or `distinct`), and
`cases`. Expected file names do not match case IDs, so always resolve through
the manifest. Loader: `tests/support/markdown_contract_loading.py`
(`load_corpus(root) -> ContractCorpus`). Model and helpers:
`tests/support/markdown_contract.py` (`CaseRecord`, `RelationRecord`,
`ContractCorpus`, `read_source`, `read_expected_payload`, `_strict_json_equal`,
`JSONValue`, `RULE_IDS`). Integrity tests: `tests/test_markdown_contract.py` and
`tests/test_markdown_contract_loading.py`.

Existing Wenmode tests from 1.2.1 and 1.2.2 are as follows.
`tests/test_wenmode_adapter.py` holds unit tests with recording doubles.
`tests/test_wenmode_adapter_bdd.py` with
`tests/features/wenmode_adapter.feature` follows the pattern
`scenarios(str(_FEATURE))`, a `scenario_state` dict fixture, and steps in the
same module. `tests/test_wenmode_adapter_properties.py` shows the Hypothesis
style: an `st.composite` strategy, `event()`,
`@settings(max_examples=50, deadline=None)`, and `@example`.
`tests/test_wenmode_adapter_concurrency.py` and
`tests/test_wenmode_adapter_workers.py` complete the set. The installed-wheel
probe in `tests/support/wenmode_runtime_probe.py` defines the installation
contract and must not be extended here.

Gates (`Makefile`): `make check-fmt` (Ruff format check and
`mdtablefix --check`), `make typecheck` (`ty check syrupy_mdast tests`),
`make lint` (Ruff, `interrogate --fail-under 100`, two Pylint passes,
`ambrleaks tests`, Skylos), `make test` (`pytest -v -n auto`),
`make markdownlint`, `make nixie`, and `make fmt` to apply formatting.
`make all` omits `markdownlint` and `nixie`, so run them explicitly for
documentation changes.

Budget survey (feeds `Tolerances`): existing comparable modules are
`tests/support/wenmode_adapter.py` (354 lines),
`tests/support/markdown_contract.py` (335), `tests/test_wenmode_adapter_bdd.py`
(169), `tests/test_wenmode_adapter_properties.py` (117), and
`tests/test_markdown_contract.py` (398). Historical ExecPlans: 1.2.2 raised its
budget from 16 files and 900 lines to 24 files and 2,400 lines after a
verification-suite under-estimate. 1.1.3 waived a 600-line cap at 813 lines.
1.2.1 had no numeric budget.

Documentation to read before implementing: `AGENTS.md`;
`docs/syrupy-mdast-design.md` sections 7, 8, and 11;
`docs/adrs/adr-0004-parser-profile-and-normalization.md` (NF-2 to NF-7,
`### Evidence`, `### Amendments`);
`docs/adrs/adr-0003-snapshot-version-policy.md` ("Wenmode upgrade workflow");
`docs/adrs/adr-0005-exact-wenmode-runtime-dependency.md`;
`docs/developers-guide.md` (corpus workflow, "Upgrade Wenmode", "Verify the
internal Wenmode seam");
`docs/complexity-antipatterns-and-refactoring-strategies.md`;
`docs/documentation-style-guide.md`; `.rules/python-00.md`,
`.rules/python-typing.md`, `.rules/python-return.md`,
`.rules/python-exception-design-raising-handling-and-logging.md`, and
`.rules/python-generators.md`; and `tests/fixtures/markdown_contract/README.md`.

Skills to load: `execplans` (this plan), `python-router` routing to
`python-testing` (parametrization, pytest-bdd), `hypothesis` (EP-M4 strategies),
`python-data-shapes` (frozen dataclasses for catalogue records),
`python-types-and-apis` (`JSONValue` typing), and `python-errors-and-logging`
(loader errors). Also load `python-verification` (to confirm that CrossHair and
mutmut are not warranted), `codegraph-mcp` (retry; it was unavailable during
planning), `leta` (navigation), `en-gb-oxendict-style` (prose),
`commit-message`, and `pr-creation`. Use the `scrutineer` agent to run full
gates.

## Conformance basis

Upstream artefacts and revisions (all at `16f99f4`):

- Technical design: `docs/syrupy-mdast-design.md` section 7 (parser profile and
  seam), section 8 (canonicalization contract and the reference, footnote, and
  HTML paragraphs), section 11 (Table 3 rows "Reference semantics", "Footnote
  structure", and "Preservation"; "Parser conformance remains Wenmode's
  responsibility").
- ADR-004 (accepted 2026-10-11, addendum 2026-10-30): NF-2, NF-3, NF-4, NF-5,
  NF-6, and NF-7; `### Evidence`; `### Amendments`; Migration plan step 2 ("Add
  the lasting contract corpus and parser probes, with each fixture linked to an
  NF identifier").
- ADR-003: "Wenmode upgrade workflow" (each entry that can affect
  GitHub-profile `to_ast()` output receives a fixture).
- ADR-005: exact pin `wenmode==0.15.2`.
- Roadmap: `docs/roadmap.md` item 1.2.3 (requires 1.2.2, which is complete).
- No Terms of Reference document exists for this project.

Derived requirements:

- `REQ-REF`: resolved ordinary references (NF-2) are pinned by executable
  evidence covering full, collapsed, shortcut, forward, case-insensitive,
  first-wins, unresolved, unused, and image forms.
- `REQ-FN`: structural footnotes (NF-3, as corrected by D2) are pinned,
  covering node members, label provenance, order, unused, repeated, undefined,
  and duplicate definitions.
- `REQ-NULL`: omitted nullable members (NF-4) and preserved `null` alignment
  elements (NF-5) are pinned, including the absent-versus-empty-string
  distinction.
- `REQ-HTML`: raw HTML (NF-6) and the type-1 divergence (NF-7) are pinned for
  every GitHub-disallowed tag, both cases of tag name, block and inline
  positions, and allowed tags.
- `REQ-FAIL`: a parser change to any pinned decision makes `make test` fail
  with a message naming the decision clause.
- `REQ-SEAM`: the evidence runs through `syrupy_mdast._wenmode.parse_markdown`,
  not a direct Wenmode call.
- `REQ-ORACLE`: expectations are hand-authored, reviewed data and are never
  regenerated by the tests.

Observed gaps:

- `GAP-NO-RUNNER`: no test executes the parser against NF-2 to NF-7 (the ADR
  probe is prose; the corpus is integrity-only).
- `GAP-NF3-TEXT`: ADR-004 NF-3 misdescribes label case folding.
- `GAP-UNPINNED`: NF-7's `<xmp>` and `<plaintext>` claims, `<noembed>`,
  `<noframes>`, tag-name case, first-wins, duplicate footnote definitions, and
  empty-title behaviour have no fixture.

Trace links:

```plaintext
ADR-004 NF-3 -> GAP-NF3-TEXT -> D2 -> EP-M1 -> ADR-004 addendum (2026-11-16)
ADR-004 NF-2 -> REQ-REF -> EP-M3/EP-M4 -> test_probe_matches_ratified_decision, test_corpus_case_matches_raw_parse, test_reference_forms_resolve_identically
ADR-004 NF-3 -> REQ-FN -> EP-M3/EP-M4 -> test_probe_matches_ratified_decision, test_footnotes_stay_structural
ADR-004 NF-4/NF-5 -> REQ-NULL -> EP-M3/EP-M4 -> test_probe_matches_ratified_decision, test_nullable_members_are_omitted
ADR-004 NF-6/NF-7 -> REQ-HTML -> EP-M3/EP-M4 -> test_probe_matches_ratified_decision, test_disallowed_html_is_escaped
Roadmap 1.2.3 success -> REQ-FAIL -> EP-M2/EP-M3/EP-M5 -> test_seeded_decision_change_is_reported, wenmode_normative_decisions.feature
Design §7 seam -> REQ-SEAM -> EP-M3 -> test_probes_observe_the_internal_seam
Design §8 / ADR-004 Migration step 2 -> REQ-ORACLE -> EP-M2 -> catalogue integrity tests
ADR-003 upgrade workflow -> D11 -> EP-M2/EP-M6 -> test_evidence_version_matches_installed_wenmode, upgrade drill transcript
```

## Verification plan

### Abstract model

Let `P` be `parse_markdown`, mapping a Markdown string to a JSON value: a
`dict[str, JSONValue]` root. Let `≡` be strict JSON equality. Two mappings are
equal when they have the same member set and each member's values are strictly
equal. Two lists are equal when they have the same length and their elements
are pairwise strictly equal. Scalars are equal when their types are identical
and their values are equal, so `True` is not equal to `1`. Member order is
ignored.

A decision clause `c` (for example, `NF-4.omitted`) is a predicate over pairs
`(source, P(source))`. The catalogue gives finite witnesses `(s, e)` with the
claim `P(s) ≡ e`, plus corpus witnesses `(s, g)` with `P(s) ≡ g` for the
selected subset. The Hypothesis properties state universally quantified clauses
over generated sources from small grammars. Malformed catalogue data is a
loader error (`ValueError` or `TypeError` with the file location), never a
skipped probe. A parser exception is a test failure, because every probe source
is valid Markdown.

### Invariants and lemmas

- `INV-REF` (REQ-REF): for every source in the reference grammar `G_ref`, `P`
  contains no node of type `definition`, `linkReference`, or `imageReference`,
  and no `link` or `image` node has `identifier`, `label`, or `referenceType`.
  For a label `L`, destination `u`, optional title `t`, and text `x`, the
  direct form `[x](u "t")` and the full forms `[x][L']` with `[L]: u "t"`,
  placed before or after use, are strictly equal, where `L'` is any ASCII case
  variant of `L`. When `x = L`, the collapsed and shortcut forms are also
  strictly equal. An undefined label yields a single `text` node equal to the
  source line. Method: Hypothesis property plus catalogue and corpus witnesses.
- `INV-FN` (REQ-FN): for every source in the footnote grammar `G_fn` (distinct
  ASCII labels, case-varied references, definitions before or after, extra
  unused definitions), each `footnoteReference` and `footnoteDefinition` has
  exactly the member set `{type, identifier, label}`, plus `children` for
  definitions. `identifier == label.lower()` holds for definitions. Every
  reference's `identifier` and `label` equal those of the definition it
  resolves to. The number of `footnoteReference` nodes equals the number of
  resolved reference occurrences. Definitions appear at their source positions
  in source order. Unused definitions are present. Undefined references are
  literal text. Method: Hypothesis property plus witnesses.
- `INV-NULL` (REQ-NULL): for every source in the nullable grammar `G_null`
  (links and images with and without titles, fences with and without info
  strings, bullet and ordered lists, task and plain items, and tables with
  random alignments), no mapping member anywhere has the value `None`. `None`
  occurs only as an element of a `table.align` list, and exactly where the
  delimiter row has no colon. `title` is present if and only if the source gave
  one (an empty-string title is present as `""`). `lang` is present if and only
  if there is an info string, and `meta` if and only if the info string has a
  second word. `checked` is present if and only if the item has a task marker.
  `start` is present if and only if the list is ordered. Method: Hypothesis
  property plus witnesses.
- `INV-HTML` (REQ-HTML): for a tag `T` drawn from GitHub's nine disallowed tags
  together with a sample of allowed tags (`div`, `span`, `p`, `em`), a random
  ASCII case spelling, and a position (inline in a paragraph, or block start),
  each `html` node `n` produced for `T` is escaped exactly when `T.lower()` is
  disallowed and the construct is not a type-1 block, meaning `script`,
  `style`, or `textarea` at block start. "Escaped" means
  `n["data"] == {"escaped": True}` strictly, and `n["value"]` equals the source
  fragment with the leading `<` of each disallowed tag replaced by `&lt;`. A
  non-escaped node has no `data` member and its `value` equals the source
  fragment. Method: Hypothesis property over the finite tag × case × position
  space, plus witnesses.
- `INV-SEAM` (REQ-SEAM): the conformance tests' observations change when the
  seam's `Parser` is replaced, so they observe `parse_markdown`. Method: a
  seeded-fault control.
- `L-STRICT` (supports REQ-FAIL): `strict_json_equal(a, a)` holds for every
  JSON value `a`. For every single-site mutation `m`,
  `strict_json_equal(m(a), a)` is false. The mutations are: add a member
  (including a `None`-valued one), delete a member, replace a scalar with a
  different value or with an equal value of a different type (`True` and `1`,
  `False` and `0`), insert, delete, or swap list elements with distinct values,
  and rename a member. This lemma links "the parser changed a pinned member" to
  "the test fails". Method: Hypothesis property over generated JSON trees.
- `L-DIFF` (supports REQ-FAIL): `first_difference(actual, expected)` returns
  `None` if and only if `strict_json_equal(actual, expected)` holds. Otherwise
  it returns the path of a position at which the two values differ. Method: the
  same Hypothesis property as `L-STRICT`, plus named examples.
- `L-SELECT` (supports REQ-REF to REQ-HTML): the corpus selection returns
  exactly the Markdown cases whose `rules` intersect `{NF-2, …, NF-7}` and
  contain none of `remove-position`, `remove-empty-data`, `merge-plain-text`,
  `normalize-line-endings`, or `order-members`. It returns 48 cases, and every
  NF identifier from NF-2 to NF-7 appears among them. Method: a named assertion
  with the expected count and per-rule membership, guarding against silent
  shrinkage.
- `L-COVER` (supports REQ-FAIL and REQ-ORACLE): every registered clause has at
  least one catalogue probe or selected corpus case. Every probe names at least
  one registered clause. Every corpus case ID named by a clause exists and is
  selected. Probe IDs are unique. Method: catalogue integrity tests.

### Axioms (trusted, not verified here)

- `AXIOM-DETERMINISM`: Wenmode is deterministic for a given source, version,
  and interpreter (Wenmode documentation; 1.2.2 evidence). Depends: every probe.
- `AXIOM-SEAM`: `parse_markdown` is the v1 construction
  `Parser(github(), positions=False).parse(source).to_ast()`. This is verified
  by 1.2.2's tests, not here.
- `AXIOM-PIN`: the installed Wenmode is 0.15.2. This is verified by
  `tests/test_package_manifest_contract.py` and by D11's tripwire.
- `AXIOM-GFM-TAGFILTER`: the GFM specification's disallowed list is `title`,
  `textarea`, `style`, `xmp`, `iframe`, `noembed`, `noframes`, `script`, and
  `plaintext`, and filtering replaces the leading `<` with `&lt;` (GFM
  specification, section 6.11, "Disallowed Raw HTML (extension)"). It is used
  only to choose the tag set for `INV-HTML`. Wenmode's observed behaviour, not
  the specification, is the oracle (NF-7).
- `AXIOM-ASCII-CASEFOLD`: for ASCII labels, CommonMark label normalization
  equals Python's `str.lower()`. This avoids Unicode-database variation.
- `AXIOM-HYPOTHESIS`: Hypothesis explores the declared strategies and reports
  failures faithfully. Its database and shrinking do not affect soundness.

### Methods, artefacts, commands, and discharge

| Obligation           | Method                                   | Artefact                                                                                        | Discharged when                                                               |
| -------------------- | ---------------------------------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `INV-REF`            | Hypothesis + witnesses                   | `tests/test_wenmode_normative_decision_properties.py::test_reference_forms_resolve_identically` | passes with ≥100 examples and events for every form                           |
| `INV-FN`             | Hypothesis + witnesses                   | same module, `test_footnotes_stay_structural`                                                   | passes; events show forward, backward, unused, and case-varied cases          |
| `INV-NULL`           | Hypothesis + witnesses                   | `tests/test_wenmode_normative_decision_shapes.py::test_nullable_members_are_omitted`            | passes; events show every optional member both present and absent             |
| `INV-HTML`           | Hypothesis over finite space + witnesses | same module, `test_disallowed_html_is_escaped`                                                  | passes; events cover all nine disallowed tags, both cases, and both positions |
| `INV-SEAM`           | seeded-fault control                     | `tests/test_wenmode_normative_decisions.py::test_probes_observe_the_internal_seam`              | the control fails when `Parser` is replaced with a mutating double            |
| `L-STRICT`, `L-DIFF` | Hypothesis over JSON trees               | `tests/test_wenmode_decision_catalogue.py::test_single_mutations_are_detected`                  | passes; events cover every mutation kind                                      |
| `L-SELECT`           | named assertion                          | `tests/test_wenmode_normative_decisions.py::test_corpus_selection_covers_every_decision`        | equals 48 and covers NF-2 to NF-7                                             |
| `L-COVER`            | integrity tests                          | `tests/test_wenmode_decision_catalogue.py`                                                      | all pass; unhappy-path loader tests raise                                     |
| REQ-FAIL             | BDD + named controls                     | `tests/features/wenmode_normative_decisions.feature`                                            | negative scenarios report the named clause                                    |

*Table 1: Verification obligations, methods, and discharge conditions.*

Focused command for every obligation:

```bash
uv run pytest -v -n 2 \
  tests/test_wenmode_decision_catalogue.py \
  tests/test_wenmode_normative_decisions.py \
  tests/test_wenmode_normative_decision_properties.py \
  tests/test_wenmode_normative_decision_shapes.py \
  tests/test_wenmode_normative_decisions_bdd.py \
  --hypothesis-show-statistics 2>&1 | tee /tmp/test-syrupy-mdast-1-2-3-focused.out
```

### Non-vacuity

- `INV-REF` to `INV-HTML`: each property carries `@example` witnesses for every
  equivalence class named in its invariant, and records `hypothesis.event()`
  labels such as `form=collapsed`, `definition=after`, `title=absent`,
  `tag=xmp`, `case=upper`, and `position=block`. The EP-M4 acceptance requires
  `--hypothesis-show-statistics` output showing every label. Strategies build
  valid inputs constructively, without `assume()` or `.filter()`, so there is
  no rejection; any "invalid" count above 5% is investigated (1.2.2 recorded
  about 5% overrun-only invalids). Each property also has a seeded-fault
  control. A test patches `syrupy_mdast._wenmode.Parser` with a double whose
  `to_ast()` applies the clause's characteristic regression, such as keeping a
  `definition` node, lower-casing `label`, adding `"title": None`, or dropping
  `data`, and asserts that the property's check function rejects the result for
  the intended clause.
- `L-STRICT` and `L-DIFF`: the mutation property asserts detection for each
  mutation kind separately, and events show that every kind occurred. Named
  examples pin `True` against `1`, `False` against `0`, a `None`-valued added
  member, and swapped list elements, the cases plain `==` misses or that matter
  most.
- Probe and corpus conformance: before parser runs, every expected tree is
  authored from ADR text (D10). After the green run, a parametrized control
  feeds each probe's expected tree through one decision-relevant mutation and
  requires `decision_mismatch` to report the probe's clause. A mutation that is
  not detected fails the control, so a probe that pins nothing cannot pass.
- `INV-SEAM`: the control must fail, not error, with the mutating double in
  place, and must pass without it.
- `L-SELECT`: the exact count 48 and the per-rule check stop a manifest or
  selection change from silently emptying the suite.
- Upgrade drill (EP-M6): running the suite in a scratch environment with
  Wenmode 1.0.0rc1 must show the evidence-version tripwire failing and all
  four-area probes passing. Running the whole corpus comparison script there
  must show the NF-13 differences. Together these show the mechanism detects
  real upstream changes, not only synthetic ones.

### Residual gaps

Finite probes and bounded grammars cannot prove universal parser stability
(ADR-004 "Beta parser behaviour"). Non-ASCII labels, nested containers, and
pathological inputs are outside the generated grammars. Raw output is compared
before canonicalization, so canonical payload outcomes remain roadmap 2.1.2's
obligation.

## Behavioural specification and contract scenarios

These are contract scenarios for the internal parser seam, written in
behaviour-driven development (BDD) form (`Feature`, `Scenario`, `Given`, `When`,
`Then`). Like `tests/features/wenmode_adapter.feature`, they are not
acceptance tests of the public package. They make the ratified decisions
readable to reviewers and exercise the failure-reporting path.

Path: `tests/features/wenmode_normative_decisions.feature`, bound by
`tests/test_wenmode_normative_decisions_bdd.py` (EP-M5; REQ-REF, REQ-FN,
REQ-NULL, REQ-HTML, and REQ-FAIL).

```gherkin
Feature: Wenmode's ratified GitHub-profile AST decisions
  The snapshot contract relies on four parser decisions from ADR-004. These
  scenarios parse decision probes through the internal Wenmode seam.

  Scenario Outline: Ordinary reference forms resolve to the same link
    Given the decision probe "<probe>"
    When the probe is parsed through the internal Wenmode seam
    Then the tree holds one link to "/u" titled "t"
    And the tree holds no definition, reference, identifier, or label member

    Examples:
      | probe                      |
      | reference-direct-titled    |
      | reference-full-titled      |
      | reference-collapsed-titled |
      | reference-shortcut-titled  |
      | reference-forward-titled   |

  Scenario: An unresolved reference stays literal text
    Given the decision probe "reference-unresolved-image"
    When the probe is parsed through the internal Wenmode seam
    Then the tree holds no link or image node
    And the paragraph text equals the probe source line

  Scenario: Footnote labels keep the definition's spelling
    Given the decision probe "footnote-label-from-definition"
    When the probe is parsed through the internal Wenmode seam
    Then every footnote node has identifier "note" and label "Note"

  Scenario: Absent optional members are not synthesized
    Given the decision probe "nullable-members-mixed"
    When the probe is parsed through the internal Wenmode seam
    Then no member anywhere in the tree is null
    And the table alignment keeps its null element

  Scenario: Disallowed raw HTML is escaped and marked
    Given the decision probe "html-inline-disallowed"
    When the probe is parsed through the internal Wenmode seam
    Then every html node for a disallowed tag is marked escaped
    And no html node for an allowed tag carries data

  Scenario: Type-1 script blocks are kept as observed
    Given the decision probe "html-type1-uppercase-script"
    When the probe is parsed through the internal Wenmode seam
    Then the tree is one unescaped html node equal to the source

  Scenario Outline: A parser change to a ratified decision is reported
    Given a parser double that <regression>
    When the decision probe "<probe>" is checked
    Then the check fails naming decision "<clause>"

    Examples:
      | regression                          | probe                          | clause              |
      | synthesizes a null title on links   | link-title-absent-forward      | NF-4.omitted        |
      | keeps ordinary definition nodes     | reference-full-titled          | NF-2.resolve        |
      | case-folds footnote labels          | footnote-label-from-definition | NF-3.label-spelling |
      | drops the escaped data marker       | html-inline-disallowed         | NF-6.escaped        |
```

The catalogue's probe IDs above are illustrative of the EP-M3 catalogue and
must be kept in sync with it. If EP-M3 renames a probe, update this section in
the same commit.

## Milestones and plateaus

### EP-M1: ADR addendum and design wording (documentation only)

Assigned: `GAP-NF3-TEXT`, D2. Append the D2 addendum verbatim to
`docs/adrs/adr-0004-parser-profile-and-normalization.md`. In
`docs/syrupy-mdast-design.md` section 8, amend the footnote paragraph to say
identifiers are case-folded while labels keep the definition's spelling, citing
ADR-004's 2026-11-16 addendum. End state: the ratified text matches observed
behaviour before any fixture exists, satisfying design section 11's rule that
the ADR is accepted before fixture changes. Acceptance: `make fmt`,
`make markdownlint`, and `make nixie` pass. Conformance check: the addendum
changes no payload; corpus goldens are untouched. Recovery: revert the single
commit. Remaining gaps: all executable evidence.

### EP-M2: catalogue model, strict comparison, and integrity tests

Assigned: `L-STRICT`, `L-DIFF`, `L-COVER`, REQ-ORACLE, D4, D5, D11.

Red. Write `tests/test_wenmode_decision_catalogue.py` first. It covers loading
a valid miniature catalogue written to `tmp_path`. Unhappy paths must raise
with a location in the message: a duplicate probe ID, an unknown clause, a
clause with no evidence, a corpus case that does not exist or is not selected,
a probe with no clause, a duplicate JSON member, a float scalar, a non-string
source, and an expected value whose root is not `type: root`. A separate
`test_evidence_version_matches_installed_wenmode` compares the catalogue's
`wenmode_evidence_version` with `importlib.metadata.version("wenmode")`; the
loader itself does not, so that the upgrade drill can show probes passing while
only the tripwire fails. Further tests check `strict_json_equal` on `True`/`1`,
`False`/`0`, and `None` members; `first_difference` paths on named examples;
and the `L-STRICT`/`L-DIFF` mutation property. Run them; they fail with
`ModuleNotFoundError` for `tests.support.wenmode_decisions` (the expected red).

Green. Rename `_strict_json_equal` to `strict_json_equal` in
`tests/support/markdown_contract.py` and update its callers
(`grep -rn _strict_json_equal tests`). Create
`tests/support/wenmode_decisions.py` with:

- frozen, slotted dataclasses `DecisionClause`, `DecisionProbe`, and
  `DecisionCatalogue`;
- `load_decision_catalogue`, which decodes with `read_expected_payload`
  (strict duplicate and scalar checks) and validates every `L-COVER` rule;
- `select_decision_corpus_cases`, which implements `L-SELECT`;
- `first_difference`, which returns the first differing path or `None`;
- `decision_mismatch`, which formats the failure message shown in `Purpose`;
- `null_member_paths`, which skips elements of `align` lists.

The exact signatures are in `Interfaces and dependencies`.

Create `tests/fixtures/wenmode_decisions/probes.json` holding only the header
and clause registry, with every clause's evidence pointing at selected corpus
cases, so that integrity passes before probes exist. Create
`tests/fixtures/wenmode_decisions/README.md`, which explains the schema, the
hand-authoring rule, and how to add a probe. Keep functions small (Ruff
complexity 8 or less) and the module at 400 lines or fewer.

Refactor. Then run the focused tests and the four gates. End state: a
validated, parser-free catalogue model. Recovery: revert the milestone's
commits; nothing depends on them yet.

### EP-M3: probe content and parser conformance

Assigned: REQ-REF, REQ-FN, REQ-NULL, REQ-HTML, REQ-SEAM, `L-SELECT`,
`GAP-NO-RUNNER`, `GAP-UNPINNED`.

Author the probes in the catalogue from the ADR and addendum text before
running anything (D10). The minimum set is listed below; IDs are stable once
committed.

- NF-2: `reference-direct-titled`, `reference-full-titled`,
  `reference-collapsed-titled`, `reference-shortcut-titled`,
  `reference-forward-titled`, `reference-first-definition-wins`,
  `reference-unresolved-image`, and `reference-in-footnote-body` (also NF-3).
- NF-3: `footnote-label-from-definition` (`x[^note] y[^NOTE]\n\n[^Note]: n\n`),
  `footnote-duplicate-definitions`, and `footnote-repeated-forward-reference`.
- NF-4 and NF-5: `link-title-absent-forward`, `link-title-empty`,
  `image-title-empty-alt-empty`, `code-lang-without-meta`,
  `code-empty-with-lang`, `nullable-members-mixed` (task and plain items, a
  bullet list, and a one-column unaligned table), and `table-align-null-only`.
- NF-6 and NF-7: `html-inline-disallowed` (all nine tags inline, with allowed
  `<span>` between them), `html-block-filtered-uppercase` (`<IFRAME>`),
  `html-block-noframes`, `html-block-noembed`, `html-block-plaintext`,
  `html-type1-uppercase-script`, and `html-inline-allowed-only`.

Point each clause's `probes` at these IDs.

Write `tests/test_wenmode_normative_decisions.py` with these tests:

- `test_probe_matches_ratified_decision`, parametrized over probe IDs, with
  `ids=` set to the probe ID. It asserts `decision_mismatch(...) is None`, and
  the assertion message is the mismatch text.
- `test_corpus_case_matches_raw_parse`, parametrized over the selected corpus
  cases. It reads the source with `read_source` and the golden with
  `read_expected_payload`, then compares strictly.
- `test_corpus_relations_hold_on_raw_parse`. For each relation whose cases
  are all selected (17 today), `equal` groups must parse strictly equal and
  `distinct` groups pairwise unequal.
- `test_corpus_selection_covers_every_decision` (`L-SELECT`).
- `test_probes_observe_the_internal_seam` (`INV-SEAM`). It monkeypatches
  `syrupy_mdast._wenmode.Parser` with a double that delegates to the real
  parser and then adds `"title": None` to every link. It asserts that
  `decision_mismatch` reports `NF-4.omitted` for `link-title-absent-forward`.
- `test_seeded_decision_change_is_reported`, parametrized over
  `(probe, mutation, clause)`, which applies the clause-specific mutation to
  each probe's expected tree.

If any probe disagrees with its authored expectation, apply the "Decision
drift" tolerance. End state: every ratified clause has executable,
parser-backed evidence, and `make test` fails on a decision change. Gates: the
focused command, then `make check-fmt`, `make typecheck`, `make lint`, and
`make test`. Recovery: revert the milestone's commits.

### EP-M4: generated-input invariants

Assigned: `INV-REF`, `INV-FN`, `INV-NULL`, `INV-HTML`.

Create `tests/support/wenmode_decision_strategies.py` with constructive
`st.composite` strategies:

- `reference_documents()` draws a label from ASCII letters and digits (1 to 8
  characters), a case variant, a destination from `/[a-z0-9]{1,8}`, an optional
  title of ASCII letters and spaces with no leading or trailing space, a form,
  and whether the definition comes before or after. It returns the source and
  the expected link fields.
- `footnote_documents()` draws 1 to 3 distinct labels, the spelling of each
  definition, the case variants and order of the references, extra unused
  definitions, and an optional undefined reference. It returns the source and
  an expected model.
- `nullable_documents()` concatenates blocks drawn from links, images, fences,
  lists, items, and tables, each with a model of which optional members must
  appear.
- `html_fragments()` uses `st.sampled_from` over tags × case × position.

Strategies must not use `assume` or `filter`.

Write `tests/test_wenmode_normative_decision_properties.py` (references and
footnotes) and `tests/test_wenmode_normative_decision_shapes.py` (nullable
members and HTML). Each module stays under 400 lines. Use
`@settings(max_examples=100, deadline=None)`, `@example` witnesses per class,
and `event()` labels. Add the per-property seeded-fault controls described in
`Non-vacuity`. End state: universal clauses hold across generated inputs.
Acceptance: the focused command with `--hypothesis-show-statistics` shows every
event label and fewer than 5% invalid examples, then the four gates run.
Recovery: revert the milestone's commits.

### EP-M5: behavioural contract scenarios

Assigned: REQ-FAIL and readable acceptance. Add the feature file from
`Behavioural specification and contract scenarios` and
`tests/test_wenmode_normative_decisions_bdd.py`. Follow the
`tests/test_wenmode_adapter_bdd.py` pattern: `scenarios(str(_FEATURE))`, a
`scenario_state` fixture, and docstrings on every step. Use `parsers.parse` for
quoted arguments. The parser doubles patch `syrupy_mdast._wenmode.Parser` with
`monkeypatch`, never globally. End state: reviewers can read the decisions as
scenarios, and the regression path is exercised. Gates: the focused command,
then the four gates. Recovery: revert.

### EP-M6: upgrade drill, documentation, and closure

Assigned: D11 evidence, documentation obligations, and roadmap closure.

1. Upgrade drill (manual evidence; not CI, because it needs the network and
   several Wenmode versions). In a scratch environment outside the worktree,
   run:

   ```bash
   drill=/tmp/wenmode-drill-1-2-3; rm -rf "$drill"; mkdir -p "$drill"
   uv export --frozen --only-group dev --no-hashes --no-emit-project --no-header \
     -o "$drill/dev.txt"
   echo 'wenmode==1.0.0rc1' > "$drill/override.txt"
   uv venv "$drill/.venv"
   uv pip install --python "$drill/.venv/bin/python" -r "$drill/dev.txt" \
     -e . --override "$drill/override.txt"
   "$drill/.venv/bin/python" -m pytest -p no:cacheprovider -q \
     tests/test_wenmode_decision_catalogue.py \
     tests/test_wenmode_normative_decisions.py 2>&1 | tee /tmp/drill-syrupy-mdast-1-2-3.out
   ```

   Expected: `test_evidence_version_matches_installed_wenmode` fails, naming
   `1.0.0rc1`, and every probe and corpus conformance test passes. Repeat with
   `wenmode==0.15.3`, where the same result is expected. Paste concise
   transcripts into `Outcomes & retrospective`. If `--override` or
   `--only-group` is unsupported by the installed `uv`, record the variant
   used. If the result differs, record it in `Surprises & discoveries` and
   evaluate it under the "Decision drift" tolerance.
2. Documentation, delegating mechanical prose edits to `scribe` where useful:
   - `docs/developers-guide.md`: add a section "Verify Wenmode's normative AST
     decisions" covering the layout, how to add a probe, the strictness rule,
     the corpus selection rule, the focused command, and the drill. Extend
     "Upgrade Wenmode" with a step to run the decision suites and update
     `wenmode_evidence_version` only after the ADR-003 report.
   - `docs/syrupy-mdast-design.md` section 8: replace "they do not run a parser
     or canonicalizer" with an accurate statement that the NF-2 to NF-7 subset
     is also run against raw parser output. In section 11, add a Table 3 row
     "Parser decisions" with the method "Catalogue probes, corpus subset, and
     generated grammars run through the seam" and the boundary "Raw output
     only; finite grammars".
   - `tests/fixtures/markdown_contract/README.md`: replace "It is test data; it
     does not run Wenmode" with wording that names the decision suite as the
     one consumer that runs the NF-2 to NF-7 subset.
   - `docs/contents.md`: index this ExecPlan (done in the planning commit).
   - `docs/users-guide.md`: no change, because there is no behaviour or public
     API change. Record this in `Outcomes & retrospective`.
   - `docs/roadmap.md`: mark 1.2.3 `[x]` and add a one-line "Current
     deliverable" note naming the suites.
3. Run `make fmt`, `make check-fmt`, `make typecheck`, `make lint`,
   `make test`, `make markdownlint`, and `make nixie` sequentially through
   `scrutineer`. Reconcile discoveries with ADR-004, ADR-003, and the design
   document, then set the status to `COMPLETE`.

## Concrete steps and acceptance

Run every gate sequentially from the repository root, with `set -o pipefail`,
and log each one:

```bash
set -o pipefail
branch=$(git branch --show-current)
make check-fmt 2>&1 | tee "/tmp/check-fmt-syrupy-mdast-${branch}.out"
make typecheck 2>&1 | tee "/tmp/typecheck-syrupy-mdast-${branch}.out"
make lint 2>&1 | tee "/tmp/lint-syrupy-mdast-${branch}.out"
make test 2>&1 | tee "/tmp/test-syrupy-mdast-${branch}.out"
make markdownlint 2>&1 | tee "/tmp/markdownlint-syrupy-mdast-${branch}.out"
make nixie 2>&1 | tee "/tmp/nixie-syrupy-mdast-${branch}.out"
```

Expected at completion: every target exits 0. `make test` reports the new
modules, with probe and corpus parametrizations named by ID, for example
`test_corpus_case_matches_raw_parse[footnote-case-upper] PASSED`. Commit after
each milestone with an imperative subject, for example "Pin Wenmode reference
and footnote decisions (1.2.3)".

Acceptance summary:

1. `make test` passes, and the new suites contain at least 20 catalogue probes
   and 48 corpus conformance cases.
2. Each seeded-fault control and each negative BDD scenario fails the check
   for the named clause.
3. The upgrade drill shows the tripwire firing and the decision probes
   behaving as recorded.
4. ADR-004, the design document, the developers' guide, both fixture READMEs,
   and the roadmap are updated as described.

## Idempotence and recovery

All steps are re-runnable. Tests write only to pytest's `tmp_path`. The drill
uses a scratch directory under `/tmp` that is deleted and recreated, and never
modifies `uv.lock`; confirm with `git status --short uv.lock` (no output). Each
milestone is one or more commits that can be reverted independently in reverse
order. EP-M1 must precede fixture commits. If a gate fails, read the cited
`/tmp` log rather than re-running it. Re-run only after a fix.

## Interfaces and dependencies

No production interface changes. The test-support interface introduced in
`tests/support/wenmode_decisions.py` is:

```python
@dataclasses.dataclass(frozen=True, slots=True)
class DecisionClause:
    id: str                       # for example "NF-4.omitted"
    adr_clause: str               # for example "NF-4"
    statement: str
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
    wenmode_evidence_version: str
    clauses: tuple[DecisionClause, ...]
    probes: tuple[DecisionProbe, ...]

def load_decision_catalogue(path: Path, *, corpus: ContractCorpus) -> DecisionCatalogue: ...
def select_decision_corpus_cases(corpus: ContractCorpus) -> tuple[CaseRecord, ...]: ...
def first_difference(actual: JSONValue, expected: JSONValue, path: str = "root") -> str | None: ...
def decision_mismatch(probe_id: str, clauses: tuple[str, ...], actual: JSONValue, expected: JSONValue) -> str | None: ...
def null_member_paths(tree: JSONValue) -> tuple[str, ...]: ...
```

Its scope and re-use policy: it is test-only, and owns raw-parser decision
evidence. Roadmap 2.1.1 may reuse `select_decision_corpus_cases` and
`first_difference` for wider corpus conformance. Canonicalization must not be
added here. The developers' guide records this policy (EP-M6).

The catalogue schema (`tests/fixtures/wenmode_decisions/probes.json`) is:

```json
{
  "catalogue_version": 1,
  "contract_version": 1,
  "wenmode_evidence_version": "0.15.2",
  "clauses": [
    {
      "id": "NF-4.omitted",
      "adr_clause": "NF-4",
      "statement": "Absent title, lang, meta, checked, and start stay absent; no null member is synthesized.",
      "probes": ["link-title-absent-forward", "nullable-members-mixed"],
      "corpus_cases": ["link-title-absent", "image-title-absent", "code-indented-omissions"]
    }
  ],
  "probes": [
    {
      "id": "link-title-absent-forward",
      "clauses": ["NF-4.omitted", "NF-2.resolve"],
      "reason": "A forward reference without a title resolves to a link with no title member.",
      "source": "[x]\n\n[x]: /u\n",
      "expected": {
        "type": "root",
        "children": [
          {
            "type": "paragraph",
            "children": [
              {"type": "link", "url": "/u", "children": [{"type": "text", "value": "x"}]}
            ]
          }
        ]
      }
    }
  ]
}
```

The initial clause registry is: `NF-2.resolve`, `NF-2.casefold`,
`NF-2.first-wins`, `NF-2.unused`, `NF-2.literal`, `NF-2.image`,
`NF-3.structural`, `NF-3.label-spelling`, `NF-3.order`, `NF-3.unused`,
`NF-3.repeat`, `NF-3.literal`, `NF-3.duplicate`, `NF-4.omitted`,
`NF-4.empty-string`, `NF-5.align-null`, `NF-6.escaped`, `NF-6.allowed`,
`NF-6.case`, and `NF-7.type-1`. A new clause requires an ADR-004 statement or
addendum to cite.

Dependencies: none added. Uses `pytest`, `pytest-bdd`, `hypothesis`, and the
standard-library `json`, `tomllib`, `dataclasses`, and `importlib.metadata`.

## Artefacts and external references

- GFM specification, section 6.11 "Disallowed Raw HTML (extension)":
  <https://github.github.com/gfm/#disallowed-raw-html-extension->, retrieved
  2026-11-16. It lists `title`, `textarea`, `style`, `xmp`, `iframe`, `noembed`,
  `noframes`, `script`, and `plaintext`, filtered by replacing the leading `<`
  with `&lt;`.
- mdast specification: <https://github.com/syntax-tree/mdast>, retrieved
  2026-11-16. The `Association` mixin has `identifier` and an optional `label`;
  the `Resource` mixin has `url` and an optional `title`; `ListItem.spread`
  reports whether an item's own children are separated by a blank line.
- Wenmode release history: <https://pypi.org/pypi/wenmode/json>, retrieved
  2026-11-16. It lists 0.15.2 (2026-10-01), 0.15.3 (2026-10-19), and 1.0.0rc1
  (2026-10-21).
- Planning scratch scripts (not committed) are in `/tmp/probe-123/`: `probe.py`,
  `corpus.py`, `sel.py`, `fn.py`, `more.py`, and `last.py`, plus `*_sa.py`
  variants for the standalone drill.
