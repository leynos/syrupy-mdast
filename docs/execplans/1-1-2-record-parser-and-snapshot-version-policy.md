# Record the parser-profile and snapshot-version policy in an ADR

This ExecPlan (execution plan) is a living document. The sections `Constraints`,
`Tolerances`, `Risks`, `Progress`, `Surprises & discoveries`, `Decision log`,
`Outcomes & retrospective`, `Conformance basis`, and `Verification plan` must
be kept up to date as work proceeds.

Status: DRAFT

## Purpose / big picture

`syrupy-mdast` will compare Markdown by its parsed structure rather than its
source text. What counts as "the same document" is therefore a persisted
contract: every `.mdast.json` snapshot a user commits encodes one particular
parser release, parser profile, normalization policy, key order, and JSON
spelling. If any of those drifts silently, users' snapshots churn with no
explanation, or, worse, a real change stops being detected.

The technical design names that contract but leaves its load-bearing values
open: no Wenmode release is chosen, the snapshot-format version is described
only as "follows semantic versioning", the exact key order is deferred to "an
immutable constant", and several Wenmode behaviours the design ratifies were
never observed against a real release. The design itself (§11) requires "an
explicitly versioned ADR" recording the complete contract, "accepted before
committing any related implementation or fixture change".

After this change a maintainer or contributor can open one document,
`docs/adr-003-parser-profile-and-snapshot-version-policy.md`, and read:

1. the snapshot contract version (`1`) and the rule that decides when it
   changes;
2. the exact Wenmode release (`0.15.1`), the exact parser construction, and why;
3. the normalization policy, including the exact key-order sequence and the
   exact JSON writer call;
4. the comparison contract: what compares equal and what does not;
5. the snapshot-version policy: how contract changes map to package releases,
   what users see, and how Wenmode upgrades are reviewed; and
6. the normative fixture decisions that roadmap task 1.1.3 must turn into a
   corpus and task 1.2.3 must turn into Wenmode probes.

A machine-readable manifest inside the ADR is guarded by a documentation
contract test, so the ADR, the technical design, and (from roadmap task 1.2.1
onwards) `pyproject.toml` cannot disagree about the parser construction or the
Wenmode pin without failing `make test`.

Observable success:

```bash
uv run pytest -v tests/test_snapshot_contract_adr.py
```

Expected: every test passes, and the report includes `test_adr_is_accepted`,
`test_design_parser_construction_matches_adr`, and
`test_pyproject_wenmode_declaration_agrees_with_adr`. Temporarily editing the
design's §7 code block back to the deprecated `Parser(github, positions=False)`
makes `test_design_parser_construction_matches_adr` fail with a message naming
both documents.

This task deliberately delivers **no** production code, no Wenmode dependency,
no corpus fixtures, and no snapshots. Those belong to roadmap tasks 1.1.3,
1.2.1-1.2.3, and phase 2, and the ADR must be accepted before any of them is
committed.

## Constraints

These are hard invariants. Violating one requires escalation, not a workaround.

1. Nothing under `syrupy_mdast/` changes. This task records a contract; it does
   not implement one. (Design §11: the ADR precedes implementation.)
2. `wenmode` is not added to `pyproject.toml`, `uv.lock`, or any dependency
   group. That is roadmap task 1.2.1. The Wenmode probes in this plan run in a
   throwaway environment under `/tmp` via `uv run --no-project --with`.
3. No corpus fixture, `.mdast.json` file, or `__snapshots__` directory is
   created. That is roadmap task 1.1.3 and depends on the accepted ADR.
4. No new runtime or development dependency. The documentation contract test
   uses only the standard library, `pytest`, `hypothesis`, and `packaging`
   (already locked at 26.3 as a hard dependency of `pytest`).
5. The ADR follows the template in `docs/documentation-style-guide.md`
   (§"Architectural decision records (ADRs)") verbatim in heading names and
   order. This is a handoff obligation from the 1.1.1 ExecPlan (its DEC-13):
   ADR-001's Nygard layout must not spread.
6. The implementer must not accept the ADR on the maintainer's behalf. The
   status moves from `Proposed` to `Accepted` only after explicit maintainer
   acceptance of the written ADR text. Approval of this ExecPlan approves the
   plan and the recommended direction; it is not acceptance of the ADR.
7. No commit containing the documentation contract test, design-document
   reconciliation, users' guide text, or developers' guide text lands before
   the commit that marks ADR-003 `Accepted`.
8. The package remains Python-only (design §2.3, §13). No Rust extension, Bun,
   Node.js, or JavaScript asset is introduced, including for verification.
9. Prose is en-GB-oxendict, wrapped at 80 columns; code blocks wrap at 120.
   Every new test function and module carries a docstring
   (`interrogate --fail-under 100` covers `tests/`).
10. Every commit passes `make check-fmt`, `make typecheck`, `make lint`,
    `make test`, `make markdownlint`, and `make nixie`, run sequentially.

## Tolerances (exception triggers)

Stop, record the situation in `Decision log`, and escalate when any of these is
reached.

1. Scope: more than 12 files touched, or any file under `syrupy_mdast/`.
2. Wenmode release drift: PyPI publishes a Wenmode release newer than 0.15.1
   before ADR-003 is accepted. Re-run the probe (see `Concrete steps`) against
   the new release, record the differences, and ask the maintainer which
   release to pin. Do not silently switch.
3. Evidence drift: re-running the probe against 0.15.1 produces any output that
   differs from the transcript in `Artefacts and notes`. Stop: the evidence the
   ADR rests on is wrong.
4. Acceptance: the maintainer requests changes that alter a decision recorded
   in `Decision log` (DEC-4 to DEC-12). Revise this plan first, then the ADR.
5. Roadmap: this plan authorizes exactly three roadmap edits (DEC-3): the
   `github()` wording in tasks 1.2.2 and 2.1.1, and ticking 1.1.2. Any further
   roadmap amendment triggers escalation.
6. Dependencies: any need for a new package, including `pytest-bdd`, triggers
   escalation.
7. Iterations: a single gate still failing after three remediation attempts.
8. Ambiguity: a design passage that conflicts with the ADR in a way not already
   resolved in `Decision log`.

## Risks

1. Risk: Wenmode is beta software; a later release changes AST output for
   inputs outside the corpus, and an "empty corpus diff" upgrade silently
   changes users' payloads. Severity: high. Likelihood: medium — 0.15.1, a
   patch release, changed list tightness and autolink boundaries. Mitigation:
   the ADR's upgrade policy (DEC-9) classifies every Wenmode changelog entry,
   not only the corpus diff, and requires a fixture for every
   behaviour-changing entry before the pin moves.
2. Risk: Dependabot's grouped minor-and-patch pip updates (see
   `.github/dependabot.yml` and `docs/developers-guide.md` §"Dependabot
   policy") bundle a Wenmode bump with routine updates once Wenmode is a
   dependency. Severity: medium. Likelihood: high. Mitigation: the ADR requires
   Wenmode changes to land alone; roadmap 1.2.1 implements the Dependabot
   exclusion. This plan only records the requirement.
