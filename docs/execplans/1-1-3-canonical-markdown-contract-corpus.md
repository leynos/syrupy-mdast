<!-- markdownlint-disable MD012 -->
<!-- ExecPlans require two blank lines after headings. -->

# Create the canonical Markdown contract corpus


Status: IN PROGRESS — EP-M1, EP-M2, and EP-M3 are complete. The last full
deterministic run passed with 344 tests on the prior candidate. Review #22's
line-ending case reasons are corrected below. On 2026-10-19, D12 split path
validation from file resolution and manifest decoding from TOML parsing after
hosted CodeScene again reported loader complexity above 4. Local `cs delta` now
reports health 10.00 for the working change. All seven sequential local gates
pass on the current working candidate, including 344 tests; the audit found no
known vulnerabilities, although two packages are unavailable on PyPI. Commit,
hosted checks, and CodeScene reassessment remain pending. Implementation
acceptance is open and roadmap task 1.1.3 remains unchecked. The maintainer
granted an exception to the 600-line total cap on 2026-10-15.

Roadmap task: **1.1.3**. Prerequisite: **1.1.2**, completed at baseline
`c19afee8ed735dffa6262cf0b2e0a9ca0a5a0551`.

This execution plan is a living document. Keep its constraints, tolerances,
risks, progress, discoveries, decisions, conformance basis, verification plan,
and outcomes current at every milestone. Publication of the initial plan did
not itself approve implementation.

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
  implementation. The initial planning revision changed documentation only.
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
- Put tests and test support beneath `tests/`; keep each Python file at most
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
- The four-new-Python-file maximum remains active. The maintainer explicitly
  waived the original 600-total-line cap for this plan on 2026-10-15 (D6); the
  400-line per-file limit remains active. More than 100 named cases still
  requires a scope review, and the matrix below is mandatory and may not be
  trimmed to fit.
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
- **Implementation size (medium impact, mitigated by D6).** The loader and seed
  tests exceed the original total Python-line ceiling, which the maintainer
  waived for this plan. Keep the four-file maximum and 400-line per-file limit;
  organize cases by normative family and retain direct, readable assertions.

## Progress


- [x] (2026-10-13 22:46Z) Read repository guidance; verify clean baseline and
  completed prerequisite 1.1.2.
- [x] (2026-10-13 22:48Z) Obtain two Wyvern reconnaissance reports, shared
  through context pack `pk_gadsijjx`; establish absent parser and corpus
  infrastructure.
- [x] (2026-10-13 22:50Z) Check primary format documentation using Firecrawl;
  resolve reference terminology and parser-level code-span whitespace rules.
- [x] (2026-10-13 22:55Z) Complete all six community-of-experts perspectives
  and reconcile source-witness, newline, schema, and red-stage findings.
- [x] (2026-10-13 22:57Z) Validate the documentation-only plan: formatting,
  type checking, linting, 103 tests, Markdown, and Mermaid all passed.
- [x] (2026-10-14 11:39Z) Receive explicit implementation approval through the
  request to use this ExecPlan; verify PR #74, the exact candidate, and the
  trusted-author execution boundary.
- [x] (2026-10-14 11:55Z) Stop EP-M1 at the size tolerance: three new Python
  files total 813 lines against the 600-line ceiling. Focused tests passed, but
  full milestone gates and commit remain pending.
- [x] (2026-10-14) Repair the reported Python lint failures by splitting the
  manifest loader from shared test records and path helpers, documenting helper
  returns and exceptions, and narrowing regex/assertion checks. Targeted Ruff
  reports zero diagnostics, 58 focused tests pass, and `make fmt` completes.
  Logs: `/tmp/ruff-syrupy-mdast-113-targeted.json` and
  `/tmp/pytest-syrupy-mdast-113-targeted-after-lint.out`. The four Python files
  now total 1140 lines; D5 remains unresolved, so full milestone gates and
  commit remain pending.
