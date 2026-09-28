# Record the parser-profile and snapshot-version policy in an ADR

This ExecPlan (execution plan) is a living document. The sections `Constraints`,
`Tolerances`, `Risks`, `Progress`, `Surprises & discoveries`, `Decision log`,
`Outcomes & retrospective`, `Conformance basis`, and `Verification plan` must
be kept up to date as work proceeds.

Status: DRAFT

## Purpose / big picture

`syrupy-mdast` will compare Markdown by its parsed structure rather than its
source text. What counts as "the same document" is therefore a persisted
contract: every `.mdast.json` snapshot a user commits encodes one parser
release, one parser profile, one normalization policy, one key order, and one
JSON spelling. If any of those drifts silently, users' snapshots churn with no
explanation, or, worse, a real change stops being detected.

The technical design names that contract but leaves its load-bearing values
open. No Wenmode release is chosen; the snapshot-format version is described
only as "follows semantic versioning"; the exact key order is deferred to "an
immutable constant"; and several Wenmode behaviours the design ratifies were
never observed against a real release. Design §11 requires "an explicitly
versioned ADR" recording the complete contract, "accepted before committing any
related implementation or fixture change".

After this work a maintainer or contributor can open one document,
`docs/adr-003-parser-profile-and-snapshot-version-policy.md`, and read:

1. the snapshot contract version (`1`) and the rules that decide when it, and
   the package version, must change;
2. the exact Wenmode release (`0.15.1`), the exact parser construction
   `Parser(github(), positions=False)`, and why;
3. the normalization policy, including the rule order and the exact key-order
   sequence, and the exact JSON writer settings;
4. the comparison contract: what compares equal and what does not;
5. the snapshot-version policy: how payload changes map to package releases,
   what users see, and how Wenmode upgrades are reviewed and kept out of
   automatic dependency updates; and
6. the normative fixture decisions (NF-1 to NF-13) that roadmap task 1.1.3 turns
   into a corpus and task 1.2.3 turns into committed Wenmode probes, each
   backed by a self-checking probe script that anyone can re-run with one
   command.

A machine-readable manifest inside the ADR is guarded by a documentation
contract test, so the ADR, the technical design, the existing extension's
`file_extension`, and the JSON examples in the design cannot disagree without
failing `make test`. Later roadmap tasks extend the same test to their code
constants (the roadmap edits in DEC-3 make that a success criterion).

The work lands in two pull requests because this repository squash-merges
(DEC-13). Pull request A carries this ExecPlan and ADR-003, and merges only
after the maintainer accepts the ADR. Pull request B, branched from `main`
after A merges, carries the guard test and the reconciliation of the design,
roadmap, and guides. On `main`, therefore, the accepted ADR provably precedes
every dependent change.

Observable success, after pull request B:

```bash
uv run pytest -v tests/test_snapshot_contract_adr.py
```

Expected: every test passes, including
`test_exactly_one_contract_adr_is_accepted`,
`test_design_parser_construction_matches_manifest`, and
`test_design_json_examples_are_writer_fixed_points`. Temporarily editing the
design's §7 code block back to the deprecated `Parser(github, positions=False)`
makes `test_design_parser_construction_matches_manifest` fail with a message
naming the design, the offending line, and the manifest value.

This task deliberately delivers **no** production code, no Wenmode dependency,
no corpus fixtures, and no snapshots. Those belong to roadmap tasks 1.1.3,
1.2.1-1.2.3, and phase 2.

## Constraints

These are hard invariants. Violating one requires escalation, not a workaround.

1. Nothing under `syrupy_mdast/` changes. This task records a contract; it does
   not implement one. The guard test may import
   `syrupy_mdast.MarkdownAstSnapshotExtension` read-only.
2. `wenmode` is not added to `pyproject.toml`, `uv.lock`, or any dependency
   group; that is roadmap task 1.2.1. Wenmode probes run only in a throwaway
   environment under `/tmp` via `uv run --no-project --with wenmode==0.15.1`.
3. No corpus fixture, `.mdast.json` file, or `__snapshots__` directory is
   created; that is roadmap task 1.1.3.
4. No new runtime or development dependency. The guard test uses only the
   standard library, `pytest`, and the package itself.
5. ADR-003 follows the template in `docs/documentation-style-guide.md`
   §"Architectural decision records (ADRs)" verbatim in heading names and
   order, including the template's `## Decision Drivers` capitalization (the
   1.1.1 ExecPlan's DEC-13 handoff; see DEC-16).
6. The implementer never accepts the ADR on the maintainer's behalf. Acceptance
   is an explicit maintainer comment or review on pull request A stating that
   ADR-003 is accepted. A pull-request approval without that statement does not
   count. Approval of this ExecPlan approves the plan and the answers to the
   questions in DEC-19; it is not acceptance of the ADR text.
7. Pull request B is created only after pull request A has merged. No commit
   containing the guard test, design reconciliation, roadmap edits (other than
   the lint fix in commit `6cfb4f7`), or guide text is pushed to pull request A.
8. The package remains Python-only (design §2.3, §13). No Rust extension, Bun,
   Node.js, or JavaScript asset is introduced, including for verification.
9. Prose is en-GB-oxendict, wrapped at 80 columns; code blocks wrap at 120.
   Every new test module, function, class, and helper carries a docstring
   (`interrogate --fail-under 100` covers `tests/`).
10. Every milestone ends with `make check-fmt`, `make typecheck`, `make lint`,
    `make test`, `make markdownlint`, and `make nixie` passing, run
    sequentially and never in parallel. Prefer delegating the full run to the
    `scrutineer` agent, which captures each gate's log under `/tmp`.

## Tolerances (exception triggers)

Stop, record the situation in `Decision log`, set `Status: BLOCKED`, and
escalate when any of these is reached.

1. Scope: more than 12 files touched across both pull requests, or any file
   under `syrupy_mdast/`.
2. Wenmode release drift: PyPI publishes a Wenmode release newer than 0.15.1
   before ADR-003 is accepted. Re-run the probe against the new release, record
   the differences, and ask the maintainer which release to pin. Do not
   silently switch. Re-check at EP-M1, at every acceptance re-ping, and
   immediately before the acceptance commit.
3. Evidence drift: the self-checking probe (see `Artefacts and notes`) prints
   anything other than the thirteen `ok` lines and `version 0.15.1` shown in
   `Concrete steps` when run against 0.15.1 with `-W error`.
4. Acceptance: the maintainer requests a change to any decision in
   `Decision log`. Revise this plan first, then the ADR.
5. Roadmap: this plan authorizes exactly the roadmap edits listed in DEC-3. Any
   further roadmap amendment triggers escalation.
6. Dependencies: any need for a new package, including `pytest-bdd` or
   `packaging` as a declared dependency, triggers escalation.
7. Iterations: a single gate still failing after three remediation attempts.
8. Ambiguity: a design passage that conflicts with the ADR in a way not already
   resolved in `Decision log`.
9. Stall: no maintainer response to the acceptance request after seven days.
   Re-ping once, re-check Tolerance 2, and record the date. After a second
   seven days, escalate in the session.

## Risks

1. Risk: Wenmode is beta software; a later release changes AST output for
   inputs outside the corpus, so an apparently payload-neutral pin move changes
   users' payloads. Severity: high. Likelihood: medium, since 0.15.1, a patch
   release, changed list tightness and autolink boundaries. Mitigation: DEC-9
   requires changelog-entry classification as well as the corpus diff, a
   fixture for every behaviour-changing entry, and a dedicated pull request.