3. Risk: the ratified behaviour includes a Wenmode divergence from the GFM
   specification (type-1 HTML blocks are not tag-filtered; Surprise 5). A
   future Wenmode fix changes payloads. Severity: medium. Likelihood: medium.
   Mitigation: the ADR records the divergence as ratified-but-known, names the
   fixture that freezes it, and classifies an upstream fix as a contract
   change. A draft upstream report is prepared; filing it requires maintainer
   authorization because it publishes to an external service.
4. Risk: the maintainer rejects DEC-8 (no in-payload version marker) or DEC-7
   (no text-node merging) during acceptance. Severity: low. Likelihood: medium.
   Mitigation: both are presented as options with trade-offs in the ADR; a
   rejection is a tolerance-4 escalation, not a surprise.
5. Risk: the documentation contract test becomes a brittle Markdown scraper
   that fails on harmless edits. Severity: medium. Likelihood: medium.
   Mitigation: parse only one fenced `toml` block under a fixed heading and the
   `## Status` paragraph; assert semantics (parsed TOML values), never line
   numbers or wording.
6. Risk: `make fmt` (`mdtablefix --wrap --renumber`) rewraps the manifest code
   block or renumbers lists in the ADR. Severity: low. Likelihood: low —
   `--fences` normalizes fences but does not rewrap code. Mitigation: run
   `make fmt` before the red test run so any rewrite is caught by the test.

## Progress

- [x] (2026-09-27T00:00Z) Branch renamed to
  `1-1-2-record-parser-and-snapshot-version-policy`, tracking origin.
- [x] (2026-09-27) Reconnaissance: repository, documentation conventions, and
  1.1.1 handoff obligations surveyed.
- [x] (2026-09-27) External research: Wenmode 0.15.1 release, presets, security
  policy, node shape contract, changelog; GFM tag filter; Syrupy 6.0.0
  single-file and amber versioning internals.
- [x] (2026-09-27) Empirical probe of Wenmode 0.15.1's GitHub profile
  (transcript in `Artefacts and notes`).
- [x] (2026-09-27) ExecPlan drafted.
- [ ] Expert-panel design review and revision of this plan.
- [ ] Maintainer approval of this ExecPlan.
- [ ] EP-M1: ADR-003 drafted as `Proposed` and indexed.
- [ ] EP-M2: ADR-003 accepted by the maintainer.
- [ ] EP-M3: documentation contract tests red, then design, roadmap, and
  guides reconciled so they pass.
- [ ] EP-M4: full gate sweep, roadmap tick, retrospective.

## Surprises & discoveries

1. Observation: the design's parser construction is deprecated. Evidence:
   Wenmode 0.15.0 changed `commonmark`, `github`, and `streaming` into preset
   factory functions; `Parser(github, positions=False)` emits
   `DeprecationWarning: Passing github without calling it is deprecated and
   will be removed in 1.0; use github() instead.`
   (probe transcript). Impact: the ADR fixes
   `Parser(github(), positions=False)`; design §7 and roadmap tasks 1.2.2 and
   2.1.1 are amended (DEC-3, DEC-5).
2. Observation: Wenmode preserves CR and CRLF inside string values. Evidence:
   `"a\r\nb\r\n"` parses to a text node `"a\r\nb"`; a CRLF fenced code block
   yields `"x\r\n"`; a CRLF link title is kept. Structure (paragraph splits,
   hard breaks) is identical across LF, CRLF, and CR. Impact: design §8 rule 3
   is load-bearing, not defensive; line-ending equivalence depends on it.
3. Observation: `null` appears inside arrays. Evidence: a table with
   unspecified column alignment yields `"align": [null, "center", null]`.
   Wenmode omits `None`-valued *members* but not `None` array *elements*.
   Impact: the ADR must say that omitted members stay omitted and `null` array
   elements are preserved; the JSON value domain includes `null`.
4. Observation: entity references and backslash escapes split text nodes.
   Evidence: `"&amp; &copy;"` yields three text nodes `"&"`, `" "`, `"©"`;
   `"\\*x\\*"` yields `"*"`, `"x"`, `"*"`. Impact: without a merge rule,
   `a & b` and `a &amp; b` produce different payloads. The ADR decides this
   explicitly (DEC-7).
5. Observation: Wenmode's GitHub tag filter does not cover HTML blocks that
   start with `<script`, `<style>`, or `<textarea>` (CommonMark HTML block type
   1), although GFM spec 0.29-gfm §6.11 applies the filter to raw HTML blocks
   as well as inline HTML. Evidence: `<script>…</script>` and
   `<style>…</style>` blocks are emitted unchanged with no `data`; an
   `<iframe>` block and inline `<script>` are rewritten to `&lt;…` with
   `data: {"escaped": true}`. Impact: ratified as observed, recorded as a known
   divergence (Risk 3, DEC-11).
6. Observation: footnote definitions stay where the source puts them, unused
   definitions are retained, undefined references remain literal text, and
   labels are case-folded. Evidence: a definition before its reference is
   emitted first; `x\n\n[^u]: unused` keeps the definition; `x[^missing]` is
   text; `[^A]` yields `identifier` and `label` `"a"`. Impact: moving a
   footnote definition changes the payload; label case does not. Both are
   recorded as normative fixture decisions (DEC-11).
7. Observation: Wenmode exports no documented parse exception; `dir(wenmode)`
   contains only `StreamingUnsupportedError`. Impact: out of scope here, but
   design §9's `parse` category may have no documented Wenmode trigger. Handed
   to roadmap task 2.2.2 via `Outcomes & retrospective`.
8. Observation: Syrupy 6.0.0 writes single-file text snapshots with
   `open(path, "wt", encoding=...)` and no `newline` argument, so on Windows
   the written bytes use CRLF, and reads use universal newlines. Evidence:
   `syrupy/extensions/single_file.py`, `write_snapshot_collection` and
   `read_snapshot_data_from_location`. Impact: the ADR's byte contract governs
   the serialized string handed to Syrupy, not on-disk line terminators;
   roadmap task 2.3.1 must decide whether to force `\n` on disk.
9. Observation: Syrupy already has a snapshot-versioning precedent. Evidence:
   the amber serializer writes a `# serializer version: 1` header and marks
   snapshots with a mismatched version as tainted, which fails the assertion
   with `TaintedSnapshotError`; `SingleFileSnapshotExtension` has no header and
   no taint source. Impact: informs DEC-8's options.
10. Observation: `docs/repository-layout.md`, cited by `AGENTS.md`, does not
    exist. Impact: none on this task; recorded, not fixed (out of scope).
11. Observation: `make fmt` rewrites `docs/roadmap.md` on the untouched tree:
    `mdtablefix` deletes the unused `[issue-23]` link definition at the end of
    the file, leaving two trailing blank lines that `markdownlint-cli2` then
    reports as MD012, so `make fmt` exits non-zero. Evidence:
    `/tmp/fmt-syrupy-mdast-1-1-2-record-parser-and-snapshot-version-policy.out`
    during planning; the roadmap change was reverted. Impact: EP-M3 edits the
    roadmap. Either leave the roadmap's tail untouched and revert the
    `make fmt` side effect, or, if the maintainer agrees, remove the unused
    definition deliberately in its own commit. Do not let the side effect ride
    along unreviewed.