- [x] (2026-10-14) Fix the follow-up df12 Pylint findings with assertion
  messages, structural matching, smaller semantic checks, and Python 3.12 type
  aliases. Targeted Ruff has zero diagnostics, targeted df12 Pylint is 10/10,
  and 59 focused tests pass. Logs: `/tmp/ruff-syrupy-mdast-113-targeted.json`,
  `/tmp/pylint-df12-syrupy-mdast-113-targeted.out`, and
  `/tmp/pytest-syrupy-mdast-113-targeted-after-df12.out`. The four Python files
  now total 1198 lines; D5 remains unresolved.
- [x] (2026-10-14) Remove three redundant casts reported by the full `ty`
  check. Targeted `ty` and Ruff checks now pass for the loader. Logs:
  `/tmp/ty-syrupy-mdast-113-targeted.out` and
  `/tmp/ruff-syrupy-mdast-113-targeted-after-ty.out`. The four Python files now
  total 1196 lines; the full hook rerun remains scheduled.
- [x] (2026-10-14) Pass the full commit gates after the `ty` repair and commit
  the seed corpus as `08c10f0`. Formatting, lint, type checking, 162 tests,
  Markdown lint, and Mermaid validation passed. The dependency audit found no
  known vulnerabilities; `df12-python-lints` and `syrupy-mdast` were
  unavailable on PyPI and could not be audited. EP-M1 remains blocked by D5
  because the four Python files total 1196 lines against the 600-line tolerance.
- [x] (2026-10-15 16:22Z) Receive the maintainer's explicit exception to the
  600-total-line cap for this plan. The four-file maximum, 400-line limit per
  Python file, and 100-named-case scope-review threshold remain active.
- [x] (2026-10-15) Triage the CodeRabbit CLI 0.9.0 review of all 23 paths. Two
  duplicate findings correctly requested assertions for the authored emphasis
  and strong child values; those assertions are now in the candidate. The
  array-error finding is not applicable: the plan requires contextual
  `ValueError` for its listed invalid IDs, paths, kinds, and relations, while
  wrong field types retain contextual `TypeError`.
- [x] (2026-10-15) Pass all seven deterministic gates after the M1 semantic
  review fixes; 169 tests passed. The audit found no known vulnerabilities, but
  could not query `df12-python-lints` or `syrupy-mdast` on PyPI. The next
  CodeRabbit review found four distinct issues: the support module needed a
  usage docstring; the manifest version test needed byte reads; a
  directory-valued manifest path needed the contextual error path and a
  negative test; and this progress list needed consistent wrapping. Its two
  notes about the path pre-check conflicted; the candidate removes the check
  and handles the directory read error without claiming the original check was
  defective. The full seven-gate rerun passed with 170 tests, and fresh
  CodeRabbit CLI 0.9.0 review returned zero findings across all 23 changed
  paths. The audit found no known vulnerabilities; its two PyPI omissions
  remain recorded. Review output: `/tmp/coderabbit-review-UpB3UD/review.out`;
  the seven gate logs use the branch-scoped filenames in `/tmp`.
- [x] (2026-10-15) Complete the static M2 matrix with 99 cases (92 Markdown,
  seven synthetic), 75 independently authored expected trees, 34 exact
  relations, and 71 semantic markers across all 20 required rules. Add exact
  case/rule coverage, a 22-node-type assertion, omission/order and
  transformation checks, and copied-file negative controls for missing cases,
  partner goldens, retained positions, weaker source witnesses, and
  newline-normalizing reads. The focused integrity suite passes 161 tests; full
  gates and the M2 CLI review remain pending. At matrix completion, the four
  Python files had 398, 363, 399, and 393 lines.
- [x] (2026-10-15) Triage the complete CodeRabbit CLI 0.9.0 review across 182
  changed paths. Fix the impossible nested `root` in the Markdown all-node
  golden, identify the README's short table as representative, remove the
  unreachable witness-empty branch, assert node coverage across all expected
  trees, and normalize progress-list wrapping. Retain whitespace-only source
  witnesses because exact invisible bytes can be meaningful; `reason` remains
  non-whitespace prose. Focused tests pass again (161 tests); full gates and
  CodeRabbit reassessment are pending for these repairs. The four Python files
  are now 398, 360, 397, and 393 lines.