2. Risk: Dependabot silently upgrades Wenmode. Its pip group batches every
   minor and patch update, the repository's Dependabot automerge workflow
   merges green batches (`docs/developers-guide.md` §"CodeScene coverage
   publication"), and `tests/test_dependabot_config_contract.py` forbids
   `exclude-patterns`, so the obvious remedy fails the suite. Severity: high.
   Likelihood: high once Wenmode is a dependency. Mitigation: DEC-9 names the
   mechanism, a Dependabot `ignore` entry for `wenmode`, which the contract
   test does not constrain; roadmap 1.2.1 implements it and extends the
   contract test to require it (DEC-3).
3. Risk: the ratified behaviour includes a Wenmode divergence from the GFM
   specification (Surprise 5, NF-7). A future Wenmode fix changes payloads.
   Severity: medium. Likelihood: medium. Mitigation: NF-7 freezes the observed
   behaviour and classifies an upstream fix as a payload change. No upstream
   report is filed: the maintainer judged the divergence irrelevant to the
   implementation (DEC-19, answer 3).
4. Risk: formatter ping-pong. `.mdast.json` invites JSON formatters (Prettier,
   Biome, the `pretty-format-json` pre-commit hook, which sorts keys) to
   rewrite snapshots, after which every assertion fails and every update is
   reverted. Severity: medium. Likelihood: medium. Mitigation: the ADR records
   strict text comparison as the v1 decision with this risk named; the users'
   guide gains a one-paragraph exclusion recipe.
5. Risk: on-disk line terminators. Syrupy 5.0.0 and 6.0.0 both open
   single-file snapshots in text mode without a `newline` argument (Surprise
   8), so snapshots written on Windows contain CRLF, and CI runs only on
   Ubuntu. Severity: medium. Likelihood: medium. Mitigation: DEC-10 requires
   the on-disk line ending to be decided (recommendation: LF) before the first
   release in which `serialize()` writes payloads; the roadmap 2.3.1 edit in
   DEC-3 carries the obligation.
6. Risk: Python's Unicode database differs between Python 3.12, 3.13, and 3.14
   (and PyPy). Wenmode's case folding of labels and its punctuation
   classification for emphasis flanking can depend on it, so one package
   version may emit different payloads on different interpreters for exotic
   input. Severity: low. Likelihood: low. Mitigation: axiom A6 and an ADR
   known-risk entry; adding a supported Python minor version triggers the DEC-9
   upgrade report.
7. Risk: the exact Wenmode pin conflicts with downstream projects that also
   depend on Wenmode, and a Wenmode security fix can then only reach users
   through a syrupy-mdast release. Severity: medium. Likelihood: low.
   Mitigation: DEC-9's security path; the users' guide recommends installing
   syrupy-mdast in a test-only dependency group.
8. Risk: a future Wenmode warning (it signals API changes with
   `DeprecationWarning`) becomes an error in user suites that run with
   `filterwarnings = error`. Severity: low. Likelihood: medium. Mitigation: the
   probe runs with `-W error`; DEC-9 makes any new warning from the v1
   construction an upgrade blocker.
9. Risk: the guard test becomes a brittle Markdown scraper. Severity: medium.
   Likelihood: medium. Mitigation: it parses only one fenced `toml` block under
   a fixed heading, the `## Status` paragraph, fenced `python` and `json`
   blocks in an explicit allowlist of documents, and link targets; it asserts
   parsed semantics, never wording or line numbers.

## Progress

- [x] (2026-09-27) Branch renamed to
  `1-1-2-record-parser-and-snapshot-version-policy`, tracking origin.
- [x] (2026-09-27) Reconnaissance (two Wyvern agents): repository, test
  conventions, documentation conventions, and the 1.1.1 handoff obligations.
- [x] (2026-09-27) External research: Wenmode 0.15.1 release, presets,
  security, compatibility, node model, and changelog; GFM tag filter; Syrupy
  5.0.0 and 6.0.0 single-file I/O and amber versioning.
- [x] (2026-09-27) Empirical probe of Wenmode 0.15.1's GitHub profile, later
  made self-checking (thirteen NF checks, key coverage over all 22 node types,
  `-W error`).
- [x] (2026-09-27) Pre-existing `make markdownlint` failure on `main` fixed in
  its own commit `6cfb4f7` (Surprise 11).
- [x] (2026-09-27) ExecPlan drafted (commit `6ad7108`).
- [x] (2026-09-27) Expert-panel design review (four agents, six lenses); plan
  revised (DEC-18).
- [x] (2026-09-28) Maintainer answered DEC-19: merge plain text nodes (yes),
  no payload version marker (yes), no upstream report (no).
- [ ] Maintainer approval of this ExecPlan.
- [ ] EP-M1: ADR-003 drafted as `Proposed` and indexed (pull request A).
- [ ] EP-M2: ADR-003 accepted; pull request A merged.
- [ ] EP-M3: guard tests red, then design, roadmap, and guides reconciled
  (pull request B).
- [ ] EP-M4: full gate sweep, roadmap tick, retrospective.

## Surprises & discoveries

1. Observation: the design's parser construction is deprecated. Evidence:
   Wenmode 0.15.0 changed `commonmark`, `github`, and `streaming` into preset
   factory functions; `Parser(github, positions=False)` emits
   `DeprecationWarning: Passing github without calling it is deprecated and
   will be removed in 1.0; use github() instead.`
   Impact: the ADR fixes `Parser(github(), positions=False)`; design §7 and
   roadmap tasks 1.2.2 and 2.1.1 are amended (DEC-3, DEC-5).
2. Observation: Wenmode preserves CR and CRLF inside string values. Evidence:
   `"a\r\nb\r\n"` yields a text node `"a\r\nb"`; a CRLF fenced code block yields
   `"x\r\n"`; a CRLF link title is kept. Structure (paragraph splits, hard
   breaks) is identical across LF, CRLF, and CR. Impact: design §8 rule 3 is
   load-bearing, not defensive.
3. Observation: `null` appears inside arrays. Evidence: a table with an
   unaligned column yields `"align": [null, "center"]`. Wenmode omits
   `None`-valued *members* but keeps `None` array *elements*. Impact: the ADR
   says so (NF-5); the JSON value domain includes `null`.
4. Observation: entity references and backslash escapes split text nodes.
   Evidence: `"&amp; &copy;"` yields `"&"`, `" "`, `"©"`; `"\\*x\\*"` yields
   `"*"`, `"x"`, `"*"`; `"a & b"` yields one node. Impact: without a merge rule,
   `a & b` and `a &amp; b` are distinct payloads (DEC-7).
5. Observation: Wenmode's GitHub tag filter skips CommonMark type-1 HTML blocks
   whose tag is on the disallowed list (`<script>`, `<style>`, `<textarea>`),
   although GFM spec 0.29-gfm §6.11 applies the filter to raw HTML blocks too.
   Evidence: those blocks are emitted unchanged with no `data`; `<iframe>` and
   `<title>` blocks and inline `<script>`, `<xmp>`, and `<plaintext>` are
   rewritten to a leading `&lt;` with `data: {"escaped": true}`. Impact: NF-7.
6. Observation: footnote definitions stay at their source position, unused
   definitions are retained, undefined references stay literal text, repeated
   references repeat, and labels are case-folded (`[^F]` yields `identifier` and
   `label` `"f"`). Impact: NF-3.
7. Observation: Wenmode exports no documented parse exception; `dir(wenmode)`
   holds only `StreamingUnsupportedError`. Impact: design §9's `parse` category
   may have no documented Wenmode trigger. Handoff to roadmap 2.2.2.
8. Observation: Syrupy 5.0.0 and 6.0.0 write single-file text snapshots with
   `open(path, "wt", encoding=...)` and no `newline` argument, and read with
   universal newlines. Evidence: `syrupy/extensions/single_file.py`
   (`write_snapshot_collection`, `read_snapshot_data_from_location`) in both
   releases. Impact: comparisons survive CRLF on disk, but bytes on disk are
   platform-dependent (Risk 5, DEC-10).
9. Observation: Syrupy's amber serializer writes `# serializer version: 1` and
   marks mismatched snapshots tainted; `assertion.py` computes
   `matches = not tainted and …`, so a tainted snapshot fails even when its
   content is identical. `SingleFileSnapshotExtension` has no header and no
   taint source. Impact: informs DEC-8 option D.
10. Observation: `docs/repository-layout.md`, cited by `AGENTS.md`, does not
    exist, and no component architecture document exists. Impact: DEC-15.
11. Observation: `origin/main` failed `make markdownlint` (MD053) because
    ticking task 1.1.1 left `[issue-23]` unused at the end of
    `docs/roadmap.md`; `make fmt` deletes the definition but leaves two blank
    lines (MD012), so the formatter could not repair it. Resolution: removed in
    its own commit, `6cfb4f7`, before any other roadmap edit.
12. Observation: rule order matters if text nodes are merged. Evidence:
    `a&#13;\nb` yields adjacent text nodes `"a"`, `"\r"`, `"\nb"`. Merging then
    normalizing gives `"a\nb"`; normalizing then merging gives `"a\n\nb"`.
    Impact: DEC-6 fixes merge before line-ending normalization; handoff lemma
    for roadmap 2.1.2.
13. Observation: Wenmode never emits lone surrogates from numeric character
    references: `&#0;` becomes U+FFFD, and `&#xD800;` and `&#x110000;` stay
    literal text. Impact: NF-13; the JSON value domain can require Unicode
    scalar values without rejecting any Wenmode output observed so far.
14. Observation: with `ensure_ascii=False`, CPython's `json` escapes `"`, `\`,
    and U+0000 to U+001F (as `\n`, `\t`, `\b`, `\f`, `\r`, or lowercase
    `\u00xx`), and emits everything else literally, including U+007F, C1
    controls, U+2028, U+2029, and bidirectional controls. Impact: DEC-10
    records the escape set; DEC-17 keeps it.
15. Observation: this repository squash-merges pull requests (every `main`
    subject ends `(#NN)`; no merge commits). Impact: branch-local commit order
    cannot prove "accepted before" on `main`; DEC-13.

## Decision log

- DEC-1. Decision: the ADR is
  `docs/adr-003-parser-profile-and-snapshot-version-policy.md`, titled
  "Architectural decision record (ADR) 003: Snapshot contract v1 — parser
  profile and snapshot-version policy". Rationale: next free sequence number;
  the style guide's naming pattern. Date/Author: 2026-09-27, planning agent.
- DEC-2. Decision: "explicitly versioned" means an integer **snapshot contract
  version**, starting at `1`, in a machine-readable manifest inside the ADR,
  alongside the style guide's `Status` and `Date`. Until the first release whose
  `serialize()` writes payloads, contract v1 may be corrected in place by
  dated entries under `### Amendments` (a subsection of
  `## Decision outcome / proposed direction`, so the template is kept), because
  no user holds a v1 snapshot yet. After that release, changes that cannot
  alter any payload (editorial clarifications, a Wenmode pin move classified as
  payload-neutral under DEC-9) are dated amendments, with `## Date` meaning
  "last updated"; any change to the definition of the payload is a new contract
  version in a new ADR, and the old ADR's status becomes
  `Superseded (YYYY-MM-DD) by ADR-NNN.` Rationale: accepted ADRs are records;
  superseding keeps each contract version citable, while the pre-release window
  lets roadmap 1.1.3 and 1.2.3 correct v1 without ceremony. Date/Author:
  2026-09-27, planning agent, revised after panel review.
- DEC-3. Decision: pull request B makes exactly these roadmap edits:
  1. 1.1.2 ticked done;
  2. 1.2.1 gains two success sub-bullets: a Dependabot `ignore` entry for
     `wenmode`, required by `tests/test_dependabot_config_contract.py`; and the
     `pyproject.toml` pin equals the ADR manifest's `wenmode`, enforced by
     `tests/test_snapshot_contract_adr.py` (which then rejects an absent
     declaration);
  3. 1.2.2 constructs `Parser(github(), positions=False)`, and the adapter's
     construction equals the manifest's `parser`;
  4. 2.1.1 wording changes to `Parser(github(), positions=False)`;
  5. 2.1.2's key-order constant and rule sequence equal the manifest's
     `key-order` and `normalization`, enforced by the guard test;
  6. 2.2.1's writer settings equal the manifest's `json-writer` table, and the
     payload is checked to encode as strict UTF-8 before it reaches Syrupy; and
  7. 2.3.1 decides the on-disk line ending before the first release that writes
     payloads.
  Rationale: the old wording prescribes a deprecated call (Surprise 1), and
  developers'-guide prose alone does not hold later tasks to the manifest.
  Date/Author: 2026-09-27, planning agent, widened after panel review.
- DEC-4. Decision: pin Wenmode 0.15.1. Rationale: latest release (2026-09-11).
  0.15.0 introduced the preset factories the ADR relies on, and 0.15.1 fixes
  list tightness and extended-autolink boundaries, so pinning 0.15.0 would
  schedule a known payload migration. Waiting for Wenmode 1.0 would block the
  roadmap on an undated upstream release; 1.0 is instead a DEC-9 upgrade
  trigger and a likely contract v2. Licence BSD-3-Clause; pure-Python
  `py3-none-any` wheel; requires Python 3.10 or later. Wheel SHA-256
  `d25b2adc75ff897640c1e28178f647631da0e03084e498a765f007844a3c340d`.
  Date/Author: 2026-09-27, planning agent.
- DEC-5. Decision: the v1 parser construction is exactly
  `Parser(github(), positions=False).parse(source).to_ast()`, with a fresh
  `Parser` per call, no plugins, no `create_preset`, and no rule registration.
  It must emit no warnings. This supersedes the construction in design §7.
  Rationale: Surprise 1; the per-call rule is unchanged from design §3 and §10.
  Date/Author: 2026-09-27, planning agent.
- DEC-6. Decision: the normalization policy is an ordered sequence of rules,
  applied recursively to every mapping and list at every depth, including inside
  `data`:
  1. `remove-position` — delete every member named `position`;
  2. `remove-empty-data` — delete a `data` member whose value is an empty
     mapping;
  3. `merge-plain-text` — replace each run of adjacent sibling nodes whose
     members are exactly `type` (equal to `"text"`) and `value` with one such
     node whose `value` is the concatenation (DEC-7);
  4. `normalize-line-endings` — replace CRLF, then bare CR, with LF in every
     string value (not in member names);
  5. `order-members` — emit members in the manifest's `key-order`, then the
     remaining members ordered by Unicode code point (Python's default `str`
     ordering, which is not JavaScript's UTF-16 ordering), so unknown members
     follow `children`.
  The 17-element `key-order` is `type`, `depth`, `ordered`, `start`, `spread`,
  `checked`, `align`, `lang`, `meta`, `url`, `title`, `alt`, `identifier`,
  `label`, `value`, `data`, `children`. Rationale: design §8's grouping (type,
  structural scalars, link and footnote fields, value, data, children); the
  probe shows these 17 names cover every member Wenmode emits across all 22
  GitHub-profile node types (NF-12); rule 3 must precede rule 4 (Surprise 12).
  Date/Author: 2026-09-27, planning agent, revised after panel review.
- DEC-7. Decision (accepted by the maintainer on 2026-09-28, DEC-19): adopt
  `merge-plain-text`, so `a & b` and `a &amp; b`, and `a*b` and `a\*b`, compare
  equal. Rationale: `mdast-util-from-markdown` merges adjacent text data, so
  splitting is a Wenmode tokenization artefact rather than mdast structure;
  where Wenmode splits text is exactly the edge-case behaviour its
  compatibility page reserves the right to change, so merging insulates
  snapshots from that churn; the narrow rule (exact member set, siblings only)
  cannot equate nodes that render differently; and adding the rule later would
  be a contract change touching every snapshot with an entity or escape. The
  alternative (retain segmentation) is the more literal reading of design §8's
  "only these transformations" and is recorded as rejected ADR option F.
  Date/Author: 2026-09-27, planning agent, reversed after panel review;
  confirmed by the maintainer 2026-09-28.
- DEC-8. Decision (accepted by the maintainer on 2026-09-28, DEC-19): the
  payload carries no version marker and the suffix stays `.mdast.json`. Payload
  changes surface as ordinary Syrupy diffs of the affected snapshots, explained
  by release notes; the users' guide maps package versions to contract
  versions. Options considered in the ADR: A (no marker, chosen), B (in-payload
  member), C (versioned suffix), D (amber-style header with taint, which fails
  even identical snapshots), and E (an informational marker that comparison
  ignores, as insta treats its metadata header). Adding any marker later is
  itself a payload change. Rationale: design §8's payload is the canonical tree
  alone, and B to D force every snapshot to change at every bump, which is the
  broad-update noise design §1 exists to remove. Date/Author: 2026-09-27,
  planning agent, option E added after panel review; confirmed by the
  maintainer 2026-09-28.
- DEC-9. Decision: the snapshot-version policy is keyed on **any change to any
  payload**, whatever its cause: contract change, canonicalizer conformance
  fix, or non-neutral Wenmode move.
  1. Patch releases never knowingly change a payload.
  2. A payload change needs, before 1.0.0, a minor release (`0.y.z` to
     `0.(y+1).0`); from 1.0.0, a major release. Its release notes list the
     affected constructs and the review-then-`pytest --snapshot-update` step.
  3. The contract version increments when the *definition* of the payload
     changes (parser profile, normalization rules, key order, writer); it is a
     migration signal, not the equivalence key (DEC-14).
  4. Every Wenmode pin change lands alone in a dedicated pull request carrying
     the roadmap 3.2.1 upgrade report. That report classifies the corpus diff
     and every Wenmode changelog entry between the two releases as an
     addition, parser fix, intentional migration, or regression (the 3.2.1
     categories), and adds a fixture for every entry that can affect the GitHub
     profile's `to_ast()` output. The move is payload-neutral only if the
     corpus diff is empty and every such entry is fixture-covered with no
     change. The move is blocked if the v1 construction emits any warning under
     `-W error`.
  5. Dependabot never proposes Wenmode updates: `.github/dependabot.yml` gains
     `ignore: [{dependency-name: "wenmode"}]` in the pip block (roadmap 1.2.1).
  6. Triggers for an upgrade evaluation: a new Wenmode release, Wenmode 1.0,
     a Wenmode security advisory, and adding a supported Python minor version.
     A security advisory ships promptly, versioned by rule 2, naming the
     advisory in the release notes.
  Rationale: design §13, with the pre-1.0 case explicit (the package is
  `0.1.0`), the Dependabot automerge path closed (Risk 2), and Risk 1 bounded.
  This overrides two clauses of design §13 (see `Conformance basis`).
  Date/Author: 2026-09-27, planning agent, rewritten after panel review.
- DEC-10. Decision: the canonical JSON writer for contract v1 is specified as
  settings, not as a code string: UTF-8, no byte-order mark,
  `ensure_ascii = false`, `indent = 2`, separators `","` and `": "`,
  `allow_nan = false`, `sort_keys = false` (rule 5 already ordered the
  members), one trailing LF. The reference realization is
  `json.dumps(tree, ensure_ascii=False, indent=2, separators=(",", ": "),
  allow_nan=False) + "\n"`,
  whose escape set is recorded in the ADR (Surprise 14). The value domain is
  mappings with string keys, lists, strings of Unicode scalar values, integers,
  booleans, and `null`; validators check `bool` before `int`; anything else is
  an `ast-shape` failure (design §9). The payload must encode as strict UTF-8
  before it is handed to Syrupy, so a failure never truncates a snapshot file.
  The contract governs the string handed to Syrupy; the on-disk line ending is
  decided, with LF recommended, before the first release that writes payloads
  (DEC-3 item 7). Rationale: settings are reviewable and machine-checkable, and
  they pin separators, escapes, and member order. Date/Author: 2026-09-27,
  planning agent, revised after panel review.
- DEC-11. Decision: the normative fixture decisions are NF-1 to NF-13 under
  `Interfaces and dependencies`. The roadmap 1.1.3 contract corpus is the
  lasting oracle; every fixture cites the NF identifier it discharges; an
  optional `mdast-util-from-markdown` differential run stays unshipped and
  outside CI. Rationale: design §11; each NF is checked by the self-checking
  probe. Date/Author: 2026-09-27, planning agent.
- DEC-12. Decision: verification scope. The executable evidence is the guard
  test (DOC-1 to DOC-6), its helper unit tests (UNIT-1 to UNIT-3), and the
  self-checking probe (EV-1). There are no pytest-bdd scenarios, Syrupy
  snapshots, end-to-end tests, Hypothesis properties, CrossHair runs, or
  Rust/Verus proofs in this task. Rationale: the task changes documents, not
  behaviour a user can exercise; pytest-bdd is not a dependency (Constraint 4);
  snapshots and fixtures are forbidden before acceptance (Constraint 3); the
  only executable logic is Markdown extraction over a finite, enumerable input
  shape, for which named examples are exhaustive enough; a Rust extension would
  breach the Python-only wheel (Constraint 8). The Wenmode-declaration check
  (exact `==` pin, PEP 440 variants such as `==0.15.10`, `==0.15.*`,
  `==0.15.1.0`, `==0.15.1+local`) moves to roadmap 1.2.1, where it can first
  fail for a real reason. The first obligations that merit property testing and
  symbolic execution are roadmap 2.1.2's canonicalizer invariants (idempotence,
  position and line-ending invariance, and the merge-before-normalize lemma of
  Surprise 12), where Hypothesis plus CrossHair over the pure canonicalizer is
  the proportionate tool. Date/Author: 2026-09-27, planning agent, revised
  after panel review.
