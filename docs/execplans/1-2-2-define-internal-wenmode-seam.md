# Define the internal Wenmode seam (1.2.2)

Status: DRAFT — approval required before implementation.

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
than 16 non-ExecPlan files or 900 net lines of code and other documentation.
ExecPlan files are excluded from both counts. A required third-party annotation
workaround involving `Any`, a cast, or a suppression requires evidence and
review before adoption. Three unsuccessful fixes for the same failure trigger
reassessment, not a weaker assertion. There is no elapsed-time cutoff.

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
- [ ] Complete plan-only validation and publish draft PR.
- [ ] Obtain explicit approval for implementation.
- [ ] EP-M1: implement and validate the seam and isolation obligations.
- [ ] EP-M2: validate installed use, reconcile documentation, and mark 1.2.2
      done.

## Surprises & discoveries

The existing installation probe in `tests/support/wenmode_runtime_probe.py`
constructs and reuses a Wenmode parser directly. It proves the dependency
boundary, not a package-owned seam. Switching that probe to the seam is needed
for this slice's integration evidence.

`docs/repository-layout.md` is referenced by instructions but absent at the
planning baseline. Use `docs/contents.md` and the explicit paths below for
orientation; creating a repository-wide layout document is outside this slice.

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

## Outcomes & retrospective

Planning only. No feature code is implemented, and roadmap 1.2.2 remains open.
On completion, record exact commits, red/green evidence, gate logs, exercised
bounds, and any residual limitations. Reconcile discoveries against every
conformance source before changing this plan to COMPLETE.

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
  `docs/adr-005-exact-wenmode-runtime-dependency.md` establish the exact Python
  dependency prerequisite. ADR-005 supersedes only ADR-004's earlier bounded
  dependency range; the exact pin takes precedence. EP-M2 discharges
  installed-use evidence E5.
- R2: roadmap 1.2.2 and `docs/syrupy-mdast-design.md` sections 5 and 7 require
  fresh construction and unchanged public AST data. EP-M1 discharges E1.
- R3: roadmap 1.2.2 and design sections 10 and 11 require sequential,
  overlapping, re-entrant, and worker independence. EP-M1 discharges E2–E4.
- R4: `docs/adr-004-parser-profile-and-normalization.md` and design section 7
  fix the GitHub profile and absent positions. EP-M1 discharges E1 and E2;
  canonicalization and the full normative corpus stay out of scope.
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

## Behavioural specification

Add `tests/features/wenmode_adapter.feature` and bind its scenarios in
`tests/test_wenmode_adapter_bdd.py` using existing pytest-bdd conventions:

```gherkin
Feature: Independent Wenmode adapter calls
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

Keep real-parser scenarios and deliberate double failures clearly
distinguished. Update the existing installation feature's parsing step to name
the internal adapter, keeping its wheel/editable scenarios and
missing-dependency failure.

## Milestones and plateaus

### EP-M1: Independent internal calls

Implement R2–R4 as one coherent tested change. Add the unit, property,
concurrency, worker, and behavioural files named above. Begin with the smallest
unit import/contract test: record the expected missing-module failure before
adding production code. Add the minimal function, then establish new test
sensitivity with temporary seeded faults before restoring it. For test-first
iterations, strict expected-failure markers may record an observed red stage,
but remove them before committing; never commit a failing suite.

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