- [x] (2026-10-15) Repair the next complete 182-file CodeRabbit review. The
  U+E000 key was already present in the synthetic source, witness, and golden;
  make it explicit as a JSON escape in the source/witness and add a temporary
  golden mutation that puts U+10000 before U+E000. Also correct the stale EP-M1
  review status in this retrospective. The focused integrity suite passes 161
  tests; full gates and CodeRabbit reassessment remain pending. The four Python
  files are 398, 360, 400, and 393 lines.
- [x] (2026-10-15) The next full rerun found Ruff's composite-assertion rule
  after the key-order negative control was added. Restore separate type and
  value checks and name the null array child explicitly, keeping the largest
  Python file at 400 lines. The other six gates passed, including 264 tests;
  the complete rerun and review remain pending.
- [x] (2026-10-15) The lint rerun then found Pylint C1804 on the empty-string
  equality. Restore separate string-type and empty-value assertions, shorten
  the null array check to one line, and keep the file at 400 lines. The other
  six gates passed, including 264 tests; the full rerun remains pending.
- [x] (2026-10-15) Pass the complete seven-gate rerun with 264 tests; the audit
  found no known vulnerabilities but could not query `df12-python-lints` or
  `syrupy-mdast` on PyPI. Fresh CodeRabbit CLI 0.9.0 review of 182 changed
  paths found one minor wording issue: the plan said “below 400 lines” while
  the repository permits 400 and one file has exactly 400. Change the limit to
  “at most 400” and clarify the historical line-count entry. Final M2 gates and
  review reassessment remain pending for this plan update.
- [x] (2026-10-15) The next full gate run also passed all seven checks with 264
  tests. CodeRabbit found a second stale “below” phrase in D7; change it to
  “within” so the plan accurately includes a file at the 400-line ceiling.
  Final M2 gates and review reassessment remain pending for this correction.
- [x] (2026-10-15) Complete EP-M2 after the final wording repair: all seven
  gates pass with 264 tests, the audit has no known vulnerabilities with two
  packages unavailable on PyPI, and fresh CodeRabbit CLI 0.9.0 review returns
  zero findings across 182 changed paths. Gate logs use the `m2-planword2.out`
  suffix; review output is `/tmp/coderabbit-syrupy-mdast-m2-xXe9Dm/review.out`.
- [x] EP-M1: establish the corpus format and focused seed cases; pass the
  required milestone review before advancing.
- [x] EP-M2: complete every normative fixture and integrity assertion.
- [x] EP-M3: reconcile documentation and validate the corpus deliverable.
- [ ] Mark roadmap 1.1.3 done after implementation acceptance and hosted
  delivery checks pass.
- [x] (2026-10-15) Reconcile design §§7–8 with the accepted parser call and
  five-rule sequence; add the corpus workflow and integrity boundary to the
  developer guide and link the corpus from the contents and user guides. No new
  decision beyond ADR-004 was needed. At that point the roadmap checkbox was
  withheld pending final M3 review and validation.
- [x] (2026-10-15) Fresh CodeRabbit CLI 0.9.0 review of 187 paths found two
  low-severity documentation issues: `list-tight` needed to explain its
  deliberate source/golden reuse, and the checked roadmap item conflicted with
  the open M3 status. The reason now documents the deliberate reuse, and the
  roadmap check was withheld until the final M3 gates and review passed.
- [x] (2026-10-15) Disposition CodeRabbit's numeric-reference finding. The
  CommonMark 0.31.2 §2.5 rule says invalid Unicode code points become U+FFFD,
  but accepted ADR-004 NF-13 records Wenmode 0.15.2 leaving the surrogate and
  out-of-range references literal. Preserve the independent expected results;
  changing them would revise the accepted parser contract. The two manifest
  reasons now identify that provenance. Final M3 gates and review were pending
  at that point.
- [x] (2026-10-15) Add the requested `table-cell-base` semantic marker for
  value `"1"`; the existing distinct relation alone only proved that the
  expected payload differs from `table-cell-changed`. The assertion index now
  has 72 markers. The final M3 gates and review subsequently passed.