- DEC-13. Decision: two pull requests. Pull request A (this branch, titled
  "Plan: … (1.1.2)") carries this ExecPlan, then ADR-003 and its
  `docs/contents.md` entry; it merges after acceptance. Pull request B,
  branched from `main` after A merges, carries EP-M3 and EP-M4. Rationale:
  squash merges collapse branch history (Surprise 15); two squash commits on
  `main` make the acceptance-before-implementation order verifiable for ever.
  Pull request A's merge commit SHA is recorded here when known. Date/Author:
  2026-09-27, planning agent, added after panel review.
- DEC-14. Decision: the comparison contract keeps design §4's key: two inputs
  are equivalent precisely when the same installed package version (and hence
  the same Wenmode pin and contract) produces byte-identical payloads for both.
  The contract version is a migration signal, not the equivalence key.
  Rationale: under DEC-2 and DEC-9 one contract version can span several
  Wenmode pins and conformance fixes, and Risk 6 shows interpreters can differ,
  so "same contract version" would over-promise. Date/Author: 2026-09-27,
  planning agent, reversed after panel review.
- DEC-15. Decision: no component architecture document is created. The
  technical design is the architecture record for the snapshot contract, and
  the one new internal interface (`tests/support/adr_contract.py`) is
  documented in `docs/developers-guide.md` under a new
  `### ADR manifest parser for contract tests`, beside the existing
  `### Makefile parser for contract tests`. Helper sweep (AGENTS.md):
  `tests/support/make_contract.py` parses the Makefile and workflow YAML only,
  and no Markdown extraction helper exists, so the new module duplicates
  nothing. Its reuse policy: tests only, text-in and data-out functions, no
  file I/O in helpers. Date/Author: 2026-09-27, planning agent.