## Decision log

- DEC-1. Decision: the ADR is
  `docs/adr-003-parser-profile-and-snapshot-version-policy.md`, titled
  "Architectural decision record (ADR) 003: Snapshot contract v1 — parser
  profile and snapshot-version policy". Rationale: next free sequence number;
  the style guide's naming pattern. Date/Author: 2026-09-27, planning agent.
- DEC-2. Decision: "explicitly versioned" means the ADR declares an integer
  **snapshot contract version**, starting at `1`, inside a machine-readable
  manifest, plus the style guide's `Status` and `Date`. Each contract version
  has its own ADR; a new contract version supersedes the previous ADR rather
  than editing it. Changes that cannot alter any payload (editorial
  clarifications, a Wenmode pin move classified as payload-neutral under DEC-9)
  are recorded as dated amendments to the current ADR. Rationale: accepted ADRs
  are records; superseding keeps each contract version's definition immutable
  and citable. Date/Author: 2026-09-27, planning agent.
- DEC-3. Decision: this plan amends the roadmap three times: tasks 1.2.2 and
  2.1.1 replace `Parser(github, positions=False)` with
  `Parser(github(), positions=False)`, and task 1.1.2 is ticked at the end.
  Rationale: the old wording prescribes a deprecated call (Surprise 1); leaving
  it would make the roadmap contradict an accepted ADR. Date/Author:
  2026-09-27, planning agent.
- DEC-4. Decision: pin `wenmode==0.15.1`. Rationale: latest release
  (2026-09-11); 0.15.0 introduced the preset factories the ADR relies on, and
  0.15.1 fixes list tightness and extended-autolink boundaries, so choosing
  0.15.0 would schedule a known payload migration immediately. Licence
  BSD-3-Clause; pure-Python `py3-none-any` wheel; requires Python 3.10 or
  later, compatible with this package's 3.12 floor. Wheel SHA-256
  `d25b2adc75ff897640c1e28178f647631da0e03084e498a765f007844a3c340d`.
  Date/Author: 2026-09-27, planning agent.
- DEC-5. Decision: the v1 parser construction is exactly
  `Parser(github(), positions=False).parse(source).to_ast()`, with a fresh
  `Parser` per call, no plugins, no `create_preset`, and no rule registration.
  This supersedes the construction in design §7. Rationale: Surprise 1; the
  per-call rule is unchanged from design §3 and §10. Date/Author: 2026-09-27,
  planning agent.
- DEC-6. Decision: the normalization policy is design §8's four rules, applied
  recursively at every depth including inside `data`, and nothing else. The
  preferred key order is the 17-element sequence `type`, `depth`, `ordered`,
  `start`, `spread`, `checked`, `align`, `lang`, `meta`, `url`, `title`, `alt`,
  `identifier`, `label`, `value`, `data`, `children`; members not in the
  sequence follow, ordered by Unicode code point. Rationale: the sequence
  covers every field in Wenmode's documented shape contract for the node types
  the GitHub profile emits (grouped as design §8 prescribes: type, structural
  scalars, link and footnote fields, value, data, children), and fixing it in
  the ADR makes the snapshot bytes fully determined by the ADR plus Wenmode.
  `position` is absent because rule 1 removes it. Date/Author: 2026-09-27,
  planning agent.
- DEC-7. Decision (recommended; confirm at acceptance): v1 does **not** merge
  adjacent text nodes, apply Unicode normalization, or rewrite entity and
  escape spellings. `a & b` and `a &amp; b` are distinct payloads. Rationale:
  the design's contract applies "only these transformations"; a merge rule
  makes the canonicalizer schema-aware (it must know which node types are
  literal text and how to combine `data`), and a spurious diff is a safer
  failure than a false equality. Merging remains a candidate named policy for
  roadmap 4.2.1 and would be a new contract version. Date/Author: 2026-09-27,
  planning agent.
- DEC-8. Decision (recommended; confirm at acceptance): the payload carries no
  version marker, and the file suffix stays `.mdast.json`. Contract changes
  surface as ordinary Syrupy diffs of the affected snapshots, explained by
  release notes. Rationale: design §8's payload is the canonical tree alone; an
  in-payload or in-filename marker forces every snapshot to change at every
  contract bump even when its tree is unchanged, which is exactly the
  broad-update noise design §1 exists to remove. Syrupy's amber taint header is
  the strongest alternative and is recorded with reconsideration criteria.
  Date/Author: 2026-09-27, planning agent.
- DEC-9. Decision: snapshot-version policy. Patch releases never change
  canonical payloads. A contract-version increment requires, before 1.0.0, a
  minor release (`0.y.z` to `0.(y+1).0`), and from 1.0.0 onwards a major
  release; either way with release notes listing affected constructs and the
  `pytest --snapshot-update` migration step. A Wenmode pin change lands alone
  in a dedicated pull request carrying the upgrade report (roadmap 3.2.1); it
  is payload-neutral only if the corpus diff is empty **and** every Wenmode
  changelog entry between the two releases is classified as not affecting the
  GitHub profile's `to_ast()` output, or is covered by a fixture that shows no
  change. Otherwise it is a contract change. Rationale: design §13 with the
  pre-1.0 case made explicit (the package is `0.1.0`) and Risk 1 closed.
  Date/Author: 2026-09-27, planning agent.
- DEC-10. Decision: the canonical JSON writer for contract v1 is exactly
  `json.dumps(tree, ensure_ascii=False, indent=2, allow_nan=False) + "\n"`,
  encoded as UTF-8 without a byte-order mark, over the value domain: mappings
  with string keys, lists, strings, integers, booleans, and `null`. Any other
  value is an `ast-shape` failure (design §9). The contract governs the string
  handed to Syrupy; on-disk line terminators are Syrupy's text-mode I/O
  (Surprise 8). Rationale: naming the reference call pins separators, escape
  spelling, and key-order preservation without re-specifying JSON. Date/Author:
  2026-09-27, planning agent.
- DEC-11. Decision: the normative fixture decisions are those listed under
  `Interfaces and dependencies` → "ADR-003 normative fixture decisions" (NF-1
  to NF-12). The contract corpus (roadmap 1.1.3) is the lasting oracle; every
  fixture cites the NF identifier it discharges; an optional
  `mdast-util-from-markdown` differential run stays unshipped and outside CI.
  Rationale: design §11; each NF is grounded in the probe transcript.
  Date/Author: 2026-09-27, planning agent.
- DEC-12. Decision: no pytest-bdd scenarios, no syrupy snapshots, no
  end-to-end tests, and no Rust or Verus proof in this task. Rationale: the
  task changes documents, not behaviour a user can exercise; pytest-bdd is not
  a dependency (Constraint 4); snapshots and fixtures are forbidden before
  acceptance (Constraint 3); a Rust extension would breach the Python-only
  wheel (Constraint 8). The executable evidence is the documentation contract
  test plus one Hypothesis property (see `Verification plan`). The first
  obligations that merit formal methods are roadmap 2.1.2's canonicalization
  invariants, where CrossHair over the pure canonicalizer is the proportionate
  tool. Date/Author: 2026-09-27, planning agent.