- [x] (2026-10-15) Complete EP-M3 after the marker repair: all seven gates
  pass with 265 tests; fresh CodeRabbit CLI 0.9.0 review returns zero findings
  across 187 paths. The audit found no known vulnerabilities;
  `df12-python-lints` and `syrupy-mdast` are unavailable on PyPI. Gate logs use
  the `m3-table-marker.out` suffix; review output is
  `/tmp/coderabbit-syrupy-mdast-m3-table-marker-LlVaJL/review.out`. The
  numeric-reference suggestion was dispositioned against the accepted
  Wenmode-specific NF-13 contract. The 2026-10-15 close-out checked the roadmap
  item; the 2026-10-17 reopening keeps it pending until implementation
  acceptance.
- [x] (2026-10-17) Repair loader complexity reported by hosted CodeScene by
  sharing duplicate-ID registration. Local `cs delta` improves loader health
  from 9.38 to 10.00. The first rerun found Markdown formatting and propagated
  exception-docstring lint errors; after correction, all seven gates passed
  with 265 tests. A fresh CodeRabbit 0.9.0 review of 187 paths returned four
  finding events: two overlapping mutation-check concerns, one spurious
  paragraph `data` member in the position-removal golden, and one plan-ordering
  inconsistency. The hosted CodeScene reassessment remains pending.
- [x] (2026-10-17) Share the exact case-inventory and recursive
  position-removal assertions between their positive and mutation-control
  tests; remove paragraph `data` absent from the synthetic input; and keep the
  reopened plan record chronological and consistent. All seven gates passed; a
  fresh review then found the wrong-type exception mismatch and premature
  roadmap completion. Their correction passed all seven gates with 266 tests. A
  subsequent review found `_table`'s wrong-type exception, a test helper that
  patched the reader, a missing exact relation inventory check, and EP-M3's
  acceptance wording. Hosted CodeScene reassessment remains pending.
- [x] (2026-10-17) Raise contextual `TypeError` for wrong-type table records;
  compare all manifest relation IDs with the assertion index; inject the source
  reader into its negative control; and separate EP-M3 completion from roadmap
  acceptance. All seven gates passed with 267 tests. Fresh CodeRabbit review
  found stale wording in this progress record; its correction is recorded here.
  Hosted CodeScene reassessment remains pending.
- [x] (2026-10-17) Document all seven non-NF rules, require pairwise-distinct
  bytes for distinct relation groups with a three-case mutation control, and
  replace inaccurate unresolved-reference and data-removal reasons. A fresh
  review identified these three gaps; this entry records their correction.
- [x] (2026-10-17) Replace remaining templated reasons that misdescribe direct
  links and images, table alignment and cell values, type-1 HTML, and entity
  spelling. A fresh review identified these false descriptions; this entry
  records their correction.
- [x] (2026-10-17) Correct the HTML-spelling, asterisk, and key-order reasons;
  require and exemplify `witness` in case records; and reconcile the outcomes
  paragraph. The preceding review identified these gaps after a seven-gate run
  passed with 267 tests; this entry records their correction.
- [x] (2026-10-17) Require equal relation groups to share one expected path;
  move manifest parsing helpers into `markdown_contract_loading.py`; expand its
  usage documentation; and correct footnote and numeric-reference reasons.
  These corrections follow the latest full-diff review.
- [x] (2026-10-17) Restore concise return and exception sections to the moved
  loader helper docstrings after the first full rerun found 28 Ruff
  diagnostics. All seven gates then passed with 267 tests; the loader remains
  within the 400-line per-file limit. Fresh review found two stale plan
  statements; their correction and final validation remain pending.
- [x] (2026-10-17) Correct the outcomes record and require hosted delivery
  checks plus implementation acceptance before roadmap completion. Fresh review
  found these inconsistencies with the constraints; final gates and review of
  this documentation update remain pending.
- [x] (2026-10-17) Fix the R-CORPUS README link and update the interface section
  for the delivered support-module split. Fresh review found both descriptions
  stale; final gates and another full-diff review remain pending.
