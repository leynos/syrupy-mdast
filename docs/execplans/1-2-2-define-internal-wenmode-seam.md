# Define the internal Wenmode seam (1.2.2)

Status: COMPLETE — implemented and locally validated (2026-11-15). The change
fits the size tolerances (21 non-ExecPlan files and 1755 net lines at the
review-repair head) after the reviewer raised them to 24 non-ExecPlan files and
2400 net lines; hosted assessment and merge remain with the pull request.

This execution plan is a living document. Keep Constraints, Tolerances, Risks,
Progress, Surprises & discoveries, Decision log, Outcomes & retrospective,
Conformance basis, and Verification plan current at every milestone.

## Purpose / big picture

Give later Markdown comparison work one small Python parsing entrypoint whose
parser state belongs to one call. After implementation, sequential documents,
concurrent calls, nested calls, and pytest-xdist workers must produce
independent Wenmode abstract syntax trees (ASTs). Editable installations and
installed wheels must exercise that same entrypoint without JavaScript or
network access. This slice does not yet make the public Syrupy extension parse
Markdown.

## Constraints

Implement only roadmap 1.2.2 after explicit approval. Preserve the exact
`wenmode==0.15.2` dependency delivered by 1.2.1. Every invocation must construct
`Parser(github(), positions=False)` and return `parser.parse(source).to_ast()`
unchanged. Do not cache parsers, profiles, results, or per-document state; do
not use thread-local storage or a parser pool. No backend protocol, registry,
injection parameter, or compatibility shim is required. A test double patched
at the module boundary is test machinery, not a production extension point.

Keep the seam internal and leave `syrupy_mdast.__all__` unchanged. Do not wire
it into the public extension, canonicalize output, validate AST shapes,
serialize JSON, or implement input limits or domain-error translation. Those
belong to later roadmap slices. Do not update normative corpus goldens to match
parser output. Retain Python-only packaging and Python 3.12 compatibility. No
Rust extension, new runtime dependency, or native proof tool belongs in this
slice.

Keep Python files below 400 lines. Read `AGENTS.md`, the relevant
`.rules/python-*.md` files, and `docs/scripting-standards.md` before modifying
helper scripts. Run candidate gates sequentially, logging output under `/tmp`;
never use `/tmp` as a build target. Do not commit failing candidates.

## Tolerances (exception triggers)

Stop implementation, record options and impacts in Decision log, set status to
BLOCKED, and seek explicit approval if a public API, dependency pin, canonical
format, or architecture must change. Also escalate if implementation needs more
than 24 non-ExecPlan files or 2400 net lines of code and other documentation.
ExecPlan files are excluded from both counts. The original limits were 16 files
and 900 net lines; after the completed change measured 19 files and 1596 net
lines at that point, the reviewer raised both limits on 2026-11-15, and the
Decision log records the measurements, the escalation, and that decision. The
change measures 1755 net lines at the review-repair head, still within both
limits; the earlier public-boundary repair head measured 1754, and the Decision
log records which head each figure belongs to. A required third-party
annotation workaround involving `Any`, a cast, or a suppression requires
evidence and review before adoption. Three unsuccessful fixes for the same
failure trigger reassessment, not a weaker assertion. There is no elapsed-time
cutoff.

## Risks

The main medium-likelihood, high-impact risk is vacuous concurrency evidence: a
passing test can serialize all work or never overlap parser state. Require
explicit barrier arrival, release ordering, retained instance references, and
negative controls. The Global Interpreter Lock is not an isolation argument.

A medium-likelihood risk is harness deadlock. All waits and joins must have
bounded timeouts, propagate worker failures, and release blocked peers in
`finally` cleanup. Avoid sleeps as synchronization and avoid relying solely on
an executor context manager to terminate blocked work.

A medium-likelihood risk is incorrect AST assumptions. Use the installed exact
release and small hand-authored assertions, not canonical corpus equality:
canonicalization has not been implemented. External documentation may describe
a newer release; inspect 0.15.2 annotations before finalizing imports.

A medium-likelihood risk is a strict Skylos finding for an internal entrypoint
whose application caller arrives later. Exercise the seam in installation
probes and investigate any finding under the documented entrypoint policy; do
not add a dummy production caller or a blanket suppression.

## Progress

- [x] (2026-11-03) Inspect roadmap, design, package boundary, and tooling.
- [x] (2026-11-03) Rename branch to `1-2-2-define-internal-wenmode-seam`.
- [x] (2026-11-03) Complete six-perspective expert review and revise the plan.
- [x] (2026-11-03) Complete plan-only validation and publish draft PR.
- [x] (2026-11-15) Obtain explicit approval for implementation.
- [x] (2026-11-15) EP-M1: implement and validate the seam and isolation
      obligations. Red stage observed as `ModuleNotFoundError`; 23 unit, 1
      property, 3 contract-scenario, 3 concurrency, and 4 worker results pass;
      every
      seeded fault and negative control failed for its intended reason.
- [x] (2026-11-15) EP-M1 gates (E6, label `ep-m1-attempt2`): `check-fmt`,
      `typecheck`, `lint` (including the strict Skylos gate), `test` (427
      passed), `audit`, `markdownlint`, and `nixie` all exit 0. The first
      attempt stopped at interrogate's 100% docstring gate and the second at
      df12-pylint assert-message and Skylos entry-point findings; both were
      repaired rather than waived.
- [x] (2026-11-15) EP-M2: route the installed probe through the seam and add
      the E5 sensitivity control. The old direct-parser probe was rerun under
      the seam replacement first and exited 0, recording the sensitivity gap
      the plan predicted; the updated probe then failed on the sentinel at its
      first adapter call. The probe now parses five documents, and
      `install_and_probe` runs the control in both installation modes. The
      wheel/editable BDD suite passes 4 tests, including the new resolved
      reference, resolved footnote, and later-document-stays-literal
      assertions. Design section 7, the developers' guide, the users' guide,
      and roadmap 1.2.2 were reconciled.