- DEC-16. Decision: ADR-003 keeps the template's `## Decision Drivers` heading
  verbatim, although the style guide otherwise prefers sentence case.
  Rationale: Constraint 5; recorded so a reviewer does not "fix" it.
  Date/Author: 2026-09-27, planning agent.
- DEC-17. Decision: the writer emits C1 controls, U+2028, U+2029, and
  bidirectional controls literally rather than escaping them. Rationale: design
  §8 requires unescaped Unicode; escaping them needs a custom encoder in place
  of the standard library; GitHub's diff view already flags bidirectional text.
  Recorded as a known limitation in the ADR. Date/Author: 2026-09-27, planning
  agent.
- DEC-18. Decision: panel review outcome. Verdict: proceed with conditions.
  Adopted: DEC-2's pre-release amendment window and `### Amendments` location;
  DEC-3's widened roadmap edits; DEC-6's ordered rules; DEC-7 reversed to
  recommend merging; DEC-8's option E; DEC-9 rewritten around payload change,
  with the Dependabot `ignore`, the security path, the warning blocker, and the
  triggers; DEC-10's structured writer, value domain, strict UTF-8, and on-disk
  deadline; DEC-12's removal of the Hypothesis property and relocation of the
  Wenmode-declaration check; DEC-13's two pull requests; DEC-14's equivalence
  key; the self-checking probe with key coverage and `-W error`; the guard
  test's discovery of the current contract ADR, its allowlist, and its
  executable-example check; formatter and Windows risks. Not adopted: a sidecar
  version file (Syrupy's snapshot-directory walk may report it as unused;
  unverified and unnecessary under DEC-8); escaping C1 and bidirectional
  controls (DEC-17). Date/Author: 2026-09-27, planning agent.