- [x] (2026-10-19) Refactor the loader's path and manifest boundaries after
  hosted CodeScene reported mean cyclomatic complexity 4.38 across 16
  functions, above the configured threshold of 4. Separate lexical path checks
  from rooted file checks and strict text decoding from TOML parsing. Exact
  path errors, read/decode errors, and malformed-TOML errors remain distinct.
  `cs delta --file tests/support/markdown_contract_loading.py` reports the
  complexity issue fixed and health 10.00 on the working change. The loader is
  398 lines. All seven sequential local gates pass, including 344 tests;
  dependency audit found no known vulnerabilities but could not audit
  `df12-python-lints` or `syrupy-mdast` because they are unavailable on PyPI.
  Commit, hosted checks, and CodeScene reassessment remain pending.

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
- The first EP-M1 implementation pass totals 813 Python lines across
  `tests/support/markdown_contract.py` (273), `tests/test_markdown_contract.py`
  (223), and `tests/test_markdown_contract_loading.py` (317). This exceeds the
  600-line tolerance before the full fixture matrix is added. D6 waives only
  that total-line cap; it does not change the file-count or per-file limits.
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
- **D5 — implementation size tolerance reached.** 2026-10-14. The three new
  Python files total 813 lines, exceeding the 600-line cap while remaining
  below the four-file cap. Stop before expanding EP-M1. Options are to approve
  a revised line ceiling while retaining every acceptance obligation, or to
  direct a design review that brings the implementation under 600 lines without
  trimming the normative matrix. A larger ceiling accepts more maintenance
  surface; compression risks hiding distinctions unless every case remains
  directly reviewable. The maintainer resolved this blocker with D6.
- **D6 — waive the total implementation-line cap for this plan.** 2026-10-15.
  The maintainer explicitly granted an exception to the 600-line tolerance.
  Apply it to the complete 1.1.3 corpus implementation so the mandatory matrix
  can be delivered without opaque compression. Keep the four-file maximum,
  400-line per-file limit, test-only boundary, and 100-named-case review
  trigger. No replacement total-line ceiling was specified; continue tracking
  the actual count and keep each file cohesive and readable.
- **D7 — keep the explicit assertion index as fixture data.** 2026-10-15.
  Store the exact case-to-rule map, relation groups, node-type inventory,
  preferred key order, and focused expected-node markers in
  `assertions/contract-assertions.json`; tests compare those values with the
  manifest and authored goldens. This keeps the Python files within their
  per-file ceiling while leaving each assertion explicit and reviewable. The
  index is hand-maintained test evidence, not parser or canonicalizer output,
  and adds no dependency or runtime behaviour.
- **D8 — preserve exact whitespace-only source witnesses.** 2026-10-15. A
  witness is a required substring of the source's original bytes, so a value
  consisting only of spaces or newline bytes can document an invisible-byte
  distinction. For string inputs, `_string` rejects only the empty string. The
  separate `.strip()` check remains appropriate for the explanatory `reason`
  field; the redundant truthiness branch after `_string` was removed.
- **D9 — make code-point ordering failure observable.** 2026-10-15. The
  U+E000 key already existed, but CodeRabbit's review did not recognize it in
  its private-use glyph form. Encode the source key as `\uE000private`, retain
  the decoded key in the authored golden, and test a temporary golden with the
  U+10000 and U+E000 unknown keys swapped. The accepted Unicode code-point
  ordering is unchanged; the mutation now proves the fixture detects the
  competing UTF-16 order.
- **D10 — share duplicate manifest-ID registration.** 2026-10-17. Hosted
  CodeScene reported the loader's mean complexity above its configured
  threshold. Case and relation loading implemented the same duplicate-ID check
  and contextual error formatting. Share that one policy in a private helper
  used only by those two manifest record types; preserve the existing exact
  error messages and tests. This is a cohesive maintenance boundary, not a
  threshold or suppression change. Reassess the hosted finding on the published
  candidate before closing the plan.
- **D11 — keep position-removal expectations transformation-only.** 2026-10-17.
  The synthetic position-removal input has no paragraph `data`, and ADR-004
  defines no transformation that adds members. Remove the paragraph `data` from
  its expected payload and assert its absence. This corrects the fixture; it
  does not change the accepted normalization contract.