- [x] (2026-11-15) EP-M2 gates (E6, label `ep-m2-attempt3`): `check-fmt`,
      `typecheck`, `lint` (including the strict Skylos gate), `test` (427
      passed, all four installed-dependency scenario tests included),
      `audit`, `markdownlint`, and `nixie` all exit 0. `ep-m2-attempt1` was
      red on `typecheck` and `lint` in the refactored probe and `ep-m2-attempt2`
      was abandoned mid-run because a candidate edit landed after dispatch; both
      are superseded by `ep-m2-attempt3`, which ran against this exact working
      tree on top of commit `053e415`.
- [x] (2026-11-15) Rebase onto `5e6924d` to clear the conflict GitHub reported
      against `main`. The only conflict was a modify/delete on
      `tests/test_skylos_lint_contract.py`: `main` deleted that suite in
      `e1aaeca`, so the deletion was accepted and the typed entry-point rule in
      `pyproject.toml` was kept. `docs/contents.md` moved from "proposes" to
      "records delivery".
- [x] (2026-11-15) Rebased-candidate gates (E6, label `rebase-2`): all seven
      targets exit 0. `make test` reports 415 passed, twelve fewer than the
      pre-rebase 427 because `main` removed the Skylos contract suites in
      `e1aaeca`; `make lint`'s Skylos tier reports the `df12-skylos` gate
      passing under Skylos 4.33.2, so the typed entry-point rule still
      discharges the finding.
- [x] (2026-11-15) Reconcile the CodeRabbit completeness assessment of
      `9962ff4`. Two of its three remaining items were valid and are repaired:
      the installation module docstring misattributed wheelhouse construction,
      and the recorded size measurement lagged the published head. The third
      item is declined with evidence, and the reply also caught an unrecorded
      E5 ordering deviation, which is corrected in the code. The follow-up
      assessment is pending.
- [x] (2026-11-15) Follow-up assessment of `ec3f7c9`. It found no production
      defect and withdrew the E3 request, leaving three asks: a fresh mutant
      log, the current-head size measurement, and the Module-Level pre-merge
      re-run after readiness. The serialized-lock mutant now fails both overlap
      parametrizations by bounded assertion in 10.22 s, the dedicated
      `-n 2 --dist=each` run passes both tests on `gw0` and `gw1`, and the
      recorded measurement is 1596 net lines at `ec3f7c9`.
- [x] (2026-11-15) The reviewer raised the size limits to 24 non-ExecPlan
      files and 2400 net lines. The 19-file, 1596-line change now fits both, so
      the escalation is resolved; the revised limits and the decision are
      recorded in Tolerances and the Decision log, and a candidate-bound
      assessment of this plan revision follows.
- [x] (2026-11-15) CodeRabbit returned a clear whole-plan completeness verdict
      for candidate `f20d74f` and plan blob `4a50acdd`, and the pull request was
      marked ready. The formal review that followed raised two inline findings
      and one failed pre-merge check. Both inline findings were valid: the
      Outcomes E6 paragraph cited only `rebase-2`, which precedes the review
      repairs, and R1 and R4 named ADR files that do not exist. Both are
      corrected below. Of the pre-merge items, the scenario relabelling and the
      probe-scope clarification are accepted and applied, the public-boundary
      requirement was reported as already satisfied by
      `tests/test_public_api_contract.py`, and removing the failure-propagation
      double is declined with evidence in the Decision log. The review-queue
      rerun on `0cf5192` rejected that third disposition and asked for a
      behavioural test at the public boundary inside this change; it is added
      below, and the seam suites are reclassified as contract scenarios.
- [x] (2026-11-15) Assessment of `0e267bc` withdrew the double-removal request
      and confirmed the ADR and E6 corrections, but found two valid items: four
      references said the comparison pipeline was scheduled for 1.2.3, while
      the roadmap puts parsing at 2.1.1 and snapshot serialization at 2.3.1;
      and the recorded size predated the review reconciliation. Both are
      corrected here, and the reconciliation head measures 1606 net lines.
- [x] (2026-11-16) Reconcile the managed-queue review of `0cf5192`. It found no
      inline findings, passed `Module-Level Documentation` on that candidate,
      and failed `Testing (Unit And Behavioural)`: the seam-BDD suites were
      still presented as behavioural evidence, and the check wants a
      behavioural test at the public boundary inside the change rather than a
      reference to the unchanged `tests/test_public_api_contract.py`. Added
      `tests/features/public_extension.feature` with its binding in
      `tests/test_public_extension_bdd.py`. The direct scenario requires the
      roadmap 2.3.1 `NotImplementedError`; the registered scenario compares
      through the assertion and requires the rejected `matcher` control, which
      is where a consumer's path stops today. A temporary mutant that returns
      text instead of raising failed the direct scenario, and later comparison
      through the assertion showed the registered path never reaches
      serialization at all. Reclassified the seam suites as contract scenarios
      in the plan,
      the feature and binding docstrings, and the installation harness, and
      removed the behavioural labels from the design and developers' guides.
      The change now measures 21 non-ExecPlan files and 1755 net lines at the
      review-repair head.

## Surprises & discoveries

The existing installation probe in `tests/support/wenmode_runtime_probe.py`
constructs and reuses a Wenmode parser directly. It proves the dependency
boundary, not a package-owned seam. Switching that probe to the seam is needed
for this slice's integration evidence.

`docs/repository-layout.md` is referenced by instructions but absent at the
planning baseline. Use `docs/contents.md` and the explicit paths below for
orientation; creating a repository-wide layout document is outside this slice.

Wenmode 0.15.2 resets its per-document reference and footnote tables when a
parser is reused, so sequential AST equality cannot detect parser reuse. The
first definition document followed by an unresolved document produces the
correct trees on a deliberately cached parser. Identity and construction counts
(the E1 recording double, E3 retained instances, E4 per-worker counts) are what
actually reject reuse; the `cached-parser` mutation confirmed this by failing
12 tests while the plain sequence assertions passed.

The E3 serialized-call negative control behaves differently from the plan's
expectation. A global non-reentrant lock around `parse` makes the nested-call
test deadlock until pytest-timeout rather than fail a bounded witness, because
a nested call cannot acquire a lock its own outer call holds. The overlapping
tests do fail the bounded overlap witness as intended. Treat the deadlock plus
the timeout report as that mutant's evidence, not as a harness defect.