- DEC-19. Decision: the maintainer settled the three questions put at plan
  review, so the ADR is drafted with its direction fixed and no outstanding
  decisions:
  1. Adopt `merge-plain-text` (DEC-7)? Answer: yes.
  2. No payload version marker (DEC-8 option A)? Answer: yes.
  3. File an upstream report on the GFM tag-filter divergence (Surprise 5)?
     Answer: no; not a relevant concern to the implementation. NF-7 still
     records the divergence as ratified behaviour, and an upstream change to
     it remains a payload change under DEC-9, but no report is drafted or
     filed.
  Date/Author: questions 2026-09-27, planning agent; answers 2026-09-28,
  maintainer (pull request #58 conversation).

## Outcomes & retrospective

Not started. At completion, record what was achieved against the purpose, pull
request A's and B's merge SHAs, and these handoffs: Surprise 7 to roadmap
2.2.2; the on-disk line ending to 2.3.1; the Dependabot `ignore` and the
Wenmode-declaration check (with its PEP 440 cases) to 1.2.1; the adapter
construction check to 1.2.2; the canonicalizer invariants and the
merge-before-normalize lemma to 2.1.2; and the writer-settings check and strict
UTF-8 pre-check to 2.2.1.

## Context and orientation

This repository is a Python library (`hatchling`, `uv`, Python 3.12 or later)
that will become a Syrupy extension. **Syrupy** is a pytest snapshot plugin: a
test compares a value with a stored file, and Syrupy creates, updates, and
deletes those files. **mdast** is the Markdown Abstract Syntax Tree format used
by the unified ecosystem. **Wenmode** is a pure-Python Markdown parser whose
`to_ast()` emits mdast-compatible dictionaries. Its **GitHub profile** (the
`github` preset) is CommonMark plus GitHub Flavoured Markdown (GFM) tables,
strikethrough, task lists, extended autolinks, footnotes, and GitHub's
disallowed-HTML tag filter. An **ADR** (architectural decision record) is a
dated document recording one decision and its rationale.

A **snapshot payload** is the exact text produced for one assertion. The
**snapshot contract** is everything that determines that text for a given
Markdown input. Its **contract version** is the integer this task introduces. A
**manifest** is the single fenced `toml` block in the ADR that states the
contract's values in machine-readable form. A **guard test** is a test that
fails when two documents, or a document and code, disagree.

Current state:

1. `syrupy_mdast/` holds the v1 public surface from roadmap 1.1.1:
   `MarkdownAstError` (`syrupy_mdast/_core/errors.py`) and
   `MarkdownAstSnapshotExtension` (`syrupy_mdast/_extension.py`, with
   `file_extension = "mdast.json"`), whose `serialize()` raises
   `NotImplementedError` naming roadmap 2.3.1. This task does not touch it.
2. `docs/syrupy-mdast-design.md` (revision dated 2026-07-28) defines the
   contract in §§4, 7, 8, 11, and 13. §11 requires this ADR.
3. `docs/adr-001-python-lint-architecture.md` and
   `docs/adr-002-main-owns-codescene-coverage-publication.md` exist. Neither
   follows the style-guide template exactly; ADR-003 must.
4. `docs/contents.md` indexes documents under "Decision records".
5. `tests/` contains infrastructure contract tests. None reads `docs/`; the
   guard test introduced here is a new pattern, modelled on
   `tests/test_toolchain_contract.py` (parse each site, compare semantics, name
   both sites in the failure). `tests/support/` holds shared helpers, and
   `tests/codescene_contract/` shows that helpers may have their own tests.
6. `make fmt` rewrites Markdown with `mdtablefix` and `markdownlint-cli2 --fix`;
   `make check-fmt` checks Ruff formatting and `mdtablefix`;
   `make markdownlint` and `make nixie` are separate Markdown gates.
7. `.github/dependabot.yml` batches minor and patch pip updates into one group,
   a Dependabot automerge workflow merges them, and
   `tests/test_dependabot_config_contract.py` forbids group exclusions.

### Signposted reading

Read these, in this order, before editing:

1. `docs/roadmap.md` task 1.1.2 and its dependants 1.1.3, 1.2.1-1.2.3, 2.1.1,
   2.1.2, 2.2.1, 2.3.1, and 3.2.1, so that the ADR fixes what they need and
   nothing they own.
2. `docs/syrupy-mdast-design.md` §§3-4, 7-8, 11, 13, and 15 (the contract being
   ratified); §§9-10 only for the failure taxonomy and concurrency rule the ADR
   cites.
3. `docs/documentation-style-guide.md` §"Architectural decision records
   (ADRs)", the template ADR-003 must follow verbatim, plus the spelling,
   footnote, and table-caption rules.
4. `docs/execplans/1-1-1-replace-package-stub-with-v1-public-contract.md`
   DEC-13 and `Conformance basis`: the template handoff obligation.
5. `docs/adr-002-main-owns-codescene-coverage-publication.md`: house tone.
6. `tests/test_toolchain_contract.py` and `tests/support/make_contract.py`:
   the cross-site contract-test pattern and `REPO_ROOT`.
7. `.rules/python-00.md` and `.rules/python-typing.md`, plus
   `pyproject.toml`'s Ruff import conventions: use `import typing as typ`,
   `import collections.abc as cabc` (under `typ.TYPE_CHECKING` where only
   annotations need it), and `import dataclasses`; `from typing import …` and
   `from dataclasses import …` are banned. `tests/support/*.py` ignores only
   `S101`, so `PLR2004`, `PLR6301`, and the docstring rules still apply there.
8. `docs/developers-guide.md` §"Maintain syrupy-mdast", §"Makefile parser for
   contract tests", and §"Dependabot policy".
9. `AGENTS.md`: gates, commit rules, Markdown rules.

Relevant skills: `execplans` (this plan), `en-gb-oxendict` (all prose),
`python-router` then `python-testing` (guard-test structure), `firecrawl-mcp`
(re-verifying Wenmode's latest release), `logisphere-design-review` (if the
maintainer requests changes to a decision), `commit-message`, and
`pr-creation`. Delegate full gate runs to the `scrutineer` agent.

Out of scope, do not read for this task:
`docs/complexity-antipatterns-and-refactoring-strategies.md` (no production
code), `docs/scripting-standards.md` (no scripts), and
`docs/local-validation-of-github-actions-with-act-and-pytest.md` (no workflow
change).

## Conformance basis

There is no Terms of Reference document for this project. Upstream artefacts:

1. `docs/syrupy-mdast-design.md`, revision dated 2026-07-28, status "Proposed
   living design": §3 (Wenmode selection, per-call parser), §4 (comparison
   contract), §7 (parser profile and dependency policy), §8 (canonicalization
   contract), §11 (the ADR requirement), §13 (compatibility and snapshot
   version), §15 (risks). The design's preamble gives accepted ADRs precedence.
2. `docs/roadmap.md` task 1.1.2, amended per DEC-3.
3. Governing standards: `AGENTS.md`, `docs/documentation-style-guide.md`, and
   `.rules/python-*.md`.
4. Handoff: 1.1.1 ExecPlan DEC-13 (template conformance).

Deviations from the design, each recorded in the ADR and reconciled into the
design at EP-M3:

1. DEC-5: preset factory call in place of design §7's uncalled preset.
2. DEC-6: exact rule order and key order fixed in the ADR rather than left to
   an implementation constant.
3. DEC-7: a fifth normalization rule, `merge-plain-text`, beyond
   design §8's "only these transformations".
4. DEC-9: design §13's "Major releases may change the Wenmode version" is
   replaced by the payload-change rule (a payload-neutral pin move may ship in
   a patch release), and §13's "minor releases may accept previously rejected
   syntax" clause is retained only for inputs rejected by the byte limit or
   encoding checks, since Markdown parsing itself never rejects input.
5. DEC-10: exact writer settings, value domain, and on-disk boundary.
6. DEC-14: equivalence stays keyed on the installed package version (design
   §4 unchanged); only the contract-version terminology is added.

None changes the public API, the dependency set, or the trust boundary.

Trace links (all guard tests are written in EP-M3):

```plaintext
TDD-§11 -> RM-1.1.2 -> EP-M2 -> test_exactly_one_contract_adr_is_accepted
TDD-§11 -> RM-1.1.2 -> EP-M1 -> test_manifest_has_the_contract_schema
TDD-§6  -> RM-1.1.2 -> EP-M3 -> test_manifest_file_extension_matches_the_extension
TDD-§8  -> RM-1.1.2 -> EP-M1 -> test_key_order_is_framed_and_duplicate_free
TDD-§7  -> RM-1.1.2 -> EP-M3 -> test_design_parser_construction_matches_manifest
TDD-§7  -> RM-1.1.2 -> EP-M3 -> test_no_normative_document_uses_the_uncalled_preset
TDD-§8  -> RM-1.1.2 -> EP-M3 -> test_design_json_examples_are_writer_fixed_points
TDD-§11 -> RM-1.1.2 -> EP-M3 -> test_contract_adr_is_indexed_and_cited_by_the_design
TDD-§11 -> RM-1.1.3 -> EP-M1 -> ADR-003 NF-1..NF-13 (consumed by the 1.1.3 corpus)
TDD-§13 -> RM-1.2.1 -> handoff -> Wenmode declaration check (DEC-12)
```

## Verification plan

This task introduces documents and a guard test. It introduces no production
invariant. The obligations below are over documents and over small test-support
functions; each states how it can fail.

### Axioms

1. A1. Wenmode 0.15.1's documented shape contract: every node has a string
   `type`; `None`-valued fields are omitted by `to_ast()`; `False`, empty
   lists, and empty strings are preserved; the per-type field table in
   Wenmode's "Node model" reference. Cross-checked by EV-1; roadmap 1.2.3 owns
   committed probes.
2. A2. Wenmode's compatibility page states that `Node.to_ast()` output for
   documented node types is intended to be stable through the beta, while
   edge-case parsing may change. DEC-9 is built on the second clause.
3. A3. Python's `json.dumps` with the DEC-10 settings is deterministic for the
   declared value domain and preserves mapping insertion order, on CPython and
   PyPy for the supported Python versions (separators and escapes unchanged
   since Python 3.4; no floats in the domain).
4. A4. PyPI's recorded SHA-256 for `wenmode-0.15.1-py3-none-any.whl` is as
   quoted in DEC-4 (retrieved 2026-09-27; re-check at EP-M1).
5. A5. `tomllib` (standard library) parses the manifest block.
6. A6. Wenmode's label case folding and emphasis punctuation classification may
   depend on the interpreter's Unicode database version (Risk 6); v1 does not
   claim byte identity across interpreters for input whose parse depends on
   Unicode data added after Unicode 15.0.

### Obligations