- **D12 — separate loader validation boundaries.** 2026-10-19. Hosted
  CodeScene still measured the manifest loader at mean cyclomatic complexity
  4.38 across 16 functions, above its threshold of 4. Split lexical path
  validation from rooted file checks, and strict UTF-8 file reading from TOML
  decoding. Preserve contextual errors and keep the unchanged 400-line limit.
  Do not suppress the rule or change its configuration. Local delta analysis
  now clears the finding; hosted reassessment and full gates decide acceptance.

## Outcomes & retrospective


The six-perspective review is complete, and explicit implementation approval
arrived on 2026-10-14. EP-M1 added a typed loader and seed fixtures; its commit
`08c10f0` passed the full gates with 162 tests. EP-M2 added 99 cases (92
Markdown and seven synthetic), 75 hand-authored expected trees, 34 exact
relations, and 71 semantic markers across 20 rules and 22 node types. Its
commit is `97179f5`; the full gates passed with 264 tests, fresh CodeRabbit
review found no issues across 182 paths, and the audit found no known
vulnerabilities. EP-M3 adds the 72nd semantic marker and reconciles the design,
contributor and user guidance, and documentation index. Roadmap completion
remains pending until implementation acceptance. The previous gate and review
checkpoint passed with 344 tests and zero findings across 187 paths. Review #22
then asked for the nine line-ending cases to name their parsed values; each
reason now identifies its paragraph, code, or link-title value. The audit found
no known vulnerabilities, but `df12-python-lints` and `syrupy-mdast` remain
unavailable on PyPI. The 600-line total cap is waived for this plan; the
four-file and 400-line per-file limits remain. Representative negative controls
reject a missing required case, partner-golden substitution, retained
`position`, a mutated writer-shaped golden, weakened source witnesses, and a
CRLF declaration with LF bytes. The numeric-reference outputs follow accepted
ADR-004 NF-13 observations for Wenmode 0.15.2 despite CommonMark's U+FFFD
requirement for invalid Unicode values. No runtime behaviour has been
delivered; valid `str` input still raises `NotImplementedError`, and
parser/canonicalizer conformance remains deferred.

The 2026-10-15 close-out recorded the finite matrix counts, representative
negative controls, gate logs, and documentation reconciliation. Passing corpus
integrity tests validate the authored examples; they are not parser-conformance
proof. Normative fixtures and documentation are complete; PR acceptance and
hosted delivery checks remain open.

After publication, hosted CodeScene reported mean loader complexity 4.36
against a threshold of 4. D10 centralizes the repeated case/relation duplicate
ID policy; local analysis now reports the issue fixed and health 10.00. The
seven-gate rerun passed with 265 tests, but a fresh full-diff CodeRabbit review
found that the position-removal golden added paragraph data absent from its
synthetic input and that two mutation controls duplicated rather than reused
their guarded assertions. D11 removes the unsupported expected member. A later
review prompted contextual type errors, the reopened roadmap state,
source-reader injection, and an exact relation inventory. Those repairs passed
all seven gates with 267 tests. Subsequent reviews prompted case-reason and
case-schema corrections, recorded in the progress log. After restoring the
moved loader helpers' required docstring sections, all seven gates passed with
267 tests; later review corrections brought the passing count to 269. The
seventeenth review found no further issues across 187 paths. Review 18
identified stale outcomes and status wording in this plan; this revision
reconciles those sections with the latest gate result. Review 20 identified
missing contextual handling for permission-denied manifest reads and a writer-
shape test that did not report failures per golden. The loader now translates
`PermissionError`, and each golden has a separate stable-ID test. The latest
gates passed with 344 tests; review 21 found no further issues across 187
paths. The plan remains open until the published candidate clears hosted
CodeScene and is accepted.

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
  forms, and complete design §8 coverage → EP-M1/EP-M2 → A-COVERAGE/A-CASES; the
  [corpus README](../../tests/fixtures/markdown_contract/README.md) is the
  reader-facing fixture index.
- **R-NORMALIZE:** design §8 as amended by ADR-004's five ordered rules →
  EP-M2 → A-SYNTHETIC and A-GOLDEN.
- **R-PRESERVE:** design §8's preserved values, order, omissions, footnotes,
  and HTML plus NF-1–NF-13 → EP-M2 → A-CASES/A-SYNTHETIC.