The nested call deliberately runs on the outer call's own thread, because
same-thread re-entry is what rejects a thread-local parser cache; moving the
inner call to a worker thread to buy a timeout would let that mutation pass. A
synchronous same-thread nested call cannot be time-bounded from inside, so a
global lock necessarily blocks it. E3 names the bounded overlap witness as that
mutant's required failure, and the overlap tests supply it within their
five-second bounds. The deadlocked nested test is therefore an accepted,
recorded consequence of keeping the stronger witness, not an undischarged
criterion.

Hypothesis reports roughly 5% of generated document sequences as "invalid test
cases" in its statistics. These are entropy overruns (inputs whose generation
exceeded the default buffer), not `assume()` or filter rejections: 50 examples
report 2 overruns, 500 report 25, and no health check fires. All classification
classes remain populated (about 85% of sequences define a label, 33% redefine
one, and 12% define none), so the property is not vacuous and no filtering
workaround is needed.

The predictor for the E5 sensitivity gap held exactly. Rerunning the previous
direct-parser probe with `syrupy_mdast._wenmode.parse_markdown` replaced by a
raising callable exited 0 and printed
`wenmode=0.15.2 mode=editable isolation=passed`, because that probe never named
the seam. The updated probe fails at its first adapter call with the sentinel
in the traceback, so the control separates the two probes for the intended
reason rather than through a collection error, a timeout, or an unrelated
import failure.

The probe cannot import the shared test documents. It runs under `python -I` in
a fresh environment, where the `tests` package is not importable, so the five
document literals are duplicated from `tests/support/wenmode_adapter.py`. The
installed BDD assertion charges that duplication to a failure instead of a
silent mismatch: it compares the probe's fifth document with
`plain_text_root(UNRESOLVED_DOCUMENT)`, which fails loudly if either side
drifts.

The replacement survives the probe's own import. The probe writes
`import syrupy_mdast._wenmode as wenmode_adapter`, which returns the module
object already held in `sys.modules`, and only then reads
`wenmode_adapter.parse_markdown`; replacing the attribute first therefore
reaches the call site without editing the probe. Running the replacement
program with `runpy.run_path(..., run_name="__main__")` keeps the probe file
unmodified and still exercises its real entrypoint, which is why no
fault-injection interface was added to production code.

`main` moved the dead-code gate while this branch was in review. Commit
`e1aaeca` replaced the Makefile's `SKYLOS_*` plumbing with the installed
`df12-skylos` command, deleted both Skylos contract suites, and moved the scan
roots and exclusions into `[tool.df12_skylos]` and `[tool.skylos]`. The typed
`[[tool.skylos.dead_code.entrypoints]]` rule remains the documented mechanism,
so the exception survives the rebase; only the duplicate symbol pin in
`tests/test_skylos_lint_contract.py` does not. Re-adding that pin would restore
a layer the repository deliberately removed, so the guarantee is recorded as
reviewed configuration instead.

- 2026-11-16: Comparing through a registered Syrupy assertion exposed a
  behaviour the direct-call checks could not see. Syrupy 6.0.0 always passes a
  `matcher` callable to `serialize`, even when no matcher is configured, so a
  registered assertion stops at the extension's unsupported-control
  `ValueError` before serialization; `NotImplementedError` is reachable only
  through a direct `serialize` call. The users' guide and design section 6 now
  say so, and the serialization milestone owns deciding how the matcher hook is
  satisfied. The new scenario records Syrupy's diff, which is how the failure
  reaches a consumer, and pytest-syrupy also prints `1 snapshot failed` for the
  deliberate comparison while the test itself passes.

## Decision log

- 2026-11-03: Propose one internal function in `syrupy_mdast/_wenmode.py`,
  following design section 7. Its only reuse scope is parsing for the later
  application pipeline and package-boundary tests. No equivalent production
  adapter exists at the baseline.
- 2026-11-03: Preserve upstream exceptions unchanged at this low-level seam.
  Test constructor, parse, and `to_ast()` failures using faithful doubles;
  domain error categorization remains with the future application pipeline.
- 2026-11-03: Combine real-parser semantics with instrumented lifetime tests.
  Sequential AST equality alone cannot detect forbidden parser reuse because
  Wenmode itself supports sequential reuse.
- 2026-11-03: Use Hypothesis for document-order independence and deterministic
  scheduling for overlapping calls. No new business logic or mathematical lemma
  warrants a Rust extension or Verus proof. Such an extension would violate the
  approved Python-only boundary without proving Python ownership.
- 2026-11-03: Record the eventual concrete seam and its lifecycle in the design
  document. No new ADR is needed for a direct realization of section 7 and
  ADR-004; any substantive departure requires approval and an ADR first.
- 2026-11-15: Implementation approved by the task request; plan status moved to
  APPROVED before any production edit. EP-M1 then proceeded red-to-green in the
  order recorded in Progress.
- 2026-11-15: Name the constructor's rule-source type once, as
  `type RuleSource = cabc.Iterable[type[Rule] | Rule] | PresetFactory`, in
  `tests/support/wenmode_adapter.py` and annotate the doubles' `rules`
  parameters with it. Passing `Parser(rules, ...)` a bare `object` was the only
  `ty` diagnostic; the alias states the upstream contract without a cast or a
  suppression, and no `Any` was introduced.
- 2026-11-15: Keep the test doubles' failure stages (`construct`, `parse`,
  `to_ast`) enumerated in one place so the sentinel tests cover every
  propagation point instead of a single representative call.
- 2026-11-15: Record the Skylos finding
  `SKY-U001 unused function: parse_markdown` as one typed entry-point rule in
  `pyproject.toml`, not a dummy caller or a blanket suppression. The seam has
  no caller inside the scanned `syrupy_mdast` tree yet; its runtime callers are
  the installed probe in a child process and the parsing pipeline scheduled for
  2.1.1. The rule names `syrupy_mdast._wenmode.parse_markdown` exactly, and
  `tests/test_skylos_lint_contract.py` lists the same name so a future symbol
  cannot inherit the exception silently.