**DOC-1: exactly one current contract ADR.** Statement: among `docs/adr-*.md`
files containing a `### Contract manifest` heading, exactly one has status
`Accepted`; every other one has status `Superseded (YYYY-MM-DD) by ADR-NNN.`
naming an existing file; and their `contract-version` values run 1 to N without
gaps, with the accepted one holding N. Method: explicit assertions. Artefact:
`test_exactly_one_contract_adr_is_accepted`. Rationale: discovering the current
ADR, rather than hard-coding ADR-003, keeps the test valid across the
supersession DEC-2 prescribes. Non-vacuity: assert that the discovered set is
non-empty and contains ADR-003. Negative controls: UNIT-1.

**DOC-2: manifest schema.** Statement: the current contract ADR contains
exactly one fenced `toml` block under `### Contract manifest`. It parses to a
`[snapshot-contract]` table whose keys are exactly `contract-version` (positive
integer), `wenmode` (a bare `MAJOR.MINOR.PATCH` string), `parser`,
`file-extension`, `normalization` (list of rule identifiers drawn from DEC-6),
`key-order`, and the sub-table `json-writer`, whose keys are exactly those in
`Interfaces and dependencies`. `file-extension` equals
`syrupy_mdast.MarkdownAstSnapshotExtension.file_extension`. Method: explicit
assertions; the extension comparison is a read-only import. Artefacts:
`test_manifest_has_the_contract_schema` and
`test_manifest_file_extension_matches_the_extension`. Non-vacuity: key-set
equality, not subset; the extractor rejects zero or two manifest blocks
(UNIT-2).

**DOC-3: key order and rule order are well formed.** Statement: `key-order` has
no duplicates, starts with `type`, ends with `children`, places `value` before
`data` before `children`, and omits `position`; `normalization` has no
duplicates, and if it contains `merge-plain-text`, that rule precedes
`normalize-line-endings`. Method: explicit assertions through the helper
`key_order_problems` and `rule_order_problems`. Artefact:
`test_key_order_is_framed_and_duplicate_free`. Rationale: these are design §8's
grouping rules and Surprise 12's lemma; exact membership is fixed by the ADR
and is not restated in the test. Negative controls: UNIT-3. Residual gap:
coverage of every emitted key is shown by EV-1 now and by roadmap 1.2.3's
committed probe later.

**DOC-4: parser construction agrees across normative documents.** Statement:
the manifest's `parser` string appears verbatim inside a fenced `python` block
of design §7, and no file in the allowlist (the design, `docs/roadmap.md`,
`docs/users-guide.md`, and `docs/developers-guide.md`) contains text matching
the uncalled-preset pattern `Parser\(\s*github\s*[,)]`, whether in a code fence
or inline code. Method: explicit test over file text. Artefacts:
`test_design_parser_construction_matches_manifest` and
`test_no_normative_document_uses_the_uncalled_preset`. Evidence: both red at
the start of EP-M3 (design §7 and roadmap 1.2.2 and 2.1.1 still use the
uncalled form); green after reconciliation. Non-vacuity: assert that the design
yields at least one `python` fence under a heading containing "Parser profile"
and that every allowlisted file exists and is non-empty. An allowlist, not a
directory scan, keeps later ExecPlans and superseded ADRs free to quote the old
form as history.

**DOC-5: the ADR is discoverable.** Statement: `docs/contents.md` links the
current contract ADR under "Decision records", and design §§7, 8, 11, and 13
each link it. Method: link-target assertions. Artefact:
`test_contract_adr_is_indexed_and_cited_by_the_design`. Evidence: red at the
start of EP-M3 for the design links; green after.

**DOC-6: the design's JSON examples obey the contract.** Statement: every fenced
`json` block in design §8 and in the ADR's normative fixture decisions, when
parsed, re-serialized with the manifest's `json-writer` settings, equals its
own text (a fixed point); every mapping in it follows `key-order`; and no list
in it holds two adjacent plain text nodes (`merge-plain-text`). Method:
explicit test with the standard library. Artefact:
`test_design_json_examples_are_writer_fixed_points`. Rationale: the design's
examples are the first thing an implementer copies; this is the only place in
this task where the contract can be executed. Non-vacuity: assert at least one
`json` block is found in design §8. Negative control: UNIT-3 feeds a
mis-ordered and a mis-indented example to the same checker.

**UNIT-1 to UNIT-3: helper happy and unhappy paths.** In
`tests/test_snapshot_contract_adr.py`, named examples against hand-written
Markdown strings:

1. UNIT-1: `adr_status` returns `Accepted`, `Proposed`, and
   `Superseded (2027-01-01) by ADR-004.` for the three forms, and raises
   `ValueError` naming the file when `## Status` is missing or empty.
2. UNIT-2: `read_manifest` returns the dataclass for a well-formed block, and
   raises `ValueError` for no block, two blocks, a block under the wrong
   heading, invalid TOML, a missing key, an extra key, and a wrong type.
3. UNIT-3: `key_order_problems` reports a duplicate, `position`, a wrong first
   or last key, and `data` after `children`; `rule_order_problems` reports
   `merge-plain-text` after `normalize-line-endings`; `writer_problems` reports
   a mis-ordered mapping and a mis-indented document.

Rationale: parameterized named examples cover the finite input shapes
exhaustively. Evidence: red first, because the helpers are written as stubs
returning a neutral value (for example, `[]` or a fixed string) and the tests
precede their bodies.

**EV-1: empirical grounding of NF-1 to NF-13.** Statement: each normative
fixture decision matches the output of Wenmode 0.15.1's GitHub profile, the v1
construction emits no warning, and every member name emitted across all 22
GitHub-profile node types is in `key-order`. Method: the self-checking probe in
`Artefacts and notes`, run under `-W error` in a throwaway environment at Stage
A, at EP-M1, and immediately before the acceptance commit; reproduced in the
ADR's `### Evidence`. Rationale: committed probes need the Wenmode dependency
and belong to roadmap 1.2.3. Non-vacuity: every equivalence check is paired
with a negative witness (unresolved reference, undefined footnote, unfiltered
versus filtered HTML, hard versus soft break), and NF-12 asserts that 22 node
types were reached. Discharge: the expected output in `Artefacts and notes`,
exactly.

No introduced invariant warrants a property test, CrossHair, a bounded model
checker, or a formal prover (DEC-12).

## Plan of work

Stage A: orientation (no edits). Read the signposted material. Run the full
gate set on the untouched tree and keep the logs. Run the probe and compare its
output. Check PyPI for a Wenmode release newer than 0.15.1.

Stage B: ADR drafting (EP-M1, pull request A). Write ADR-003 as `Proposed`,
following the template headings verbatim and the DEC-19 answers. Index it in
`docs/contents.md`. Commit and push.

Stage C: acceptance gate (EP-M2, pull request A). Request acceptance of the
written ADR. On acceptance, set `Accepted`, commit, push, and ask the
maintainer to merge pull request A. Do not proceed without both.

Stage D: guard and reconcile (EP-M3, pull request B). Branch from the updated
`main`. Write the guard test and helpers; observe the planned failures; then
reconcile the design, roadmap, users' guide, and developers' guide until they
pass.

Stage E: sweep (EP-M4, pull request B). Run every gate, tick roadmap 1.1.2,
complete the retrospective, set this plan to `COMPLETE`.

## Milestones and plateaus

### EP-M1: ADR-003 drafted as Proposed (pull request A)

- Outcome: `docs/adr-003-parser-profile-and-snapshot-version-policy.md` exists
  with status `Proposed`, `docs/contents.md` lists it, and this plan records
  progress. Nothing else changes. A proposed ADR is a record of a proposal;
  committing it does not pre-empt acceptance.