- **R-BOUNDARY:** design §§2–5 and roadmap dependency order → every milestone
  → unchanged production API/dependency contracts and explicit deferred tests.
- **R-MAINTAIN:** design §8, contributor and user guidance, the documentation
  index, corpus README, and roadmap completion requirements → EP-M3 → A-DOCS
  and the gated roadmap checkbox.

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
`id`, `rules` (non-empty rule-ID array), `reason`, `witness` (a non-empty
string whose UTF-8 bytes occur as an exact substring of the input file bytes),
`kind` (`markdown` or `synthetic`), `input`, and `expected` (relative paths).
Markdown records also have `line_endings` (`lf`, `crlf`, `cr`, or `none`). For
mixed-newline examples, use a synthetic JSON string rather than adding an
ambiguous source category.

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
witness = "*a*\n"
kind = "markdown"
input = "sources/emphasis-asterisk.txt"
expected = "expected/emphasis.json"
line_endings = "lf"

[[cases]]
id = "emphasis-underscore"
rules = ["NF-1"]
reason = "Underscore emphasis removes delimiter spelling as a distinction."
witness = "_a_\n"
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

Use two test-only support modules, within the four-new-Python-file maximum.
`tests/support/markdown_contract.py` owns the typed records, `read_source`, and
JSON assertion helpers. `tests/support/markdown_contract_loading.py` owns the
manifest loader:

```python
def load_corpus(root: Path) -> ContractCorpus: ...  # markdown_contract_loading
def read_source(path: Path) -> str: ...  # markdown_contract
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

EP-M1 partial evidence on 2026-10-14: the focused red run failed all three
tests with the deliberate `NotImplementedError` stub, then the focused green
run passed 55 tests. The expanded tests cover metadata errors, source-byte
preservation, newline classification and corruption, seed relationships, and
writer shape. The raw Wenmode 0.15.2 probe passed all thirteen ADR checks; it
confirmed AST shapes only and did not execute canonicalization. Logs are
`/tmp/pytest-syrupy-mdast-1-1-3-EP-M1-red-attempt2.out`,
`/tmp/pytest-syrupy-mdast-1-1-3-EP-M1-green-attempt3.out`, and
`/tmp/wenmode-syrupy-mdast-113-adr004-probe-attempt2.out`. Full gates passed
before the seed corpus commit `08c10f0`: 162 tests passed, with the two PyPI
audit omissions recorded above. D6 resolves the only recorded M1 blocker;
milestone CLI review and the normative acceptance matrix remain.

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
  after A-COVERAGE through A-LOAD, all commit gates, hosted delivery checks,
  and implementation acceptance pass.

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

After all corpus evidence passes, update this plan's outcomes, progress, trace
links, and revision note. Run final gates and commit the implementation work.
Mark roadmap item 1.1.3 done only after hosted delivery checks and
implementation acceptance, in a separate gated documentation change. Final
conformance checks confirm all matrix obligations, unchanged architecture,
valid assumptions, current trace links, and no unresolved deviation. Recovery:
leave the roadmap unchecked until the failed gate is repaired; never weaken a
gate to close it. The remaining parser and serializer gaps stay visibly
assigned to their existing roadmap tasks.

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
artefacts. Re-running gates should produce the same fixture bytes. Use stable
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

Revision note (2026-10-14): the user explicitly approved implementation by
requesting this plan through the `sdlc-implementation` workflow. The plan is
now in progress; implementation remains bounded by its existing tolerances.

Revision note (2026-10-14): EP-M1 reached the 600-line Python implementation
tolerance at 813 lines. The plan is blocked pending direction; focused evidence
is recorded, and no full gates or implementation commit were produced.

Revision note (2026-10-15): the maintainer granted an exception to the total
600-line cap for this plan. The four-file maximum, per-file line limit, and
scope-review trigger remain. At that point, the seed corpus was committed and
its full local gates had passed; EP-M1's CLI review and the full normative
matrix were still outstanding.

Revision note (2026-10-15): EP-M2 is complete and committed as `97179f5` with
99 cases, 75 authored expected trees, 34 exact relations, 71 semantic markers,
264 passing tests, and a zero-finding review across 182 paths. EP-M3 adds the
72nd semantic marker, reconciles the accepted five-rule contract and user and
contributor documentation, and records the CommonMark/Wenmode numeric-reference
disposition. Final gates passed with 265 tests, and fresh CodeRabbit review
returned zero findings across 187 paths. The roadmap checkbox was checked at
that close-out; the 2026-10-17 revision below restores it to pending until
implementation acceptance. Runtime conformance remains deferred.

Revision note (2026-10-17): reopen final delivery after hosted CodeScene
reports the loader mean complexity over its threshold. D10 centralizes the
case/relation duplicate-ID check and clears local analysis. Successive fresh
reviews also led to a corrected position-removal golden and shared positive
assertions for its mutation controls. Successive reviews found wrong-type
exception gaps in `_string` and `_table`, and that roadmap completion preceded
implementation acceptance. The following review prompted exact relation-set and
source-reader corrections; all four repairs passed the seven gates with 267
tests. A subsequent review found stale wording in this progress record. The
roadmap item remains unchecked while hosted CodeScene reassessment and PR
acceptance are pending.

Revision note (2026-10-17): the next full-diff review found generic fixture
explanations and missing test-module usage notes. The manifest now names the
reference forms, break nodes, and retained code/list fields each case records;
both test docstrings state their focused command and scope within the 400-line
per-file limit. Fresh gates and review remain pending.

Revision note (2026-10-17): review #13 found that Python equality could match
boolean markers to integers and that the positive corpus source check
duplicated its mutation helper. Semantic marker matching is now recursively
type-sensitive, with nested `False`/`0` and `True`/`1` negative controls; the
corpus check uses the shared source round-trip assertion. Fresh gates and
review remain pending.

Revision note (2026-10-17): review #14 found one remaining dictionary equality
that allowed `False` and `0` to compare equal in the falsy-data assertion. The
test now checks the exact key set and asserts the retained boolean by identity.
Fresh gates and review remain pending.

Revision note (2026-10-17): review #15 found that the test-module docstrings
omitted purpose and coverage details, and that two hard-break line-ending
reasons described string normalization instead of the expected `break` node.
Both descriptions now match their cases. Fresh gates and review remain pending.

Revision note (2026-10-17): review #16 found that the fenced-code whitespace
case changed both leading and trailing spaces. Its source, expected value,
semantic marker, witness, and reason now isolate the leading-space count while
retaining the trailing space. Source fixtures now treat trailing whitespace as
input data for diff checks. Review #17 found no further issues; all seven gates
passed with 269 tests, and the full-diff review reported zero findings across
187 paths. Hosted CodeScene reassessment and PR implementation acceptance
remain pending, so roadmap item 1.1.3 stays unchecked.

Revision note (2026-10-17): review #20 found that permission-denied manifest
reads escaped the loader's contextual `ValueError`, and that the writer-shape
check reported only the first failing golden. `_read_manifest` now catches
`PermissionError` narrowly, and all 75 expected payloads have individual
writer-shape tests with corpus-relative IDs. The seven gates passed with 344
tests; fresh review #21 found zero issues across 187 paths. Hosted CodeScene
reassessment and implementation acceptance remain pending.

Revision note (2026-10-17): review #22 found that the nine line-ending case
reasons described normalization without naming the parsed string and expected
value. The paragraph, fenced-code, and link-title reasons now state the value
each fixture pins for LF, CRLF, and bare CR input. Hosted CodeScene
reassessment and implementation acceptance remain pending.

Revision note (2026-10-19): hosted CodeScene result 7998531 reports loader
complexity 4.38 across 16 functions, above the threshold of 4, on published head
`2b5ca1d`. D12 separates path validation, rooted file checks, manifest
reading, and TOML decoding without suppressing the rule. Local delta analysis
reports the working change fixed at health 10.00. All seven sequential local
gates pass on the working candidate, including 344 tests. Audit reports no
known vulnerabilities with two packages unavailable on PyPI. Commit, hosted
checks, and hosted CodeScene reassessment remain pending. The PR remains draft
and the roadmap item remains unchecked until implementation acceptance.