- 2026-11-15: The completed change exceeds the original size limits: 19
  non-ExecPlan files against a limit of 16, and 1596 net lines against a limit
  of 900 (1648 insertions and 52 deletions at `ec3f7c9`; the same candidate
  measured 1594 at `9962ff4`, 1572 at `98cfed3`, and 1419 before the rebase).
  EP-M1 alone accounted for 12 files and 1311 net lines; EP-M2 added seven
  touched files and about 108 net lines. The composition is 52 production lines
  in `syrupy_mdast/_wenmode.py`, roughly 1225 lines of the unit, property,
  contract-scenario, concurrency, worker, and installed-evidence tests and
  support this plan names individually, and roughly 140 lines of documentation
  and configuration. Production code plus its design and developer
  documentation remains about 160 net lines; the estimate under-counted the
  verification suite and the number of files that evidence touches. The options
  were to compress or merge the evidence suites, to raise the budgets, or to
  accept the overage. Compressing would drop witnesses the Verification plan
  names individually, and raising a budget after the fact would hide the
  estimate error. The overage was escalated here and in the PR description; an
  attempt to obtain approval before EP-M1 finished was lost to a tool failure,
  and the task instruction required delivery to continue rather than block. On
  2026-11-15 the reviewer raised the limits to 24 non-ExecPlan files and 2400
  net lines. At the review-reconciliation head `0e267bc` the same change
  measures 19 non-ExecPlan files, 1658 insertions, 52 deletions, and 1606 net
  lines, so it fits both revised limits; 1596 was the measurement before that
  reconciliation. Reverting this branch's commits remains the recovery path if
  that decision is reversed.
- 2026-11-15: Put the E5 sensitivity control in its own module,
  `tests/support/wenmode_seam_sensitivity.py`, and call it from
  `install_and_probe`. A separate module names one responsibility, keeps
  `wenmode_installation.py` well inside the 400-line ceiling, and puts the
  control on the path of both installation modes instead of one test case.
- 2026-11-15: Assert the installed adapter's semantics with the existing
  `reference_urls`, `footnote_texts`, and `plain_text_root` helpers from
  `tests/support/wenmode_adapter.py` rather than new walkers or `json.dumps`
  substring checks. The helpers assert node semantics, and reusing them avoids
  a second definition of "resolved link" or "literal text".
- 2026-11-15: Keep the probe's five document literals local to the probe,
  because it runs with `-I` in a fresh environment where `tests` is not
  importable. Charge the duplication to a loud failure by comparing the probe's
  fifth document with `plain_text_root(UNRESOLVED_DOCUMENT)`.
- 2026-11-15: Mark roadmap 1.2.2 done and leave 1.2.3 and later items open.
  The success criteria for 1.2.2 name parser independence only; normative AST
  decisions and canonicalization belong to 1.2.3 and later slices.
- 2026-11-15: Accept `main`'s deletion of `tests/test_skylos_lint_contract.py`
  during the rebase onto `5e6924d`. The deleting change moved the gate to
  `df12-skylos` and removed the contract and whitelist-boundary suites as part
  of that migration; the typed entry-point rule is still supported and still
  names `syrupy_mdast._wenmode.parse_markdown` exactly, but the duplicate pin
  goes with the suite. The alternative, a new suite that pins the symbol again,
  would reverse a deliberate repository decision and widen this slice for a
  guarantee the reviewed configuration already provides.
- 2026-11-15: Reconcile the CodeRabbit completeness assessment of `9962ff4`.
  Two of its three remaining items were valid. The installation module
  docstring said `install_and_probe` built the wheelhouse, but
  `prepare_wheelhouse` builds it and `install_and_probe` serves one mode per
  call; the docstring now says so. The recorded size measurement was the
  `98cfed3` figure; the Decision log now records the `9962ff4` measurement. The
  third item, the serialized-lock control deadlocking the nested witness, is
  declined with the evidence recorded under Surprises & discoveries: the nested
  call stays on the outer thread because same-thread re-entry is what rejects a
  thread-local parser cache, and E3 names the bounded overlap witness as that
  mutant's required failure. The assessment also caught a real E5 sequencing
  deviation: the successful probe ran before the sensitivity control, while E5
  requires the control first. `install_and_probe` now runs the control first,
  so that deviation is removed rather than recorded.
- 2026-11-15: The follow-up assessment of `ec3f7c9` found no production defect
  and withdrew the E3 request, but asked for the mutation log rather than the
  report. Rerunning the serialized-lock mutant against the overlap tests alone
  fails both parametrizations with
  `AssertionError: both calls must be inside parse before either proceeds` once
  the five-second bound expires, with no pytest timeout, and the mutant is
  restored before the gates. The same assessment measured 1596 net lines at
  `ec3f7c9`, which the size entry above now records. The size deviation
  remained escalated to the reviewer until the limit increase recorded above,
  and the Module-Level pre-merge check remains to be re-run once the pull
  request is ready.
- 2026-11-15: CodeRabbit's formal review of `f20d74f` raised two valid inline
  findings, both corrected: Outcomes now cites `cap-2` on `f20d74f` alongside
  the earlier labels and points later record-only revisions at the pull
  request's validation table, because a plan edit cannot cite the run of the
  commit it creates; and R1 and R4 now name
  `docs/adrs/adr-0005-exact-wenmode-runtime-dependency.md` and
  `docs/adrs/adr-0004-parser-profile-and-normalization.md`, which are the paths
  `docs/contents.md` publishes. The same review failed its
  `Testing (Unit And Behavioural)` pre-merge check with four items. Two are
  accepted: the scenarios in `tests/features/wenmode_adapter.feature` are now
  presented as contract scenarios for the internal seam rather than as
  behavioural acceptance of the public package, and the design and developers'
  guides now state that the installed probe is installation and isolation
  evidence, not acceptance of the public surface. The third was answered by
  pointing at `tests/test_public_api_contract.py`, which asserts the two
  ratified public names, `__all__` equality, and the `NotImplementedError`
  contract through both the direct and the Syrupy-registered extension path;
  the rerun on `0cf5192` declined that answer, because the check wants a
  behavioural test inside the change rather than a reference to an unchanged
  suite. The fourth, removing the recording double from the propagation
  scenario, is declined: the plan's own contract-scenario specification
  requires the scenario `An upstream failure does not poison the next call`,
  the real parser cannot be made to fail deterministically on demand, and the
  double is already documented as test machinery rather than an extension
  point. Removing it would delete a named witness and replace it with nothing.