## Outcomes & retrospective

Not started. Record here, at completion: what was achieved against the purpose;
handoffs (Surprise 7 to roadmap 2.2.2, Surprise 8 to 2.3.1, the Dependabot
exclusion to 1.2.1, the key-coverage probe to 1.2.3); and any upstream-document
change made.

## Context and orientation

This repository is a Python library (`hatchling`, `uv`, Python 3.12 or later)
that will become a Syrupy extension. **Syrupy** is a pytest snapshot plugin: a
test compares a value with a stored file and Syrupy creates, updates, and
deletes those files. **mdast** is the Markdown Abstract Syntax Tree format used
by the unified ecosystem. **Wenmode** is a pure-Python Markdown parser whose
`to_ast()` emits mdast-compatible dictionaries; its **GitHub profile** (the
`github` preset) is CommonMark plus GitHub Flavoured Markdown (GFM) tables,
strikethrough, task lists, extended autolinks, footnotes, and GitHub's
disallowed-HTML tag filter. An **ADR** (architectural decision record) is a
dated document recording one decision and its rationale.

A **snapshot payload** is the exact text written for one assertion. The
**snapshot contract** is everything that determines that text for a given
Markdown input. Its **contract version** is the integer this task introduces.

Current state:

1. `syrupy_mdast/` holds the v1 public surface from roadmap 1.1.1:
   `MarkdownAstError` (in `syrupy_mdast/_core/errors.py`) and
   `MarkdownAstSnapshotExtension` (in `syrupy_mdast/_extension.py`), whose
   `serialize()` raises `NotImplementedError` naming roadmap 2.3.1. It is not
   touched by this task.
2. `docs/syrupy-mdast-design.md` (revision dated 2026-07-28) defines the
   contract in §§4, 7, 8, 11, and 13. §11 requires this ADR.
3. `docs/adr-001-python-lint-architecture.md` and
   `docs/adr-002-main-owns-codescene-coverage-publication.md` exist. Neither
   follows the style-guide template exactly; ADR-003 must.
4. `docs/contents.md` indexes documents under "Decision records".
5. `tests/` contains infrastructure contract tests. None reads `docs/`; the
   documentation contract test introduced here is a new pattern, modelled on
   `tests/test_toolchain_contract.py` (parse, then compare semantics across
   sites, with messages that name both sites). `tests/support/` holds shared
   helpers.
6. `make fmt` rewrites Markdown with `mdtablefix` and `markdownlint-cli2 --fix`;
   `make check-fmt` checks Ruff formatting and `mdtablefix`;
   `make markdownlint` and `make nixie` are separate Markdown gates.

### Signposted reading

Read these, in this order, before editing:

1. `docs/roadmap.md` task 1.1.2 and its dependants 1.1.3, 1.2.1-1.2.3, 2.1.1,
   2.1.2, 3.2.1 — so the ADR fixes what they need and nothing they own.
2. `docs/syrupy-mdast-design.md` §§3-4, 7-8, 11, 13, 15 — the contract being
   ratified. §§9-10 only for the failure taxonomy and concurrency rule the ADR
   cites but does not change.
3. `docs/documentation-style-guide.md` §"Architectural decision records
   (ADRs)" — the template ADR-003 must follow verbatim — plus the spelling,
   footnote, and table-caption rules.
4. `docs/execplans/1-1-1-replace-package-stub-with-v1-public-contract.md` DEC-13
   and `Conformance basis` — the template handoff obligation.
5. `docs/adr-002-main-owns-codescene-coverage-publication.md` — house tone.
6. `tests/test_toolchain_contract.py` and `tests/support/make_contract.py` —
   the cross-site contract-test pattern and `REPO_ROOT`.
7. `.rules/python-00.md`, `.rules/python-typing.md` — test-module style; note
   `import typing as typ` (bare `from typing import …` is banned by Ruff's
   import conventions in `pyproject.toml`).
8. `docs/developers-guide.md` §"Maintain syrupy-mdast" and §"Dependabot policy".
9. `AGENTS.md` — gates, commit rules, Markdown rules.

Relevant skills: `execplans` (this plan), `en-gb-oxendict` (all prose),
`python-router` then `python-testing` (contract-test structure) and
`hypothesis` (the one property), `firecrawl-mcp` (re-verifying Wenmode's latest
release at EP-M1 and EP-M2), `commit-message`, and `pr-creation`.

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
   version), §15 (risks). Design §preamble: accepted ADRs take precedence.
2. `docs/roadmap.md` task 1.1.2, amended per DEC-3.
3. Governing standards: `AGENTS.md`, `docs/documentation-style-guide.md`,
   `.rules/python-*.md`.
4. Handoff: 1.1.1 ExecPlan DEC-13 (template conformance).

Deviations from the design, all recorded in the ADR and reconciled into the
design at EP-M3: DEC-5 (preset factory call), DEC-6 (exact key order fixed in
the ADR rather than left to an implementation constant), DEC-9 (pre-1.0 mapping
and changelog classification), DEC-10 (exact writer call and on-disk boundary).
None changes the public API, dependency set, or trust boundary.

Trace links:

```plaintext
TDD-§11 -> RM-1.1.2 -> EP-M1,EP-M2 -> tests/test_snapshot_contract_adr.py::test_adr_is_accepted
TDD-§11 -> RM-1.1.2 -> EP-M1       -> tests/test_snapshot_contract_adr.py::test_manifest_declares_contract_version_one
TDD-§7  -> RM-1.1.2 -> EP-M3       -> tests/test_snapshot_contract_adr.py::test_design_parser_construction_matches_adr
TDD-§7  -> RM-1.1.2 -> EP-M3       -> tests/test_snapshot_contract_adr.py::test_no_document_prescribes_the_uncalled_preset
TDD-§8  -> RM-1.1.2 -> EP-M3       -> tests/test_snapshot_contract_adr.py::test_key_order_is_framed_and_duplicate_free
TDD-§13 -> RM-1.1.2 -> EP-M3       -> tests/test_snapshot_contract_adr.py::test_pyproject_wenmode_declaration_agrees_with_adr
TDD-§13 -> RM-1.2.1 -> EP-M3       -> tests/test_snapshot_contract_adr.py::test_wenmode_declaration_rejects_any_other_version
TDD-§11 -> RM-1.1.3 -> EP-M1       -> docs/adr-003-…md NF-1..NF-12 (consumed by the 1.1.3 corpus)
```

## Verification plan

This task introduces documents and a documentation contract test. It introduces
no production invariant. The obligations below are over documents and over one
small test-support function; each states why it can fail.

### Axioms

1. Wenmode 0.15.1's documented shape contract: every node has a string `type`;
   `None`-valued fields are omitted by `to_ast()`; `False`, empty lists, and
   empty strings are preserved; the per-type field table in Wenmode's "Node
   model" reference. Cross-checked by the probe; not re-verified by tests here
   (roadmap 1.2.3 owns executable probes).
2. Wenmode's compatibility page states that `Node.to_ast()` output for
   documented node types is intended to be stable through the beta, while
   edge-case parsing may change. DEC-9 is built on the second clause.