- Content, in the template's order, with its headings verbatim:
  1. `## Status`: `Proposed.`
  2. `## Date`: the drafting date.
  3. `## Context and problem statement`: why the snapshot contract needs one
     versioned record; what design §11 requires; what was open.
  4. `## Decision Drivers`: reviewability (design §1), determinism, Wenmode
     beta churn, the Python-only boundary, conservative equivalence, and
     protection from automatic dependency updates.
  5. `## Requirements` with `### Functional requirements` and
     `### Technical requirements`.
  6. `## Options considered`: two independent decisions, each introduced as
     such. Payload versioning: `### Option A: No version marker`,
     `### Option B: In-payload version member`, `### Option C: Versioned file
     suffix`, `### Option D: Header with taint`, and
     `### Option E: Informational header ignored by comparison`, compared in a
     table captioned "*Table 1: Payload versioning options.*". Text
     segmentation: `### Option F: Retain Wenmode's text segmentation` and
     `### Option G: Merge adjacent plain text nodes`, compared in
     "*Table 2: Text segmentation options.*".
  7. `## Decision outcome / proposed direction`, containing, in order:
     `### Contract manifest` (the single fenced `toml` block); `### Parser
     profile` (DEC-5); `### Wenmode release` (DEC-4, licence, wheel hash);
     `### Normalization policy` (DEC-6, DEC-7, referring to the manifest rather
     than restating `key-order`); `### Canonical JSON writer` (DEC-10, the
     escape set, DEC-17); `### Comparison contract` (DEC-14);
     `### Snapshot-version policy` (DEC-2, DEC-8, DEC-9); `### Normative
     fixture decisions` (NF-1 to NF-13); `### Evidence` (the probe script, the
     one-line command, the expected output, and the probe date); and
     `### Amendments` (empty, with a sentence explaining DEC-2's rule).
  8. `## Goals and non-goals`: non-goals from design §2.2, plus unified byte
     compatibility and on-disk line terminators.
  9. `## Migration plan`: numbered phases mapping to roadmap 1.1.3, 1.2.1,
     1.2.2, 1.2.3, 2.1.2, 2.2.1, 2.3.1, and 3.2.1, as in DEC-3.
  10. `## Known risks and limitations`: Risks 1 to 8, the consequences of
      `merge-plain-text`, and DEC-17.
  11. `## Outstanding decisions`: "None." (DEC-19 settled every question.)
- Acceptance evidence: Constraint 10's full gate sequence passes; each heading
  is checked against the template by eye; EV-1 re-run matches.
- Conformance check: design sections cited; only the ADR, `docs/contents.md`,
  and this plan changed.
- Recovery: new file; revert the commit to retry.
- Remaining gaps: acceptance, reconciliation, and tests.
- Compatibility decision: none.

### EP-M2: ADR-003 accepted (pull request A merged)

- Outcome: the ADR's status reads
  `Accepted (YYYY-MM-DD): <one-sentence summary>.`, per the style guide, with a
  link to the maintainer's accepting comment; pull request A is merged.
- Procedure: push; post a comment on pull request A asking the maintainer to
  accept ADR-003 or request changes, and state it in the session. Set this
  plan's status to `BLOCKED` while waiting (Tolerance 9 governs re-pings). On
  requested changes, revise `Decision log` first (Tolerance 4), then the ADR,
  then ask again. Immediately before the acceptance commit, re-run EV-1 and
  re-check Tolerance 2.
- Acceptance evidence: the maintainer's explicit acceptance, quoted with its
  date and link in `Decision log`; the acceptance commit; pull request A's
  squash SHA on `main`, recorded in DEC-13.
- Conformance check: the accepted text equals the reviewed text apart from the
  status line and resolved outstanding decisions.
- Recovery: if acceptance is withdrawn before merge, revert the status commit.
- Compatibility decision: none.

### EP-M3: guard, then reconcile (pull request B)

- Outcome: the guard test passes and every normative document agrees with
  ADR-003.
- Red: create a branch from the updated `main` (suggested name
  `1-1-2-guard-snapshot-contract`). Add `tests/support/adr_contract.py` with
  stub helpers (see `Interfaces and dependencies`) and
  `tests/test_snapshot_contract_adr.py`. Run the focused command in
  `Concrete steps`. Expected failures: UNIT-1 to UNIT-3 (stubs), DOC-4 (design
  §7 and roadmap 1.2.2 and 2.1.1 still use the uncalled form), and DOC-5
  (design does not cite ADR-003). DOC-1, DOC-2, DOC-3, and DOC-6 may already
  pass against the accepted ADR and the current design; that is expected, and
  their negative controls are the UNIT examples.
- Green: implement the helpers; then edit:
  1. `docs/syrupy-mdast-design.md`:
     - design section 7's code block and prose use `github()`;
     - sections 4, 7, 8, 11, and 13 cite ADR-003;
     - section 8 refers to the ADR for the rule order and key order, and adds
       the `null`-element rule and the merge rule;
     - section 11 names ADR-003 as the required record;
     - section 13 adopts DEC-9;
     - section 15 adds the GFM divergence, formatter, and Windows risks;
     - the references gain Wenmode's node-model and changelog pages and the GFM
       specification; and
     - "Last updated" moves to the reconciliation date.
  2. `docs/roadmap.md`: exactly DEC-3's edits 2 to 7.
  3. `docs/users-guide.md`: a short section, `## Snapshot contract and
     upgrades`, of at most two paragraphs plus one recipe, written in the
     future tense that the existing "after serialization is implemented"
     wording uses. It says that snapshots follow contract v1, defined by
     ADR-003 (linked, not restated), and is provisional until syrupy-mdast
     1.0. It says that patch releases never knowingly change payloads, and that
     a payload change arrives in a minor release (before 1.0) with release
     notes and a review-then-`pytest --snapshot-update` step. It recommends
     installing syrupy-mdast in a test-only dependency group and gives a recipe
     for excluding `**/__snapshots__/**/*.mdast.json` from JSON formatters (for
     example a `.prettierignore` line) and marking them `text eol=lf` in
     `.gitattributes`.
  4. `docs/developers-guide.md`: §"Upgrade Wenmode" rewritten to cite ADR-003
     and DEC-9 (dedicated pull request, corpus plus changelog classification,
     no Dependabot, warnings blocker, triggers, contract-version decision,
     amendment or superseding ADR); a new `### Snapshot contract ADR` paragraph
     describing the manifest and the guard test, and the rule that each later
     code constant (pin, parser construction, key order, rule order, writer
     settings) is added to the guard test when it is introduced; and a new
     `### ADR manifest parser for contract tests` describing
     `tests/support/adr_contract.py` (DEC-15).
- Acceptance evidence: focused test green; Constraint 10's full gate sequence
  green.
- Conformance check: every deviation in `Conformance basis` is now in the
  design text; no production file touched; roadmap edits equal DEC-3's list.
- Recovery: tests and documents are independent files; revert per file.
- Remaining gaps: roadmap tick and retrospective.
- Compatibility decision: none.

### EP-M4: sweep and close (pull request B)

- Outcome: all gates pass; roadmap 1.1.2 ticked (DEC-3 edit 1); this plan
  `COMPLETE` with retrospective and handoffs.
- Acceptance evidence: gate logs, and, on `main` after pull request B merges,
  the following command lists pull request A's squash commit below pull request
  B's:

  ```bash
  git log --oneline -- docs/adr-003-parser-profile-and-snapshot-version-policy.md \
    tests/test_snapshot_contract_adr.py
  ```

- Recovery: documentation-only commit; revert to retry.

## Concrete steps

Run everything from the repository root of a checkout of the relevant branch.
Run gates sequentially, never in parallel, each through `tee`:

```bash
BR=$(git branch --show-current)
make check-fmt 2>&1 | tee /tmp/check-fmt-syrupy-mdast-$BR.out
make typecheck 2>&1 | tee /tmp/typecheck-syrupy-mdast-$BR.out
make lint 2>&1 | tee /tmp/lint-syrupy-mdast-$BR.out
make test 2>&1 | tee /tmp/test-syrupy-mdast-$BR.out
make markdownlint 2>&1 | tee /tmp/markdownlint-syrupy-mdast-$BR.out
make nixie 2>&1 | tee /tmp/nixie-syrupy-mdast-$BR.out
```

Run the probe (Stage A, EP-M1, and before the acceptance commit). Save the
script from `Artefacts and notes` as `/tmp/wenmode-probe/probe.py`, then:

```bash
mkdir -p /tmp/wenmode-probe
cd /tmp/wenmode-probe && uv run --no-project --with wenmode==0.15.1 python -W error probe.py
```

Expected output, exactly:

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
version 0.15.1
```

(`uv` may print an `Installed 1 package` line first.) Then check for newer
releases with the `firecrawl-mcp` skill by scraping
`https://pypi.org/project/wenmode/#history`; Tolerance 2 applies if one exists.

Focused test loop during EP-M3:

```bash
uv run pytest -v tests/test_snapshot_contract_adr.py 2>&1 | tee /tmp/adr-contract-syrupy-mdast-$BR.out
```

Commits (subject lines; bodies explain why, Markdown allowed, with the
session's attribution trailer):

1. Pull request A: `Draft ADR-003 snapshot contract v1` (EP-M1), then
   `Accept ADR-003 snapshot contract v1` (EP-M2).
2. Pull request B: `Guard ADR-003 and reconcile the design` (EP-M3), then
   `Complete roadmap task 1.1.2` (EP-M4).

## Validation and acceptance

Quality criteria:

- Tests: `make test` passes; `tests/test_snapshot_contract_adr.py` passes; its
  UNIT examples failed against the stubs, and DOC-4 and DOC-5 failed before the
  reconciliation edits.
- Verification: DOC-1 to DOC-6 and UNIT-1 to UNIT-3 discharged; EV-1 output
  identical to the expected output above.
- Lint and typecheck: `make check-fmt`, `make typecheck`, and `make lint` pass
  (Interrogate at 100% including the new modules).
- Markdown: `make markdownlint` and `make nixie` pass.
- Process: on `main`, pull request A's squash commit (accepted ADR) precedes
  pull request B's.

Red-Green-Refactor record (fill in during EP-M3):

- Red: the focused command; expected failures listed under EP-M3.
- Green: the same command; all pass.
- Refactor: Constraint 10's full sequence.

No pytest-bdd feature file is part of this plan (DEC-12).

## Idempotence and recovery

Every step is a file edit or a read-only command and may be repeated. The probe
installs into `uv`'s cache and a throwaway environment; it never touches the
project environment or lockfile. If a gate fails midway, fix and re-run that
gate, then re-run the full sequence before committing. If the maintainer
rejects the ADR, revise on pull request A. If `make fmt` rewrites a file this
plan does not touch, revert that side effect and record it in
`Surprises & discoveries`.

## Artefacts and notes

The self-checking probe, `/tmp/wenmode-probe/probe.py` (never saved in the
repository; the ADR's `### Evidence` reproduces it):

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

The probe records Wenmode's raw output. NF-11 therefore checks that Wenmode
splits text (Surprise 4); `merge-plain-text` acts later, in the canonicalizer,
not in Wenmode.

Rule-order evidence for Surprise 12:

```plaintext
'a&#13;\nb\n' => [{"type": "paragraph", "children": [{"type": "text", "value": "a"},
                  {"type": "text", "value": "\r"}, {"type": "text", "value": "\nb"}]}]
```

Sources consulted (2026-09-27): Wenmode on PyPI
(<https://pypi.org/project/wenmode/>); Wenmode's presets, security,
compatibility, node model, and changelog pages under
<https://wenmode.lepture.com/>; the GFM specification 0.29-gfm
(<https://github.github.com/gfm/>); and Syrupy 5.0.0 and 6.0.0 source
(`syrupy/extensions/single_file.py`, `syrupy/extensions/amber/serializer.py`,
`syrupy/assertion.py`).

## Interfaces and dependencies

No production interface changes. No dependency changes.

### ADR-003 contract manifest (normative content for EP-M1)

The ADR's `### Contract manifest` contains exactly this block (values fixed by
DEC-4, DEC-5, DEC-6, DEC-7, and DEC-10):

```toml
[snapshot-contract]
contract-version = 1
wenmode = "0.15.1"
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

### ADR-003 normative fixture decisions (for EP-M1; consumed by 1.1.3 and 1.2.3)

"Equal" means the two inputs must produce byte-identical payloads; "distinct"
means they must not. Each item is checked against Wenmode by the probe line of
the same number.

- NF-1. Emphasis delimiter spelling: `*a*`/`_a_` and `**b**`/`__b__` equal.
- NF-2. Ordinary references: direct, full, collapsed, and shortcut forms equal
  when destination, title, and children agree; a definition before its use
  resolves; label matching is case-insensitive while link text keeps its case;
  unused definitions leave no trace; an unresolved reference stays literal
  text. Reference images resolve to `image` with `url`, `alt`, and `title` when
  present.
- NF-3. Footnotes: `footnoteReference` and `footnoteDefinition` carry
  `identifier` and `label`, both case-folded by Wenmode (so `[^F]`/`[^f]`
  equal); definitions stay at their source position (moving one is distinct);
  unused definitions are retained; repeated references repeat; undefined
  references stay literal text.
- NF-4. Omitted nullable members: absent `title`, `lang`, `meta`, `checked`
  (non-task items), and `start` (bullet lists) stay absent; no `null` member is
  synthesized.
- NF-5. `null` array elements: an unaligned table column is `null` inside
  `align` and is preserved; alignment changes are distinct.
- NF-6. Raw HTML: `html` nodes keep their `value`; tags on GitHub's disallowed
  list are rewritten by Wenmode to a leading `&lt;` with
  `data: {"escaped": true}`, and that non-empty `data` is preserved, so
  filtered and unfiltered HTML are distinct.
- NF-7. Known divergence: CommonMark type-1 HTML blocks whose tag is on the
  disallowed list (`<script`, `<style`, `<textarea`) are not tag-filtered in
  0.15.1 and are ratified as observed; other disallowed tags (`<title>`,
  `<iframe>`, `<xmp>`, `<plaintext>`, and so on) are filtered. An upstream fix
  is a payload change under DEC-9.
- NF-8. Line endings: LF, CRLF, and CR inputs produce equal payloads after
  `normalize-line-endings`, including in text, code values, and titles; the
  parsed structure (paragraphs, hard breaks) is already equal.
- NF-9. Positions: payloads never contain `position`; the parser is built with
  `positions=False`, and `remove-position` removes it should a future parser
  emit it anyway.
- NF-10. Preserved distinctions: hard break versus soft line break; code
  whitespace, `lang`, and `meta`; list `ordered`, `start`, `spread`, item
  `checked`, and item order; table cell content and alignment; raw HTML
  spelling.
- NF-11. Text segmentation: Wenmode splits text at entity references and
  backslash escapes; `merge-plain-text` rejoins adjacent plain text nodes, so
  `a & b` equals `a &amp; b`, and `a*b` equals `a\*b`. A text node carrying any
  member besides `type` and `value` is never merged.
- NF-12. Key order and coverage: every emitted mapping's members follow the
  manifest's `key-order`, then remaining members by code point; every member
  name Wenmode emits across the 22 GitHub-profile node types is in `key-order`;
  a contract fixture pins one node of every type.
- NF-13. Numeric character references: `&#0;` becomes U+FFFD; `&#xD800;` and
  `&#x110000;` stay literal text; no lone surrogate reaches a payload.

### Test-support interface (EP-M3)

In `tests/support/adr_contract.py` (text in, data out, no file I/O):

```python
import dataclasses
import typing as typ

if typ.TYPE_CHECKING:
    import collections.abc as cabc

MANIFEST_HEADING: typ.Final = "### Contract manifest"


@dataclasses.dataclass(frozen=True, slots=True)
class SnapshotContractManifest:
    """Typed view of one ADR's `[snapshot-contract]` table."""

    contract_version: int
    wenmode: str
    parser: str
    file_extension: str
    normalization: tuple[str, ...]
    key_order: tuple[str, ...]
    json_writer: cabc.Mapping[str, str | int | bool]


def adr_status(markdown: str) -> str: ...
def read_manifest(markdown: str) -> SnapshotContractManifest: ...
def fenced_blocks(markdown: str, language: str) -> list[str]: ...
def key_order_problems(key_order: cabc.Sequence[str]) -> list[str]: ...
def rule_order_problems(normalization: cabc.Sequence[str]) -> list[str]: ...
def writer_problems(document: str, manifest: SnapshotContractManifest) -> list[str]: ...
```

`tests/test_snapshot_contract_adr.py` owns all file reads (through
`tests.support.make_contract.REPO_ROOT`) and holds DOC-1 to DOC-6 and UNIT-1 to
UNIT-3.

## Revision notes

- 2026-09-27: initial draft from reconnaissance, a Wenmode 0.15.1 probe, and
  external research.
- 2026-09-27: revised after a four-agent, six-lens expert-panel review (DEC-18).
  Changed: two pull requests to survive squash merges (DEC-13); the equivalence
  key restored to the package version (DEC-14); the snapshot-version policy
  rewritten around any payload change, with a Dependabot `ignore`, security
  path, warnings blocker, and upgrade triggers (DEC-9); a pre-release amendment
  window (DEC-2); ordered normalization rules and a recommendation to merge
  plain text nodes (DEC-6, DEC-7); a structured writer specification and
  on-disk line-ending deadline (DEC-10); roadmap edits that bind later tasks to
  the manifest (DEC-3); a self-checking probe with key coverage and `-W error`;
  a guard test that discovers the current contract ADR, scans an allowlist, and
  executes the design's JSON examples; the Hypothesis property removed and the
  Wenmode-declaration check moved to roadmap 1.2.1 (DEC-12); new risks for
  formatters, Windows line endings, Unicode data, pin conflicts, and warnings.
  Effect on remaining work: the maintainer answers DEC-19 at plan approval;
  EP-M1 drafts the ADR on pull request A; EP-M3 starts on a new branch after
  pull request A merges.
- 2026-09-28: recorded the maintainer's DEC-19 answers. `merge-plain-text` is
  now unconditional in DEC-6, DEC-7, the manifest, DOC-6, NF-11, and the
  milestones; DEC-8's option A is confirmed; no upstream report is filed, so
  the draft report text is removed and Risk 3 and EP-M1's outstanding decisions
  are updated. Effect on remaining work: EP-M1 starts once the plan itself is
  explicitly approved.