- 2026-11-15: The assessment of `0e267bc` withdrew the double-removal request
  and confirmed the ADR and E6 corrections, then found two valid documentation
  items. The roadmap schedules normative AST probes at 1.2.3, parsing at 2.1.1,
  and snapshot serialization at 2.3.1, so the four places that treated the
  comparison pipeline as a 1.2.3 deliverable now name 2.1.1, and 2.3.1 where
  the public entrypoint is meant: this plan's two statements, the developers'
  guide, and the Skylos rationale in `pyproject.toml`. The size record also
  predated the review reconciliation; the reconciliation head measures 19
  non-ExecPlan files, 1658 insertions, 52 deletions, and 1606 net lines, and
  1596 is retained as the earlier measurement.
- 2026-11-16: The managed-queue review of `0cf5192` returned no inline findings
  and passed `Module-Level Documentation`, but kept
  `Testing (Unit And Behavioural)` failed. It rejected the earlier disposition
  that cited `tests/test_public_api_contract.py`, because the check requires a
  behavioural test inside the change and that suite is unchanged. The
  requirement is accepted rather than argued again: the new scenarios in
  `tests/features/public_extension.feature` drive the public package and a
  registered Syrupy assertion, and never the private seam. The seam suites are
  contract scenarios, and the plan, feature titles, binding docstrings, and
  installation harness now say so. The mutation that returns text from
  `serialize` instead of raising failed both new scenarios with
  `valid Markdown must reach the planned serializer, not be accepted`, so the
  scenarios are not vacuous. The change measured 21 non-ExecPlan files, 1811
  insertions, 57 deletions, and 1754 net lines at `2c59f41`, still inside the
  revised limits.
- 2026-11-16: CodeRabbit's assessment of `fb2aee9` found that the registered
  scenario stored only `assertion.extension` and then called `serialize`
  directly, so it did not serialize through the assertion the scenario names.
  The finding is valid. The scenario now keeps the assertion, compares a valid
  document through it, and requires the comparison to fail and Syrupy's
  recorded diff to name the unsupported `matcher` control; that is the
  consumer-visible path, because Syrupy always supplies the matcher hook before
  serialization. The direct scenario keeps the `NotImplementedError` naming
  2.3.1. The change measures 21 non-ExecPlan files and 1754 net lines at that
  head, inside the revised limits, and the full gate sequence is rerun on the
  resulting tree.
- 2026-11-16: CodeRabbit's assessment of `2c59f41` withdrew the earlier request
  for a `NotImplementedError` through a registered assertion, confirming from
  the tagged Syrupy 5.0.0 and 6.0.0 sources that both supply a matcher callable
  and record serialization failures. It kept one documentation inconsistency
  under R5: the users' guide's corpus paragraph still said valid `str` input
  raises `NotImplementedError` without noting that this describes a direct
  `serialize` call with no property controls. The paragraph now says so, which
  matches the paragraph above it and the two public-boundary scenarios. The
  change then measures 21 non-ExecPlan files, 1813 insertions, 58 deletions,
  and 1755 net lines. The status line and Tolerances cite that later
  measurement, and the E6 sequence is rerun on the resulting tree.

## Outcomes & retrospective

Both milestones are implemented and locally validated, and roadmap 1.2.2 is
claimed done; roadmap 1.2.3 and later work, including the deferred corpus, the
canonicalizer, and the public pipeline (2.1.1 parsing, 2.3.1 snapshot
serialization), remain open.

The seam is one production function that constructs
`Parser(github(), positions=False)`, parses once, and returns `to_ast()`
unchanged. Everything else the two plateaus needed was test machinery and the
evidence that the machinery is sensitive. Seeded faults and negative controls
(wrong profile, positions enabled, copied output, translated failure, cached
parser, cached concurrency, per-worker singleton, leaking double, and a
direct-parser probe under the seam replacement) each failed focused checks for
their intended reason, and the logs are recorded under `/tmp` with `ep-m1` and
`ep-m2` labels.

The installed evidence now covers what a unit double cannot: the package as
built and installed, in a child process with JavaScript runtimes absent and
socket and subprocess audit events denied, exercising the seam in both wheel
and editable modes and failing when the seam is replaced.

All seven gates pass under label `ep-m2-attempt3` (427 tests on the pre-rebase
base), again under `rebase-2` (415 tests after `main` removed the Skylos
contract suites), and again under `cap-2` on the implementation candidate
`f20d74f`, which is the tree after the review repairs, with 100% docstring
coverage, both Pylint passes at 10.00/10, a passing strict Skylos gate, and no
known audit vulnerabilities. The two earlier EP-M2 labels are red or abandoned
and are not evidence. A later record-only ExecPlan revision cannot cite the run
of the commit it creates, so each such run is recorded with its label and
candidate in the pull request's validation table instead; that table is the E6
index for revisions after `f20d74f`. Hosted CI, the two CodeRabbit assessments,
and the merge belong to the pull request and were not part of this local
plateau.

Residual limitations are recorded rather than hidden. The serialized-lock
negative control deadlocks the nested-call test until the global pytest
timeout, although its designated witness, the overlapping-call test, fails by
bounded assertion in 10.22 s. Hypothesis reports entropy overruns as "invalid"
cases, and the property samples rather than proves. The concurrency evidence
covers two controlled interleavings plus one nested level, not every schedule.
None of these leaves a required criterion undischarged, but none of them should
be read as a broader guarantee than it is.

## Context and orientation

The baseline is commit `d602b1f6bc58ba97bba71d9ed7b6dddd19528954`.
`pyproject.toml` declares Wenmode 0.15.2 and already includes pytest,
pytest-bdd, Hypothesis, Syrupy, pytest-timeout, and pytest-xdist. The package
lives directly under `syrupy_mdast/`, not under `src/`. Its public exports are
`MarkdownAstError` and `MarkdownAstSnapshotExtension`; parsing integration is
still future work.