3. CPython's `json.dumps` with fixed arguments produces deterministic output
   for the declared value domain, preserving insertion order of mapping keys.
4. `packaging.requirements.Requirement` parses PEP 508 strings and normalizes
   project names per PEP 503. Available at 26.3 through `pytest`.
5. PyPI's recorded SHA-256 for `wenmode-0.15.1-py3-none-any.whl` is as quoted
   in DEC-4 (retrieved 2026-09-27; re-check at EP-M1).

### Obligations

**DOC-1 — Acceptance precedes dependent work.** Statement: ADR-003's status is
`Accepted`, and the commit that set it precedes every commit adding the
contract test or reconciling other documents. Method: explicit test for the
status, plus a recorded `git log` ordering check at EP-M4 (process evidence,
not a test: history is not a runtime property). Artefact:
`tests/test_snapshot_contract_adr.py::test_adr_is_accepted`. Evidence: the test
is written after EP-M2, so it cannot be red against the tree; the red evidence
is the negative control. Non-vacuity: the test asserts the `## Status` section
exists and is non-empty before comparing its first word, so a renamed heading
fails rather than passes. Negative control: set the status word to `Proposed`
in a scratch copy passed through the same parser; the test's helper must report
`Proposed`.

**DOC-2 — Manifest completeness and typing.** Statement: the ADR contains
exactly one fenced `toml` block under the heading `### Contract manifest`; it
parses to a `[snapshot-contract]` table whose keys are exactly
`contract-version` (integer, equal to `1`), `wenmode` (string matching
`==MAJOR.MINOR.PATCH`), `parser` (string), `file-extension` (`"mdast.json"`),
`key-order` (list of strings), and `json-writer` (string). Method: explicit
assertions on the parsed TOML. Rationale: a fixed, finite shape; enumeration is
exhaustive. Artefact:
`tests/test_snapshot_contract_adr.py::test_manifest_declares_contract_version_one`.
Evidence: red before EP-M1's ADR exists (`FileNotFoundError` surfaced as an
assertion naming the path); green after. Non-vacuity: assert the key set
equality (not subset), so an added or missing key fails; the extractor asserts
exactly one matching block, so a duplicated manifest fails.

**DOC-3 — Key order is well formed.** Statement: `key-order` has no duplicates,
starts with `type`, ends with `children`, places `value` before `data` before
`children`, and omits `position`. Method: explicit assertions. Rationale: these
are the design §8 grouping rules; the exact membership is fixed by the ADR text
and is not restated in the test (that would be a tautology). Artefact:
`tests/test_snapshot_contract_adr.py::test_key_order_is_framed_and_duplicate_free`.
Non-vacuity: assert the list is non-empty and longer than two. Negative
control: the unit tests feed a hand-written list with `position` and with a
duplicate to the same checking helper and expect both rejected. Residual gap:
whether the sequence covers every key Wenmode actually emits is verified by
roadmap 1.2.3's probe over the corpus, which needs the Wenmode dependency.

**DOC-4 — Parser construction agrees across documents.** Statement: the
manifest's `parser` string appears verbatim inside a fenced `python` block in
design §7, and no Markdown file under `docs/` other than ADR-003 itself (which
quotes it as the rejected form) and this ExecPlan contains the uncalled form
`Parser(github,`. Method: explicit test over file text. Rationale: this is the
drift the ADR was partly written to stop (Surprise 1). Artefacts:
`test_design_parser_construction_matches_adr` and
`test_no_document_prescribes_the_uncalled_preset`. Evidence: both red at the
start of EP-M3 (design §7 and roadmap 1.2.2/2.1.1 still use the uncalled form);
green after the reconciliation edits. Non-vacuity: assert the design contains
at least one `python` fence under a heading containing "Parser profile", and
that the scanned file set is non-empty and includes `docs/roadmap.md`.

**DOC-5 — Wenmode declaration agrees with the ADR pin.** Statement: in
`pyproject.toml`, across `[project] dependencies` and every dependency group,
`wenmode` is either absent, or declared exactly once as `wenmode==<pin>` with
the manifest's pin, with no extras and no environment marker. Method: a pure
helper
`wenmode_declaration_problem(requirements: cabc.Sequence[str],
pinned_version: str) -> str | None`
in `tests/support/adr_contract.py`, exercised three ways: (a) against the real
`pyproject.toml` (`test_pyproject_wenmode_declaration_agrees_with_adr`); (b) a
parameterized table of named cases: absent, exact match, non-canonical name
spelling (`Wenmode == 0.15.1`, accepted after PEP 503 normalization), range
(`wenmode>=0.15.1`), compatible release (`wenmode~=0.15.1`), different version,
arbitrary equality (`wenmode===0.15.1`), extras, marker, and duplicate
declarations, each asserting the problem text names the defect; (c) one
Hypothesis property, `test_wenmode_declaration_rejects_any_other_version`: for
any generated `MAJOR.MINOR.PATCH` distinct from the pin, `wenmode==<generated>`
is reported as a problem. Rationale: the table covers the finite operator and
shape classes; the property covers the open version space, and specifically
catches a prefix-comparison bug (`0.15.1` versus `0.15.10`), which a small
table is likely to miss. Domain for (c): integer triples in `0..=99` each,
filtered to differ from the pin, with `hypothesis.event` recording whether the
generated version shares the pin as a string prefix; assert with
`hypothesis.target` or a follow-up explicit example that the prefix class is
reached. Evidence: (b) and (c) are red against a stub returning `None`; green
after the helper is implemented. (a) is green while `wenmode` is absent and
becomes live at roadmap 1.2.1, when the pin is added. Non-vacuity: (a) is not
vacuous at 1.2.1 because (b) proves the helper rejects every wrong form; the
explicit example `wenmode==0.15.10` is added as a named regression case in (b).

**DOC-6 — The ADR is discoverable.** Statement: `docs/contents.md` links
ADR-003 under "Decision records"; design §§7, 8, and 13 link ADR-003. Method:
explicit link-target assertions. Artefact:
`test_adr_is_indexed_and_cited_by_the_design`. Evidence: red at the start of
EP-M3 for the design links; green after.

**EV-1 — Empirical grounding of NF-1 to NF-12.** Statement: each normative
fixture decision matches the observed output of Wenmode 0.15.1's GitHub
profile. Method: the reproducible probe script (see `Artefacts and notes`) run
in a throwaway environment at EP-M1 and again immediately before EP-M2.
Rationale: executable probes committed to the repository need the Wenmode
dependency and belong to roadmap 1.2.3; here the evidence is a transcript that
any reviewer can regenerate with one command. Non-vacuity: the probe includes
negative witnesses for each equivalence (the unresolved reference, the
undefined footnote, the escaped and unescaped HTML tags) so that "everything is
equal" or "nothing is equal" outcomes are visibly wrong. Discharge: transcript
identical to the recorded one (Tolerance 3).

No introduced invariant warrants CrossHair, a bounded model checker, or a
formal prover: the only executable logic is `wenmode_declaration_problem`,
whose domain is covered by DOC-5's table and property. A Verus proof would
require a Rust extension, which Constraint 8 forbids.

## Plan of work

Stage A — orientation (no edits). Read the signposted material. Run the full
gate set on the untouched tree and keep the logs. Re-run the Wenmode probe and
compare with the transcript. Check PyPI for a release newer than 0.15.1.

Stage B — ADR drafting (EP-M1). Write ADR-003 as `Proposed`, following the
template headings verbatim. Index it in `docs/contents.md`. Commit.

Stage C — acceptance gate (EP-M2). Request maintainer acceptance of the written
ADR. On acceptance, set `Accepted` with the date and a one-sentence summary.
Commit. Do not proceed without it.

Stage D — guard and reconcile (EP-M3). Write the documentation contract tests
and observe them fail for the expected reasons; then reconcile the design,
roadmap, users' guide, and developers' guide until they pass. Commit.

Stage E — sweep (EP-M4). Run every gate, tick roadmap 1.1.2, complete the
retrospective, set this plan to `COMPLETE`. Commit.

## Milestones and plateaus

### EP-M1 — ADR-003 drafted as Proposed

- Outcome: `docs/adr-003-parser-profile-and-snapshot-version-policy.md` exists
  with status `Proposed`, and `docs/contents.md` lists it. Nothing else
  changes. A proposed ADR is a record of a proposal; committing it does not
  pre-empt acceptance.
- Content, in the template's order (headings verbatim from the style guide):
  1. `## Status` — `Proposed.`
  2. `## Date` — the drafting date.
  3. `## Context and problem statement` — why the snapshot contract needs one
     versioned record; what design §11 requires; what was open (release,
     version identifier, key order, observed behaviour).
  4. `## Decision Drivers` — reviewability (design §1), determinism across
     platforms, Wenmode beta churn, Python-only boundary, conservative
     equivalence.
  5. `## Requirements` with `### Functional requirements` and
     `### Technical requirements`.
  6. `## Options considered` — `### Option A: No payload version marker`,
     `### Option B: In-payload version member`, `### Option C: Versioned file
     suffix`, `### Option D: Amber-style header with taint`, and separately
     `### Option E: Merge adjacent text nodes` versus retaining segmentation,
     with a captioned comparison table for A-D.
  7. `## Decision outcome / proposed direction`, containing, in order:
     `### Contract manifest` (the single fenced `toml` block, see `Interfaces
     and dependencies`), `### Parser profile` (DEC-5), `### Wenmode release`
     (DEC-4, including licence and wheel hash), `### Normalization policy`
     (DEC-6, DEC-7), `### Canonical JSON writer` (DEC-10), `### Comparison
     contract` (design §4, refined: equivalence is byte-identical payloads
     under the same contract version), `### Snapshot-version policy` (DEC-2,
     DEC-8, DEC-9), `### Normative fixture decisions` (NF-1 to NF-12 with
     observed outputs), and `### Evidence` (the one-line probe reproduction
     command and the probe date).
  8. `## Goals and non-goals` — non-goals copied from design §2.2 plus
     unified byte compatibility and on-disk line terminators.
  9. `## Migration plan` — numbered phases mapping to roadmap 1.1.3, 1.2.1
     (pin and Dependabot exclusion), 1.2.3 (probes, key coverage), 2.1.2
     (canonicalizer constant equals manifest), 3.2.1 (upgrade report
     implements DEC-9).
  10. `## Known risks and limitations` — Risks 1-3, Surprise 8, and the text
      segmentation consequence.
  11. `## Outstanding decisions` — while `Proposed`: DEC-7 and DEC-8
      confirmation; whether to file the upstream report (Surprise 5). Emptied
      (or each item marked resolved) at acceptance.
- Acceptance evidence: `make markdownlint`, `make nixie`, `make check-fmt`
  pass; manual check that every heading matches the template.
- Conformance check: design sections cited; no file outside the ADR and
  `docs/contents.md` changed.
- Recovery: the ADR is a new file; revert the commit to retry.
- Remaining gaps: acceptance; reconciliation; tests.
- Compatibility decision: none.

### EP-M2 — ADR-003 accepted

- Outcome: the ADR's status reads
  `Accepted (YYYY-MM-DD): <one-sentence summary>`, per the style guide, and
  `## Outstanding decisions` records how each item was resolved.
- Procedure: push the EP-M1 commit; ask the maintainer, in the pull request
  and in the session, to accept ADR-003 or request changes. Quote the two
  recommended decisions (DEC-7, DEC-8) in the request. Set this plan's status to
  `BLOCKED` while waiting. On requested changes, revise this plan's
  `Decision log` first (Tolerance 4), then the ADR, then ask again.
- Acceptance evidence: a maintainer message explicitly accepting ADR-003,
  quoted with its date in `Decision log`; the acceptance commit.
- Conformance check: the accepted text equals the text the maintainer reviewed
  (no edits between the request and the status change other than the status
  itself and resolved outstanding decisions).
- Recovery: if acceptance is withdrawn, revert the status commit.
- Compatibility decision: none.

### EP-M3 — Guard, then reconcile

- Outcome: the documentation contract test passes, and every upstream document
  agrees with ADR-003.
- Red: add `tests/support/adr_contract.py` with the extraction helpers and a
  stub `wenmode_declaration_problem` that returns `None`, and add
  `tests/test_snapshot_contract_adr.py`. Run
  `uv run pytest -v tests/test_snapshot_contract_adr.py`. Expected failures:
  the DOC-5 table and property (stub accepts everything), DOC-4 (design §7 and
  roadmap still say `Parser(github,`), DOC-6 (design does not link ADR-003).
  DOC-1, DOC-2, DOC-3, and DOC-5(a) already pass; that is expected and is why
  their negative controls exist.
- Green: implement `wenmode_declaration_problem`. Then edit:
  1. `docs/syrupy-mdast-design.md` — §7 code block and prose to
     `github()`; §§4, 7, 8, 13 cite ADR-003; §8 records the exact key order by
     reference to the ADR, the `null`-element rule, the no-merge rule, and the
     CR evidence; §11 replaces "An explicitly versioned ADR records…" with a
     link to ADR-003 as that record; §13 adds the pre-1.0 mapping and the
     changelog-classification rule; §15 adds the GFM divergence; references
     gain the Wenmode node-model, changelog, and GFM spec footnotes; "Last
     updated" moves to the reconciliation date.
  2. `docs/roadmap.md` — tasks 1.2.2 and 2.1.1 wording (DEC-3).
  3. `docs/users-guide.md` — new section `## Snapshot contract and upgrades`:
     contract version 1 and ADR-003; what compares equal and what does not
     (including entity/escape spelling and footnote placement); that patch
     releases never change payloads; what a contract-version change looks like
     and the review-then-`pytest --snapshot-update` step; stated as the
     contract serialization will implement, since `serialize()` still raises
     `NotImplementedError`.
  4. `docs/developers-guide.md` — §"Upgrade Wenmode" rewritten to cite ADR-003
     and DEC-9 (dedicated pull request, corpus diff plus changelog
     classification, contract-version decision, ADR amendment or superseding
     ADR); a short "Snapshot contract ADR" paragraph describing the manifest
     and `tests/test_snapshot_contract_adr.py` as the guard, and the rule that
     code constants introduced later (key order, pin) must be added to that
     test's cross-checks.