`tests/test_wenmode_dependency_bdd.py` and
`tests/features/wenmode_dependency.feature` exercise editable and wheel
installations through `tests/support/wenmode_installation.py` and
`tests/support/wenmode_runtime_probe.py`. Reuse those installation fixtures,
audit-hook controls, external working directory, and import-origin checks.
`tests/test_package_boundary.py` and `tests/test_package_manifest_contract.py`
protect Python-only packaging.

The corpus in `tests/fixtures/markdown_contract/` contains canonical expected
payloads. Its integrity tests do not establish raw parser conformance. Full
normative AST decisions remain roadmap 1.2.3; this plan needs only focused
reference, footnote, empty-input, heading, and task-list witnesses.

Before execution, load `python-router` and follow its `python-testing` and
`python-concurrency` guidance for the relevant tests; use `hypothesis` for the
order invariant. Use `codegraph-mcp` for entity relationships and `leta` for
LSP navigation when available. Use `execplans` to maintain this document,
`firecrawl-mcp` for external documentation gaps, `commit-message` for commits,
and `pr-creation` for publication. Read `.rules/python-00.md`,
`.rules/python-typing.md`, `.rules/python-return.md`,
`.rules/python-exception-design-raising-handling-and-logging.md`,
`.rules/python-pyproject.md`, and the context-manager/generator rules when
those constructs are used. Also read `docs/developers-guide.md`,
`docs/complexity-antipatterns-and-refactoring-strategies.md`, and
`docs/documentation-style-guide.md`.

## Conformance basis

All repository references in this section refer to the baseline commit above.
There is no separate Terms of Reference document for this slice.

- R1: `docs/roadmap.md` 1.2.1 and
  `docs/adrs/adr-0005-exact-wenmode-runtime-dependency.md` establish the exact
  Python dependency prerequisite. ADR-005 supersedes only ADR-004's earlier
  bounded dependency range; the exact pin takes precedence. EP-M2 discharges
  installed-use evidence E5.
- R2: roadmap 1.2.2 and `docs/syrupy-mdast-design.md` sections 5 and 7 require
  fresh construction and unchanged public AST data. EP-M1 discharges E1.
- R3: roadmap 1.2.2 and design sections 10 and 11 require sequential,
  overlapping, re-entrant, and worker independence. EP-M1 discharges E2–E4.
- R4: `docs/adrs/adr-0004-parser-profile-and-normalization.md` and design
  section 7 fix the GitHub profile and absent positions. EP-M1 discharges E1
  and E2; canonicalization and the full normative corpus stay out of scope.
- R5: `AGENTS.md`, the developer guide, Python rules, and documentation style
  guide govern tests, types, documentation, and gates. Both milestones require
  E6; EP-M2 updates the roadmap only after all evidence passes.

## Interfaces and dependencies

Add `parse_markdown(source: str) -> dict[str, object]` in
`syrupy_mdast/_wenmode.py`, subject to verifying the exact published return
annotation in 0.15.2. A dictionary of opaque values describes a raw boundary,
not a validated recursive domain schema. Prefer that annotation if it passes
`ty` without casts; if upstream exposes a suitable public exact type, document
and use it instead. Do not invent a parallel AST model to satisfy annotations.

Import `Parser` from `wenmode` and `github` from `wenmode.presets`. The
function constructs the profile and parser locally, calls `parse(source)` once,
calls `to_ast()` on the returned document once, and returns that object
directly. Document the string input, raw dictionary return, unchanged upstream
failures, and a short heading example. The underscore-prefixed module makes
this an internal interface without changing package exports.

## Verification plan

Axiom A1 is the pinned Wenmode public constructor/parse/to_ast contract and
GitHub preset semantics. Axiom A2 is ordinary Python allocation and call-stack
locality: independently constructed objects are distinct while live. Axiom A3
is the documented synchronization and process isolation supplied by Python and
pytest-xdist. Tests exercise repository use of these interfaces; they do not
prove Wenmode internals, every operating-system schedule, or crash isolation.

E1 verifies the call contract with a recording double patched at
`syrupy_mdast._wenmode.Parser` and a profile sentinel at the module's `github`.
In `tests/test_wenmode_adapter.py`, assert fresh profile and parser
construction per invocation, `positions=False`, exact source forwarding, call
counts, and returned-object identity. Retain constructed instances rather than
comparing recyclable integer IDs. Parameterize empty, ordinary, Unicode, and
incomplete Markdown; incomplete Markdown is normally valid parser input, not a
fabricated error. Raise distinct sentinel exceptions at construction, parse,
and to_ast; assert the same exception reaches the caller and a subsequent call
succeeds. Wrong profile, dropped positions, copied output, swallowed failures,
and cached parser mutations must fail focused tests for the expected reason.

E2 verifies sequence independence with real Wenmode in
`tests/test_wenmode_adapter.py` and `tests/test_wenmode_adapter_properties.py`.
Parse a document defining `[key]` and `[^note]`, then a document using those
labels without definitions, then one redefining them to different
destinations/text. Compare each output with a fresh direct Wenmode parse and
independently assert resolved destinations, unresolved-reference text, and
footnote payloads. Assert earlier returned trees remain unchanged after later
calls. Include empty documents and repeated calls.

Generate bounded lists of 1–8 short documents using Hypothesis: labels from a
small non-empty ASCII alphabet, ordinary-reference and footnote families,
with/without definitions, and differing targets. Compare each adapter result
with its fresh-parser result regardless of preceding documents; preserve copies
of prior results to detect later mutation. Use explicit examples for all three
classes (definition, unresolved use, redefinition), `event()` classifications,
and `--hypothesis-show-statistics`; no filtering should be necessary. Sampling
is not an exhaustive proof. The E1 identity assertion rejects a cached parser
even if upstream resets its state; an intentionally state-leaking double must
also make the sequence witness fail.

E3 verifies overlapping and nested lifetimes in
`tests/test_wenmode_adapter_concurrency.py`, with small private helpers in
`tests/support/wenmode_adapter.py` only if duplication warrants them. Run two
threads through a recording wrapper around real Parser instances. Start A and
wait for its parse-entry acknowledgement before starting B. Both must reach
`threading.Barrier(2)` inside parse before either proceeds. Separate events
then release B-complete before A-complete, with a second parameterization
reversing completion. Compare each result against its independently parsed
document, retain both instances, and assert distinct identity and source
association. Test ordinary references and footnotes with colliding labels. Put
five-second bounds on barriers, events, joins, and future results; release all
events and abort the barrier in cleanup.