- Acceptance evidence: focused test green; then all gates green.
- Conformance check: every deviation listed in `Conformance basis` is now in
  the design text; no production file touched.
- Recovery: tests and documentation are independent files; revert per file.
- Remaining gaps: roadmap tick and retrospective.
- Compatibility decision: none.

### EP-M4 — Sweep and close

- Outcome: all gates pass; roadmap 1.1.2 ticked; this plan `COMPLETE` with a
  retrospective and handoffs.
- Acceptance evidence: gate logs, and the following command shows the
  acceptance commit before the test commit (DOC-1):

  ```bash
  git log --format='%h %s' -- docs/adr-003-parser-profile-and-snapshot-version-policy.md \
    tests/test_snapshot_contract_adr.py
  ```

- Recovery: documentation-only commit; revert to retry.

## Concrete steps

Run everything from the repository root:
`/home/leynos/.lody/repos/github---leynos---syrupy-mdast/worktrees/<worktree>`
(any checkout of branch `1-1-2-record-parser-and-snapshot-version-policy`). Run
gates sequentially, never in parallel, each through `tee`:

```bash
BR=$(git branch --show-current)
make check-fmt 2>&1 | tee /tmp/check-fmt-syrupy-mdast-$BR.out
make typecheck 2>&1 | tee /tmp/typecheck-syrupy-mdast-$BR.out
make lint 2>&1 | tee /tmp/lint-syrupy-mdast-$BR.out
make test 2>&1 | tee /tmp/test-syrupy-mdast-$BR.out
make markdownlint 2>&1 | tee /tmp/markdownlint-syrupy-mdast-$BR.out
make nixie 2>&1 | tee /tmp/nixie-syrupy-mdast-$BR.out
```

Re-verify the Wenmode evidence (Stage A, EP-M1, and before EP-M2). The script
is reproduced in `Artefacts and notes`; save it as
`/tmp/wenmode-probe/probe.py`:

```bash
mkdir -p /tmp/wenmode-probe
cd /tmp/wenmode-probe && uv run --no-project --with wenmode==0.15.1 python probe.py > out.txt 2>&1
```

Expected: the first lines read `version 0.15.1` and the per-case outputs match
the transcript. Then check for newer releases with the `firecrawl-mcp` skill
(scrape `https://pypi.org/project/wenmode/#history`); Tolerance 2 applies if
one exists.

Focused test loop during EP-M3:

```bash
uv run pytest -v tests/test_snapshot_contract_adr.py 2>&1 | tee /tmp/adr-contract-syrupy-mdast-$BR.out
```

Commits (subject lines; bodies explain why, Markdown allowed, attribution as
the session requires):

1. `Draft ADR-003 snapshot contract v1` (EP-M1).
2. `Accept ADR-003 snapshot contract v1` (EP-M2).
3. `Guard ADR-003 and reconcile the design` (EP-M3).
4. `Complete roadmap task 1.1.2` (EP-M4).

## Validation and acceptance

Quality criteria:

- Tests: `make test` passes; `tests/test_snapshot_contract_adr.py` passes, and
  its DOC-5 table and property failed against the stub before the helper was
  implemented; DOC-4 and DOC-6 failed before the reconciliation edits.
- Verification: DOC-1 to DOC-6 discharged as described; EV-1 transcript
  identical.
- Lint and typecheck: `make check-fmt`, `make typecheck`, `make lint` pass
  (Interrogate at 100% including the new test module and helpers).
- Markdown: `make markdownlint` and `make nixie` pass.
- Process: the ADR-003 acceptance commit precedes the contract-test commit.

Red-Green-Refactor record (fill in during EP-M3):

- Red: `uv run pytest -v tests/test_snapshot_contract_adr.py` — expected
  failures listed under EP-M3.
- Green: same command, all pass.
- Refactor: `make check-fmt`, `make typecheck`, `make lint`, `make test`.

No pytest-bdd feature file is part of this plan (DEC-12).

## Idempotence and recovery

Every step is a file edit or a read-only command and may be repeated. The probe
installs into `uv`'s cache and a throwaway environment; it never touches the
project environment or lockfile. If a gate fails midway, fix and re-run that
gate, then re-run the full sequence before committing. If the maintainer
rejects the ADR, revert to the EP-M1 commit and revise.

## Artefacts and notes

Probe script (run in `/tmp/wenmode-probe`, never in the repository):

```python
"""Probe Wenmode's GitHub profile for ADR-003's normative decisions."""

import json
from importlib.metadata import version

from wenmode import Parser
from wenmode.presets import github

CASES = {
    "emph_star": "*a* **b**\n",
    "emph_under": "_a_ __b__\n",
    "direct": '[x](/u "t")\n',
    "full": '[x][r]\n\n[r]: /u "t"\n',
    "collapsed": '[x][]\n\n[x]: /u "t"\n',
    "shortcut": '[x]\n\n[x]: /u "t"\n',
    "forward_first": "[r]: /u\n\n[x][r]\n",
    "unresolved": "[x][nope]\n",
    "unused": "text\n\n[u]: /unused\n",
    "label_case": "[Foo]\n\n[FOO]: /u\n",
    "image_ref": "![alt][i]\n\n[i]: /i.png\n",
    "footnote": "a[^1] b[^n]\n\n[^1]: one\n[^n]: two\n",
    "footnote_forward": "[^f]: def\n\nref[^f]\n",
    "footnote_unused": "x\n\n[^u]: unused\n",
    "footnote_undefined": "x[^missing]\n",
    "footnote_case": "x[^A]\n\n[^a]: y\n",
    "html_ok": "<div>\nhi\n</div>\n\n<span>x</span>\n",
    "html_block_script": "<script>alert(1)</script>\n",
    "html_block_iframe": "<iframe src=a></iframe>\n",
    "html_inline_iframe": "x <iframe src=a></iframe> y\n",
    "table_align": "| a | b | c |\n|---|:-:|--:|\n| 1 | 2 | 3 |\n",
    "task": "- [ ] a\n- [x] b\n",
    "ordered": "3. a\n4. b\n",
    "code": "```py title=x\n  x \n```\n",
    "hardbreak": "a  \nb\\\nc\n",
    "crlf": "a\r\nb\r\n",
    "cr": "a\rb\r",
    "crlf_code": "```\r\nx\r\n```\r\n",
    "entity": "&amp; &copy;\n",
    "no_title": "[x](/u)\n",
}


def children(source: str) -> list[object]:
    """Return the root children for one source under the v1 construction."""
    return Parser(github(), positions=False).parse(source).to_ast()["children"]


print("version", version("wenmode"))
for name, source in CASES.items():
    print(name, "=>", json.dumps(children(source), ensure_ascii=False))
```

Key transcript lines observed on 2026-09-27, abridged: the full output is
regenerated by the command in `Concrete steps`. Here `para(...)` abbreviates
`{"type": "paragraph", "children": [...]}`, `text "x"` abbreviates
`{"type": "text", "value": "x"}`, and `…` elides unchanged children.

```plaintext
version 0.15.1
emph_star          => para(emphasis(text "a"), text " ", strong(text "b"))
emph_under         => identical to emph_star
direct, full, collapsed, shortcut
                   => para({"type": "link", "children": [text "x"], "url": "/u", "title": "t"})
unresolved         => para(text "[x][nope]")
unused             => para(text "text")
label_case         => para({"type": "link", "children": [text "Foo"], "url": "/u"})
footnote_forward   => {"type": "footnoteDefinition", …, "identifier": "f", "label": "f"},
                      para(text "ref", {"type": "footnoteReference", "identifier": "f", "label": "f"})
footnote_unused    => para(text "x"), {"type": "footnoteDefinition", …, "identifier": "u", "label": "u"}
footnote_undefined => para(text "x[^missing]")
footnote_case      => … {"type": "footnoteReference", "identifier": "a", "label": "a"} …
html_block_script  => {"type": "html", "value": "<script>alert(1)</script>\n"}
html_block_iframe  => {"type": "html", "data": {"escaped": true}, "value": "&lt;iframe src=a>&lt;/iframe>\n"}
html_inline_iframe => para(text "x ", {"type": "html", "data": {"escaped": true}, "value": "&lt;iframe src=a>"}, …)
table_align        => {"type": "table", …, "align": [null, "center", "right"]}
code               => {"type": "code", "value": "  x \n", "lang": "py", "meta": "title=x"}
hardbreak          => para(text "a", {"type": "break"}, text "b", {"type": "break"}, text "c")
crlf               => para(text "a\r\nb")
cr                 => para(text "a\rb")
crlf_code          => {"type": "code", "value": "x\r\n"}
entity             => para(text "&", text " ", text "©")
no_title           => para({"type": "link", "children": [text "x"], "url": "/u"})
```

Draft upstream report (file only with maintainer authorization): "With the
`github` preset in 0.15.1, HTML blocks beginning `<script`, `<style`, or
`<textarea` are emitted as `html` nodes without the disallowed-tag rewrite,
while `<iframe>` blocks and inline `<script>` are rewritten and marked
`data.escaped`. GFM 0.29-gfm §6.11 applies the tag filter to raw HTML blocks as
well. Reproduction: `Parser(github()).parse('<script>x</script>\n').to_ast()`."

Sources consulted (2026-09-27): Wenmode on PyPI
(<https://pypi.org/project/wenmode/>), Wenmode presets, security,
compatibility, node model, and changelog pages under
<https://wenmode.lepture.com/>, GFM spec 0.29-gfm
(<https://github.github.com/gfm/>), and Syrupy 6.0.0 source in the project
environment (`syrupy/extensions/single_file.py`,
`syrupy/extensions/amber/serializer.py`).

## Interfaces and dependencies

No production interface changes. No dependency changes.

### ADR-003 contract manifest (normative content for EP-M1)

The ADR's `### Contract manifest` subsection contains exactly this block
(values fixed by DEC-4, DEC-5, DEC-6, DEC-10):

```toml
[snapshot-contract]
contract-version = 1
wenmode = "==0.15.1"
parser = "Parser(github(), positions=False)"
file-extension = "mdast.json"
key-order = [
  "type", "depth", "ordered", "start", "spread", "checked", "align", "lang", "meta",
  "url", "title", "alt", "identifier", "label", "value", "data", "children",
]
json-writer = 'json.dumps(tree, ensure_ascii=False, indent=2, allow_nan=False) + "\n"'
```

### ADR-003 normative fixture decisions (for EP-M1; consumed by 1.1.3 and 1.2.3)

Each item states the ratified behaviour under contract v1. "Equal" means the
two inputs must produce byte-identical payloads; "distinct" means they must not.

- NF-1. Emphasis delimiter spelling: `*a*`/`_a_` and `**b**`/`__b__` equal.
- NF-2. Ordinary references: direct, full, collapsed, and shortcut forms equal
  when destination, title, and children agree; a definition before its use
  resolves; label matching is case-insensitive while link text keeps its case;
  unused definitions leave no trace; an unresolved reference stays literal
  text. Reference images resolve to `image` with `url`, `alt`, and `title` when
  present.
- NF-3. Footnotes: `footnoteReference` and `footnoteDefinition` carry
  `identifier` and `label`, both case-folded by Wenmode (so `[^A]`/`[^a]`
  equal); definitions stay at their source position (moving one is distinct);
  unused definitions are retained; repeated references repeat; undefined
  references stay literal text.
- NF-4. Omitted nullable members: absent `title`, `lang`, `meta`, `checked`
  (non-task items), and `start` (bullet lists) stay absent; no `null` member is
  synthesized.
- NF-5. `null` array elements: unspecified table column alignment is `null`
  inside `align` and is preserved; alignment changes are distinct.
- NF-6. Raw HTML: `html` nodes keep their `value`; tags on GitHub's disallowed
  list are rewritten by Wenmode to a leading `&lt;` with
  `data: {"escaped": true}`, and that non-empty `data` is preserved.
- NF-7. Known divergence: CommonMark type-1 HTML blocks whose tag is on the
  disallowed list (`<script`, `<style`, `<textarea`) are not tag-filtered in
  0.15.1 and are ratified as observed; other disallowed tags (`<title>`,
  `<iframe>`, `<xmp>`, `<plaintext>`, and so on) are filtered. An upstream fix
  is a contract change.
- NF-8. Line endings: LF, CRLF, and CR inputs produce equal payloads after
  rule 3; this includes text, code values, and titles.
- NF-9. Positions: payloads never contain `position`, even though the parser
  is constructed with `positions=False`.
- NF-10. Preserved distinctions: hard break versus soft line break; code
  whitespace and `lang`/`meta`; list `ordered`, `start`, `spread`, item
  `checked`, and item order; table cell content and alignment; raw HTML
  spelling.
- NF-11. Text segmentation: entity references and backslash escapes produce
  separate text nodes and are not merged; `a & b` and `a &amp; b` are distinct
  (DEC-7).
- NF-12. Key order: every emitted object's members follow the manifest
  `key-order`, then remaining members by code point; a contract fixture pins
  one node of every GitHub-profile type.

### Test-support interface (EP-M3)

In `tests/support/adr_contract.py`:

```python
ADR_PATH: typ.Final[pathlib.Path]  # REPO_ROOT / "docs/adr-003-parser-profile-and-snapshot-version-policy.md"


@dataclasses.dataclass(frozen=True, slots=True)
class SnapshotContractManifest:
    contract_version: int
    wenmode: str
    parser: str
    file_extension: str
    key_order: tuple[str, ...]
    json_writer: str


def adr_status(markdown: str) -> str: ...
def read_manifest(markdown: str) -> SnapshotContractManifest: ...
def key_order_problems(key_order: cabc.Sequence[str]) -> list[str]: ...
def wenmode_declaration_problem(requirements: cabc.Sequence[str], pinned_version: str) -> str | None: ...
```

Each function takes text or data rather than paths, so the negative controls
can feed hand-written inputs; only the tests read files.

## Revision notes

- 2026-09-27 — initial draft from reconnaissance, Wenmode 0.15.1 probe, and
  external research. Awaiting expert-panel review.