Separately use a re-entrant double: while outer `parse` is active, invoke the
adapter once for an inner source, guarded to prevent infinite recursion. Record
outer-enter, inner-enter, inner-return, outer-return; assert distinct retained
parsers and correct outer/inner results. This rejects both global and
thread-local parser reuse. Negative controls cache one parser and serialize
calls behind a global lock: the former must violate identity, the latter must
fail the bounded overlap witness rather than hang. Restore every mutation
before the full gates. Deterministic schedules cover these two interleavings
and one nested level, not all possible schedules.

E4 verifies per-call allocation inside actual pytest-xdist workers in
`tests/test_wenmode_adapter_workers.py`. Run the focused worker test with
`-n 2 --dist=each` so both workers execute it. In each worker, retain two
parser instances, assert distinct identity, and check reference/footnote
isolation. Use `worker_id` and process identity for evidence; never compare
Python object IDs across processes. The distributed acceptance run must show
both `gw0` and `gw1` completed the test; a serial run is useful but does not
discharge E4. A per-worker singleton mutation must fail on each worker. Do not
start nested xdist sessions from tests or require a particular distribution from
`make test`.

E5 is end-to-end installation evidence: update the existing runtime probe to
import and call the internal seam, preserving empty, heading, and task-list
semantic assertions and all isolation checks. Add the short sequential
reference/footnote witness without broad snapshots. The existing wheel/editable
BDD suite must demonstrate identical results from both installed modes. Check
the adapter module's import origin as well as the package origin. In each
installation mode, temporarily patch the seam callable in the child process to
raise a uniquely named sentinel exception before running the probe. Require
that exception to fail the probe; the old direct-Wenmode probe would succeed
and must be rejected by this sensitivity check. Restore the callable and run
the real successful probe. Do not modify installed files or add a production
fault-injection interface. A probe that still calls Wenmode directly cannot
discharge this obligation.

E6 is the sequential gate set specified below. All evidence must belong to the
same candidate. Snapshot tests are unnecessary for allocation, exception, and
identity contracts: direct assertions are clearer. If implementation adds a
multivariant output fixture, use a narrowly scoped Syrupy snapshot alongside
semantic assertions, excluding worker IDs, paths, timings, and object IDs.

## Behavioural specification and contract scenarios

Add `tests/features/public_extension.feature` and bind its scenarios in
`tests/test_public_extension_bdd.py`. These are behavioural scenarios at the
public boundary: every step drives `syrupy_mdast.MarkdownAstSnapshotExtension`
or a Syrupy snapshot assertion configured with it, never `_wenmode`, and they
record what a consumer observes until roadmap 2.3.1 implements serialization.

```gherkin
Feature: Public Markdown snapshot extension defers serialization
  Scenario: A direct call defers serialization to the planned serializer
    Given the public Markdown snapshot extension
    When a caller serialises a valid Markdown document directly
    Then the extension refuses with the planned roadmap task

  Scenario: A registered Syrupy assertion is refused before serialization
    Given a Syrupy snapshot assertion using the public extension
    When that assertion compares a valid Markdown document
    Then the comparison does not match
    And Syrupy reports the rejected property control
    And the registered extension is the public type
```

The registered scenario compares through the assertion itself, which is the
path a consumer's `assert data == snapshot` takes, and reads Syrupy's recorded
diff. It cannot require the roadmap refusal there: Syrupy 6.0.0 supplies a
`matcher` callable to every serializer, so the extension's control guard fires
before serialization. The recorded diff therefore names the `matcher`
rejection, and satisfying that hook belongs to roadmap 2.3.1. The direct
scenario carries the `NotImplementedError` naming 2.3.1. The comparison also
records one failed snapshot in Syrupy's session report; pytest still passes,
because the scenarios assert on the recorded evidence rather than on an
assertion statement.

Add `tests/features/wenmode_adapter.feature` and bind its scenarios in
`tests/test_wenmode_adapter_bdd.py` using existing pytest-bdd conventions.
These are contract scenarios for the internal seam, written in BDD form:

```gherkin
Feature: Contract scenarios for independent internal Wenmode adapter calls
  Scenario: Definitions do not escape their document
    Given a document defining an ordinary reference and a footnote
    When it is parsed before a document using those labels without definitions
    Then the second tree equals its independent parse
    And the first tree remains unchanged

  Scenario: Later definitions belong to the later document
    Given two documents defining the same labels with different contents
    When both documents are parsed sequentially
    Then each tree contains only its own reference and footnote contents

  Scenario: An upstream failure does not poison the next call
    Given a parser double that fails during one parse
    When the failure is observed and a second document is parsed
    Then the original exception is propagated unchanged
    And the second call uses a new parser and succeeds
```

They are not behavioural acceptance of the public package: no public entrypoint
is reachable for the seam until roadmap 2.1.1 implements the parsing pipeline
and 2.3.1 the snapshot serialization. The installed probe is installation and
isolation evidence about the same seam, not evidence about the public surface.
Keep real-parser scenarios and deliberate double failures clearly
distinguished. Update the existing installation feature's parsing step to name
the internal adapter, keeping its wheel/editable scenarios and
missing-dependency failure.

## Milestones and plateaus

### EP-M1: Independent internal calls

Implement R2–R4 as one coherent tested change. Add the unit, property,
concurrency, worker, and contract-scenario files named above. Begin with the
smallest unit import/contract test: record the expected missing-module failure
before adding production code. Add the minimal function, then establish new
test sensitivity with temporary seeded faults before restoring it. For
test-first iterations, strict expected-failure markers may record an observed
red stage, but remove them before committing; never commit a failing suite.

Run focused E1–E4 tests, then the full E6 gates. Update design section 7 with
the concrete private path and its ownership/exception policy and update the
developer guide with focused testing commands and bounds in this same plateau.
Acceptance is fresh construction and correct isolated output, including both
worker reports, with no public API change. Check all R2–R4 links, unchanged
external assumptions, no new dependency/trust boundary/persisted format, and no
speculative backend abstraction. Commit only the green candidate.

Recovery is to revert this unshipped atomic commit or correct the failed test
and rerun the affected checks, then all gates. No compatibility machinery is
needed. Installed-use coverage and roadmap completion remain for EP-M2.

### EP-M2: Installed evidence and delivery documentation

Discharge R1 and R5 by routing the existing installation probe through the seam
and updating its BDD wording. First run the E5 raising-sentinel invocation
witness against the old direct-parser probe and observe the expected
sensitivity-check failure; then make the minimal probe change. Preserve
audit-hook negative controls and wheel/editable origin checks. Read the
scripting standards before editing this helper.

Run E5. Reconcile design and developer guidance with observed behaviour. Update
`docs/users-guide.md` only with accurate consumer-facing status: Python-only
installation is unchanged, and the internal seam does not yet enable public
Markdown comparison. Do not advertise a private API as a consumer entrypoint.
Update `docs/contents.md` if another document is introduced. Once focused
acceptance evidence is recorded, provisionally mark roadmap 1.2.2 `[x]` (done),
leaving 1.2.3 and later work open. Run the complete E6 sequence on this final
candidate, including the documentation and roadmap edits. Retain the done
marker and commit only if every gate succeeds; otherwise restore the open
marker until the failure is resolved and rerun all gates.

Check R1–R5 and every evidence link, resolve or explicitly approve discoveries,
and confirm no public behaviour, dependency, trust boundary, or persisted
format has changed. Recovery is to revert this milestone's commit while
retaining the valid EP-M1 seam. No compatibility shim is needed. Remaining gaps
are the explicitly deferred parser corpus, canonicalizer, and public pipeline.

## Concrete steps and acceptance

Run from the repository root on the named task branch. Recheck prerequisite
1.2.1 and the clean working tree before implementation. Use the shared default
caches. The existing Makefile is the authority for environment setup; the
focused pytest commands below use its `uv` environment after `make build`.

```bash
uv run pytest -v tests/test_wenmode_adapter.py
uv run pytest -v tests/test_public_extension_bdd.py
uv run pytest -v tests/test_wenmode_adapter_properties.py --hypothesis-show-statistics
uv run pytest -v tests/test_wenmode_adapter_concurrency.py tests/test_wenmode_adapter_bdd.py
uv run pytest -v -n 2 --dist=each tests/test_wenmode_adapter_workers.py
uv run pytest -v tests/test_wenmode_dependency_bdd.py tests/test_package_boundary.py
```

The first command initially fails because the seam is absent. After the change,
all selected tests must pass. Record actual counts rather than predicting them;
worker evidence must include successful execution on both worker IDs. Red
negative controls must fail their intended assertion, not merely collection,
timeout infrastructure, or an unrelated dependency error.

After each major milestone, the implementing agent runs `make fmt`, logs its
output, and inspects the resulting diff. The `scrutineer` agent cannot edit
tracked files; delegate only the subsequent checks to it. Do not overlap gates
for this candidate. Use a new milestone/attempt label on every run so evidence
is never overwritten. Execute the sequence in a failure-stopping subshell:

```bash
(
set -euo pipefail
run_label=ep-m1-attempt1
# Implementing agent runs formatting before delegating the checks.
make fmt 2>&1 | tee /tmp/fmt-syrupy-mdast-${run_label}.out
make check-fmt 2>&1 | tee /tmp/check-fmt-syrupy-mdast-${run_label}.out
make typecheck 2>&1 | tee /tmp/typecheck-syrupy-mdast-${run_label}.out
make lint 2>&1 | tee /tmp/lint-syrupy-mdast-${run_label}.out
make test 2>&1 | tee /tmp/test-syrupy-mdast-${run_label}.out
make audit 2>&1 | tee /tmp/audit-syrupy-mdast-${run_label}.out
make markdownlint 2>&1 | tee /tmp/markdownlint-syrupy-mdast-${run_label}.out
make nixie 2>&1 | tee /tmp/nixie-syrupy-mdast-${run_label}.out
)
```

Execute each command only after the previous command succeeds; the block is a
sequence specification, not permission to continue after failures. Expected
results are exit status zero, no formatting/type/lint/audit failures, a passing
pytest summary, and valid Markdown/Mermaid. Inspect formatter changes and
restart validation after any candidate edit. Use `make test WITH_ACT=1` only if
workflow changes require local GitHub Actions validation; none are planned. For
this planning-only PR, validate formatting and documentation and run the four
explicitly requested check-fmt/typecheck/lint/test gates before publication.

## Idempotence and recovery

Tests and validation may be repeated. Keep temporary mutation experiments
uncommitted, restore only owned edits, and preserve unrelated work. Do not
regenerate normative goldens. If an installation fixture fails, retain its logs
and import-origin evidence, diagnose the failure, then rerun the failed probe
after correction. An unavailable service or gate is unknown, not passed. Commit
each validated plateau with the `commit-message` skill; push using the
repository's clean-environment SSH procedure. Refresh the remote-tracking ref
and verify the remote SHA. Keep this PR a draft and this plan DRAFT until
explicit implementation approval is recorded.

## Artefacts and external references

Consulted on 2026-11-03 using Firecrawl: Wenmode's usage guide documents
`parse(source).to_ast()` and position control; parser reuse documentation is
not evidence of concurrent shared-parser safety.[^1] pytest-xdist documents
worker identification; use its per-worker execution mode for explicit worker
acceptance.[^2] The pinned local release remains authoritative when current
online documentation differs.

[^1]: [Wenmode usage guide](https://wenmode.lepture.com/usage/).
[^2]: [pytest-xdist how-tos](https://pytest-xdist.readthedocs.io/en/stable/how-to.html).

Revision note (2026-11-03): Initial approval-gated plan defines the minimal
seam, its independent-state obligations, bounded witnesses, and installation
reuse. Implementation remains pending approval.

Revision note (2026-11-03, expert review): Correct architecture traceability
and ADR precedence; make thread entry order and installed invocation negative
controls explicit; assign formatting to the implementor and preserve gate logs
with failure-stopping commands. All final edits precede candidate validation.
