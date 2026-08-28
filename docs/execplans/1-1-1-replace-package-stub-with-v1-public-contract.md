# Replace the generated package stub with the v1 public contract

This ExecPlan (execution plan) is a living document. The sections
`Constraints`, `Tolerances`, `Risks`, `Progress`, `Surprises & discoveries`,
`Decision log`, `Outcomes & retrospective`, `Conformance basis`, and
`Verification plan` must be kept up to date as work proceeds.

Status: DRAFT

## Purpose / big picture

Today `syrupy_mdast` is a Copier-template stub. It exports one function,
`hello()`, which returns the string `"hello from Python"`. It declares no
runtime dependencies, and its `README.md` describes it as an example package.
Nothing in the repository expresses the product this project intends to ship.

After this change, a developer who installs the package gets exactly two public
names, `MarkdownAstError` and `MarkdownAstSnapshotExtension`, matching the
technical design's §6. They can import them, catch the error type, subclass the
extension, and read a documented, version-bounded statement of which Python and
Syrupy releases are supported. Attempting to snapshot a non-string, or to pass
Syrupy's `exclude`, `include`, or `matcher` controls, fails immediately with the
declared exception type and an actionable message rather than silently
producing a misleading snapshot.

Observable success, in one command:

```bash
uv run python -c "
import syrupy_mdast
print(sorted(syrupy_mdast.__all__))
print(syrupy_mdast.MarkdownAstSnapshotExtension.file_extension)
"
```

Expected output:

```plaintext
['MarkdownAstError', 'MarkdownAstSnapshotExtension']
mdast.json
```

And `uv run python -c "import syrupy_mdast; syrupy_mdast.hello()"` must fail
with `AttributeError`.

What this change deliberately does **not** deliver: parsing, canonicalization,
and JSON serialization. Those arrive in roadmap phase 2. The single
serialization seam raises `NotImplementedError` naming roadmap task 2.3.1. This
plan explains below why that is a coherent plateau rather than a facade.

## Constraints

These are hard invariants. Violating one requires escalation, not a workaround.

1. The package must remain pure Python. No Bun, Node.js, TypeScript,
   JavaScript manifest, lockfile, or installed JavaScript package asset may
   become a runtime, build, test, or wheel dependency. This is design §2.3 and
   §13.
2. `syrupy_mdast/_core/` must import neither `syrupy` nor `wenmode`, nor any
   input/output module. It is the dependency-free domain core of design §5.
3. The public surface must be exactly `MarkdownAstError` and
   `MarkdownAstSnapshotExtension`. No other non-underscore attribute may be
   reachable from the `syrupy_mdast` namespace.
4. `MarkdownAstError.category` values are drawn from the closed set fixed by
   design §9 Table 2. This plan may not invent a category, and specifically may
   not add a "not implemented" category.
5. No release may be cut between this task and roadmap 2.3.1. The version stays
   at `0.1.0` and the package is classified `Development Status :: 2 -
   Pre-Alpha`. The plateau claim in this plan depends on this.
6. `Wenmode` must not be added as a dependency here. That is roadmap task
   1.2.1, and the release to pin is decided by the roadmap 1.1.2 ADR.
7. All four commit gates must pass before each commit: `make check-fmt`,
   `make lint`, `make typecheck`, `make test`.
8. Prose is en-GB-oxendict, wrapped at 80 columns; code wraps at 120.

## Tolerances (exception triggers)

Stop and escalate rather than improvising when any of these is reached.

1. Scope: if delivery requires touching more than 20 files, stop and escalate.
2. Interface: if design §6's two-name surface cannot be delivered as written,
   stop and escalate. Do not add or rename a public name unilaterally.
3. Dependencies: `syrupy` is the only new runtime dependency authorised by this
   plan. Any further runtime dependency, or any new dev dependency beyond those
   named in `Interfaces and dependencies`, triggers escalation.
4. Lint suppression: at most two `[tool.skylos.whitelist.documented]` entries
   are authorised (`file_extension` and `_write_mode`). A third finding that
   cannot be resolved by making the symbol genuinely live triggers escalation.
5. Iterations: if a single gate still fails after four remediation attempts,
   stop and escalate with the captured log path.
6. Roadmap: this plan already carries one approved roadmap amendment (see
   DEC-3). A second amendment triggers escalation.
7. Ambiguity: if design §6 and the roadmap appear to conflict in a way not
   already resolved in `Decision log`, stop and present options.

## Risks

1. Risk: Skylos flags `file_extension` and `_write_mode` as unused variables
   (`SKY-U003`), and neither documented remedy works.
   Severity: high. Likelihood: high — empirically observed during planning.
   Mitigation: use bare symbol names in
   `[tool.skylos.whitelist.documented]`, update
   `tests/test_skylos_lint_contract.py::_DOCUMENTED_WHITELIST_NAMES` in the
   same commit, and correct the guidance in `AGENTS.md` and
   `docs/developers-guide.md`. See EP-M4 and DEC-7.

2. Risk: Ruff `PLR6301` (no-self-use) fires on `serialize()` because the method
   validates its arguments without reading `self`.
   Severity: low. Likelihood: medium.
   Mitigation: prefer naming the instance in the diagnostic, which is
   independently useful to the caller. If that is insufficient, apply a scoped
   `# noqa: PLR6301` carrying a link to roadmap 2.3.1, per `AGENTS.md`'s
   temporary-suppression rule. Verify before choosing; do not pre-suppress.

3. Risk: a declared bound is never resolved against. `uv` resolves
   highest-compatible, so without intervention CI exercises Syrupy 6.x on
   Python 3.13 only, while the package declares `syrupy>=5.0.0,<7.0.0` and
   `requires-python = ">=3.12"`.
   Severity: medium. Likelihood: medium.
   Mitigation: EP-M5 adds a `compatibility-matrix` job to
   `.github/workflows/ci.yml` covering Python 3.12, 3.13, and 3.14 against both
   the declared Syrupy floor and the latest resolvable release. `INV-6` asserts
   that the floor exercised by the matrix equals the floor declared in
   `pyproject.toml`, so the declaration and the evidence cannot drift apart.

4. Risk: `_write_mode` is a private Syrupy attribute carrying no compatibility
   promise, yet is depended upon across two major versions.
   Severity: medium. Likelihood: low.
   Mitigation: `INV-4` asserts its continued existence, converting a silent
   behaviour change into a failing test in the pull request that bumps Syrupy.
   The EP-M5 matrix now exercises that assertion at both ends of the declared
   range rather than at one resolved point. Recorded in design §13 as the
   stated reason for the upper bound.

5. Risk: deleting `hello()` before deleting `tests/test_stub.py` breaks pytest
   at collection time, which under `-n auto` surfaces as xdist worker-crash
   output rather than a clean assertion failure.
   Severity: low. Likelihood: high if ordering is ignored.
   Mitigation: EP-M1 deletes the test first. This ordering is mandatory.

6. Risk: `uv.lock` is not regenerated after adding the first runtime
   dependency, so CI diverges from the working tree.
   Severity: medium. Likelihood: medium.
   Mitigation: EP-M2 runs `make build` and commits the regenerated lockfile in
   the same commit as the `pyproject.toml` change.

7. Risk: the wheel omits `syrupy_mdast/_core/` or `py.typed`.
   Severity: medium. Likelihood: low.
   Mitigation: `_core/__init__.py` exists so hatchling treats it as a
   subpackage; EP-M7 inspects the built wheel.

8. Risk: a matrix combination fails for a reason unrelated to this package —
   for example an old Syrupy release lacking Python 3.14 support.
   Severity: low. Likelihood: medium.
   Mitigation: `fail-fast: false` so every leg reports independently. A
   genuinely unsupportable combination is recorded with a `matrix.exclude`
   entry carrying a comment naming the incompatibility. Do not narrow the
   declared range to make a leg pass without first deciding, deliberately, that
   the range was wrong.

## Progress

- [ ] EP-M1 Remove the generated stub.
- [ ] EP-M2 Declare package metadata and the Syrupy runtime dependency.
- [ ] EP-M3 Establish the dependency-free domain core and its import guard.
- [ ] EP-M4 Deliver the Syrupy adapter and the public API contract test.
- [ ] EP-M5 Add the Python and Syrupy compatibility matrix to CI.
- [ ] EP-M6 Update documentation and correct the Skylos guidance.
- [ ] EP-M7 Full gate sweep, wheel inspection, and roadmap tick.

Update this section at every stopping point, with a UTC timestamp, splitting a
partially completed milestone into "done" and "remaining" rather than leaving
it ambiguous.

## Surprises & discoveries

These were established during planning, before implementation began. They are
recorded here because each one overturned an assumption that a reasonable
implementer would otherwise make.

1. Observation: Skylos does **not** flag a class re-exported through `__all__`
   with no in-package caller.
   Evidence: a scratch package mirroring this layout scanned clean, exit 0,
   under the repository's exact gate command with `strict = true`.
   Impact: no entry-point rule is needed for `MarkdownAstError` or
   `MarkdownAstSnapshotExtension` themselves. `_RUNTIME_ENTRY_POINT_NAMES` in
   `tests/test_skylos_lint_contract.py` stays an empty frozenset.

2. Observation: Skylos **does** flag class attributes that override an
   inherited attribute, and flags every parameter of a method whose body does
   not read them.
   Evidence: a probe of the design §6 class shape with a stubbed `serialize()`
   returned six findings — `SKY-U003` for `file_extension` and `_write_mode`,
   and `SKY-U006` for `data`, `exclude`, `include`, and `matcher`.
   Impact: decisive. Implementing §6's input contract makes all four parameters
   live, so a *real* implementation costs four fewer findings than a stub. This
   is the primary technical argument behind DEC-3.

3. Observation: Skylos 4.33.2 matches whitelist entries on the **bare symbol
   name only**. A qualified name is accepted by `skylos whitelist`, which
   prints a success tick and writes it to `pyproject.toml`, and then suppresses
   nothing. A typed `[[tool.skylos.dead_code.entrypoints]]` rule does not model
   class attributes at all and also fails to suppress.
   Evidence: five spellings tested against one finding; only `file_extension`
   and `*file_extension` suppressed it.
   Impact: both remedies documented in `AGENTS.md` and
   `docs/developers-guide.md` are wrong for this construct. EP-M6 corrects
   them. Note the blast radius: a bare-name entry is repository-global.

4. Observation: `ambrleaks` scans only `.ambr` files, so it is structurally
   blind to this project's own `.mdast.json` snapshots.
   Evidence: byte-identical content in `__snapshots__/t.ambr` produced one
   finding and exit 1; in `__snapshots__/t.mdast.json` it produced none and
   exit 0.
   Impact: not a blocker for this task, which writes no snapshots, but this is
   the task that fixes `file_extension = "mdast.json"`. EP-M6 records the gap
   in the developers' guide and adds a roadmap item so it is closed before
   roadmap 2.3.1 begins writing snapshots.

5. Observation: `requires-python = ">=3.12"` is **already declared** at
   `pyproject.toml` line 6.
   Evidence: direct inspection.
   Impact: the roadmap bullet "declare the supported Python and Syrupy ranges"
   is half-complete. Only the Syrupy range is new work here.

6. Observation: `syrupy` is absent from `uv.lock`; the sole match is the
   project's own name.
   Evidence: `grep -n 'name = "syrupy"' uv.lock` returns nothing.
   Impact: the lockfile must be regenerated and committed in EP-M2.

7. Observation: the repository has no `py.typed` marker, so under PEP 561 a
   consumer's type checker must ignore every annotation the package ships.
   Evidence: `find . -name py.typed` returns nothing.
   Impact: design §2.1's goal of a "narrow and fully typed" public API is
   currently unobservable downstream. EP-M2 adds the marker.

## Decision log

- DEC-1: Lay out the package as `syrupy_mdast/_core/` (a package containing
  `__init__.py` and `errors.py`), `syrupy_mdast/_extension.py`, and
  `syrupy_mdast/__init__.py` re-exporting exactly two names.
  Rationale: design §5 mandates a dependency-free core with narrow adapters
  around it. A `_core` *package* rather than a single module is justified
  within two roadmap tasks — by 2.1.2 the core additionally holds
  canonicalization, AST-shape validation, the normative field-order constant,
  and two resource limits, and `AGENTS.md` caps files at 400 lines. This is
  known growth, not speculation. `_core/__init__.py` stays a pure re-export
  with no logic, so relocating `errors.py` later touches no call site.
  Date/Author: 2026-08-28, planning agent, on Pandalump's recommendation.

- DEC-2: Name the Syrupy adapter module `_extension.py`, not `extension.py`.
  Rationale: `from .extension import ...` binds `extension` as an attribute of
  the `syrupy_mdast` namespace. `__all__` governs `import *` only, not
  attribute access, so a public module name would itself be a public export and
  would defeat the milestone's own success criterion. With every module
  private, the API-stability assertion becomes a clean set equality, and
  roadmap 2.3.2's promise that "a consumer can copy the recipe without
  importing internal modules" becomes structurally true.
  Date/Author: 2026-08-28, raised independently by Telefono and Pandalump.

- DEC-3: **Approved roadmap amendment.** Deliver design §6's input contract —
  `TypeError` for non-`str` data, `ValueError` for non-`None` `exclude`,
  `include`, or `matcher` — in this task rather than in roadmap 2.3.1.
  Rationale: three reinforcing arguments. It needs no parser, canonicalizer, or
  pipeline, so it is deliverable now. It converts the milestone from a facade
  into a genuine plateau with enforced, tested behaviour, satisfying the
  ExecPlan rule against compatibility theatre. And empirically it *removes*
  four Skylos `SKY-U006` findings, because a stubbed `serialize()` leaves all
  four parameters unread. Roadmap 2.3.1 correspondingly shrinks to wiring the
  pipeline into the seam. Approved by the user on 2026-08-28.
  Date/Author: 2026-08-28, user-approved.

- DEC-4: The serialization seam raises `NotImplementedError`, not
  `MarkdownAstError`.
  Rationale: design §6 declares `MarkdownAstError`'s `category` values stable
  and §9 Table 2 enumerates them exhaustively. There is no "not implemented"
  category, and inventing one would inject a temporary implementation state
  into a versioned public taxonomy. `NotImplementedError` sits outside the
  documented failure contract and therefore cannot be depended upon. Its
  message must name roadmap task 2.3.1 so its removal is a deliberate,
  test-visible act.
  Date/Author: 2026-08-28, planning agent.

- DEC-5: Model `MarkdownAstError.category` as a `str` attribute backed by
  module-level `typ.Final` constants and a `CATEGORIES` tuple, not as a
  `StrEnum`.
  Rationale: an unexported enum used as the type of a public attribute is a
  leaky contract — a typed downstream consumer has no importable annotation and
  must widen to `str` anyway. Declaring `category: str` now permits a later
  narrowing to `Literal[...]` in a minor release, which is backward-compatible
  for every reader because `Literal` is a subtype of `str`; promoting a private
  enum to public later is a rename-shaped break. Start wide, narrow later,
  never the reverse. `.rules/python-typing.md` prefers `StrEnum` "where values
  are unimportant"; here the values *are* the public contract, so that
  precondition does not hold and the rule does not bind.
  Date/Author: 2026-08-28, on Telefono's recommendation, over Dinolump's
  contrary suggestion.

- DEC-6: `category` is a required keyword-only constructor argument, and
  `MarkdownAstError` defines an explicit `__reduce__`.
  Rationale: an error documented as always carrying a stable category must not
  be constructible without one, or a raiser could silently emit an
  uncategorised error and break Table 2. Keyword-only because positional
  `MarkdownAstError("...", "parse")` invites argument transposition. The
  explicit `__reduce__` is required because `BaseException.__reduce__`
  reconstructs via `type(exc)(*exc.args)`, which raises `TypeError` for a
  required keyword-only argument — breaking `copy.copy`, `pickle`, and
  propagation across any executor boundary. Cheap now, expensive after
  ratification.
  Date/Author: 2026-08-28, on Telefono's R1.

- DEC-7: Resolve the Skylos `SKY-U003` findings with bare-name entries in
  `[tool.skylos.whitelist.documented]`, and correct the guidance that points at
  the broken remedies.
  Rationale: entry-point rules were empirically shown not to model class
  attributes, and qualified whitelist names silently no-op. Do **not** add an
  in-package reader purely to satisfy the linter — that is production code
  shaped by a tool, which ADR-001's policy exists to prevent. Reading
  `self.file_extension` inside a diagnostic message is acceptable only where it
  genuinely improves the message. Approved by the user on 2026-08-28.
  Date/Author: 2026-08-28, user-approved.

- DEC-8: Declare `syrupy>=5.0.0,<7.0.0`.
  Rationale: 5.0.0 is the release that renamed `_file_extension` to
  `file_extension`, the public attribute design §6 explicitly depends upon and
  explicitly justifies. Both boundary releases were confirmed during planning
  to expose `WriteMode`, `SingleFileSnapshotExtension`, `file_extension`,
  `_write_mode`, and an identical `serialize` signature. The upper bound caps
  an unreviewed major that could move the single-file lifecycle §6 and §10 rely
  on. Note the asymmetry worth stating in the compatibility policy: Wenmode
  defines the persisted bytes and is therefore pinned exactly per §13; Syrupy
  defines storage and lifecycle and therefore takes a range. Approved by the
  user on 2026-08-28.
  Date/Author: 2026-08-28, user-approved.

- DEC-9: Defer `pytest-bdd`, `tests/features/`, and `tests/steps/` to roadmap
  2.3.1.
  Rationale: this task introduces two type declarations, a dependency
  declaration, and deletions. A Gherkin scenario for "a consumer imports the
  package" restates the unit test across three additional files without adding
  behavioural meaning. It would force a `conftest.py` that changes collection
  for every later test, and each step function owes 100% `interrogate` coverage
  and NumPy-style `D`/`DOC` conformance. The first genuine Given/When/Then
  arrives at 2.3.1 (snapshot create, update, delete) and the layout should be
  chosen knowing what it must serve. The existing forward-looking
  `tests/steps/*.py` entry in `per-file-ignores` is inherited Copier
  boilerplate, not a commitment. Approved by the user on 2026-08-28.
  Date/Author: 2026-08-28, user-approved.

- DEC-10: Add no Syrupy snapshot test in this task.
  Rationale: there is no output format yet. The only extension available today
  is Syrupy's default amber, so a snapshot here would mean self-snapshotting a
  snapshot-extension package using a different extension's format — actively
  confusing, and precisely the "generic dump" `AGENTS.md` proscribes. It would
  also make the `ambrleaks` tier load-bearing for an artefact intended for
  deletion. The first legitimate snapshot is a `.mdast.json` at roadmap 2.3.1.
  Date/Author: 2026-08-28, on Dinolump's recommendation.

- DEC-11: Add no installed-wheel end-to-end test in this task.
  Rationale: roadmap 1.2.1 owns wheel-purity confirmation and 2.4.1 owns the
  installed-wheel suite. The interesting assertion — that no JavaScript asset
  is present — is untestable until Wenmode is a dependency, since today no
  plausible source of one exists. What remains would test hatchling, not this
  change. A one-off wheel inspection is retained in EP-M7 as a manual
  acceptance step rather than a suite test, keeping it out of the 30-second
  pytest timeout and off the `-n auto` critical path.
  Date/Author: 2026-08-28, on Dinolump's recommendation.

- DEC-12: Leave `docs/users-guide.md` untouched.
  Rationale: it is wholly Copier-template content describing the template's own
  quality gates, including Rust extension guidance inapplicable to this
  project. Roadmap 3.1.1 replaces it wholesale. Appending a compatibility
  section to it would produce an incoherent artefact that 3.1.1 deletes. The
  compatibility policy therefore lands in `README.md` (consumer-facing) and
  design §13 (normative). Recorded so the omission reads as a decision.
  Date/Author: 2026-08-28, on Dinolump's recommendation.

- DEC-13: Leave `docs/adr-001-python-lint-architecture.md` and the
  Pyright-versus-`ty` tension in `.rules/python-00.md` alone.
  Rationale: ADR-001 uses a Nygard-style layout where
  `docs/documentation-style-guide.md` prescribes a different template, but it
  concerns lint architecture and has no connection to the v1 contract; roadmap
  3.1.2 already owns documentation reconciliation. `.rules/python-00.md`
  mandates strict Pyright, whereas the actual gate is `ty`; that file is shared
  estate-wide boilerplate and amending it exceeds this repository. This plan's
  only obligation is to tell the implementer plainly which typechecker to run.
  A handoff note requires that the roadmap 1.1.2 ADR follow the documented
  template so the deviation stops spreading.
  Date/Author: 2026-08-28, on Dinolump's recommendation.

- DEC-14: Add the Python and Syrupy compatibility matrix in this task rather
  than deferring it to roadmap 2.4.2.
  Rationale: the plan originally recorded the untested `>=5.0.0` floor as an
  accepted residual gap. That was the wrong call. The declared bounds are
  ratified *here*, and a bound nobody resolves against is a claim rather than a
  contract — the same objection Telefono and Pandalump raised independently
  against the floor and the Python range. The cost is one additive CI job and
  one contract test; the cost of discovering the floor was wrong is a published
  package whose metadata lies to a resolver. Roadmap 2.4.2 retains the wider
  combinatorial matrix over Wenmode releases and pytest-xdist, which this does
  not attempt. Requested by the user on 2026-08-29.
  Date/Author: 2026-08-29, user-requested.

- DEC-15: Pin the Syrupy floor by explicit install plus `uv run --no-sync`,
  not by `uv sync --resolution lowest-direct`.
  Rationale: `lowest-direct` floors every direct dependency including the `dev`
  group, where `pytest` is declared with no lower bound and `hypothesis` only as
  `>=6,<7`. It would resolve absurd tooling versions and produce failures that
  say nothing about the Syrupy bound under test. Installing the exact floor
  release keeps the experiment aimed at the one variable this matrix exists to
  vary. `--no-sync` is required because `uv run` otherwise re-syncs and
  silently restores the resolved version, which would make every floor leg a
  duplicate of the latest leg — a vacuous pass.
  Date/Author: 2026-08-29, planning agent.

## Outcomes & retrospective

To be completed at EP-M7. Before setting this plan to `COMPLETE`, reconcile
every implementation discovery against `Conformance basis`: update design §13
if the Syrupy range changes, record any purely mechanical difference here, and
confirm no upstream deviation remains unaccepted.

## Context and orientation

You are working in a Python library repository. It builds with `hatchling`,
is managed with `uv`, and targets Python 3.12 and later.

The product this repository is building is a Syrupy extension. **Syrupy** is a
snapshot-testing plugin for pytest: a test asserts a value against a stored
file, and Syrupy handles creating, comparing, updating, and deleting those
files. A **snapshot extension** customises how a value is serialized and what
file extension it is stored under. **mdast** is a Markdown Abstract Syntax Tree
format. The product's purpose is to compare Markdown by its parsed structure
rather than by its raw source text, so that reformatting Markdown does not
produce snapshot churn.

Files that matter here:

1. `syrupy_mdast/__init__.py` — currently the generated stub. It imports an
   optional Rust extension module named `_syrupy_mdast_rs` via `importlib` and
   falls back to `syrupy_mdast/pure.py`. No Rust extension exists in this
   repository and `.github/workflows/release.yml` builds a pure-Python wheel,
   so this fallback is dead scaffolding.
2. `syrupy_mdast/pure.py` — defines `hello()`. To be deleted.
3. `tests/test_stub.py` — asserts `hello() == "hello from Python"`. To be
   deleted **first**, before `hello()` itself.
4. `pyproject.toml` — 442 lines. `[project]` is at lines 1-8 with
   `dependencies = []`. Extensive Ruff, Pylint, and Skylos configuration
   follows. `[tool.hatch.build.targets.wheel]` at line 439 sets
   `packages = ["syrupy_mdast"]`.
5. `tests/` — every existing test except `test_stub.py` is an *infrastructure
   contract* test that parses the `Makefile` or CI workflow YAML and asserts
   exact token sequences. `tests/support/make_contract.py` holds the shared
   helpers. Read `tests/test_toolchain_contract.py` for the pattern to copy.

The gate you must satisfy is `make all`, which runs `build`, `check-fmt`,
`lint`, `typecheck`, and `test` in order. `make lint` runs six blocking tiers:
Ruff, `interrogate --fail-under 100`, a PyPy-backed Pylint pass, a
`df12-python-lints` Pylint pass, `ambrleaks`, and a strict Skylos dead-code
gate. The Skylos tier scans `syrupy_mdast` only, with `tests` **excluded** —
which means a test that reads a symbol does not make that symbol live.

Two environment notes that will otherwise cost you an hour. `make test`
requires a pinned Rust-built `makeutil` binary on `PATH`; the bootstrap command
is in `docs/developers-guide.md`. And the typechecker is `ty`, invoked by
`make typecheck` — `pyright` is an unconfigured dev dependency and
`.rules/python-00.md`'s Pyright wording is not enforced here. Do not run
Pyright.

### Signposted reading

Read these, in this order, before writing code:

1. `docs/syrupy-mdast-design.md` §6 — the exact public surface, and the
   rationale for `file_extension` rather than `_file_extension`. This is the
   single most important passage for this task. Then §5 (core and adapter
   split), §9 Table 2 (the category values), and §2.3 with §13
   (compatibility).
2. `docs/roadmap.md` task 1.1.1 and its neighbours 1.1.2, 1.2.1, 2.3.1, and
   2.4.1 — so you know what *not* to build. Scope discipline is the main
   failure mode here.
3. `AGENTS.md` — "Change quality and committing" for the gate commands and the
   Skylos policy, and "Python verification and testing".
4. `docs/developers-guide.md` — the Skylos dead-code gate section, and the
   `makeutil` bootstrap.
5. `pyproject.toml` `[tool.ruff.lint.flake8-import-conventions]` — `from
   typing import ...` is **banned**. Use `import typing as typ` and
   `import collections.abc as cabc`. This silently breaks the obvious import
   style and the error message is not self-explanatory.
6. `.rules/python-exception-design-raising-handling-and-logging.md` — governs
   `MarkdownAstError`'s shape, including the N818 `Error` suffix and the
   "construct the message once, pass it once" rule (EM101/EM102).
7. `.rules/python-typing.md` — `from __future__ import annotations`,
   `typ.override`, and `typ.Final`.
8. `tests/test_toolchain_contract.py` and `tests/support/make_contract.py` —
   the working pattern to copy for the manifest contract test.

Relevant skills: `python-router`, then `python-errors-and-logging` and
`python-types-and-apis`; `hypothesis` for the one property test;
`en-gb-oxendict`; `execplans`.

Explicitly **out of scope, do not read**:
`docs/complexity-antipatterns-and-refactoring-strategies.md`,
`docs/scripting-standards.md`,
`docs/local-validation-of-github-actions-with-act-and-pytest.md`,
`.rules/python-generators.md`, `.rules/python-context-managers.md`,
`.rules/python-return.md`, and design §§7-8 and §§11-12. Nothing here iterates,
manages a resource, parses Markdown, or invokes an external command.

## Conformance basis

There is no Terms of Reference document for this project. The governing
upstream artefacts are:

1. `docs/syrupy-mdast-design.md`, revision dated 2026-07-28, status "Proposed
   living design". Sections §2.1, §2.3, §5, §6, §9, and §13 bind this task.
2. `docs/roadmap.md` task 1.1.1, as amended by DEC-3.
3. `docs/adr-001-python-lint-architecture.md` — governs the Skylos
   false-positive policy that DEC-7 operates within.
4. `AGENTS.md`, `.rules/python-*.md`, and `docs/documentation-style-guide.md`
   as governing standards.

No ADR yet records the snapshot contract; that is roadmap task 1.1.2, which
this task must not pre-empt. A handoff obligation applies: **the 1.1.2 ADR must
follow `docs/documentation-style-guide.md`'s template verbatim**, unlike
ADR-001.

Trace links:

```plaintext
TDD-§6      -> RM-1.1.1 -> EP-M4 -> tests/test_public_api_contract.py::test_public_surface_matches_design_section_six
TDD-§5      -> RM-1.1.1 -> EP-M3 -> tests/test_core_import_boundary.py::test_core_imports_only_allowlisted_modules
TDD-§9      -> RM-1.1.1 -> EP-M3 -> tests/test_public_api_contract.py::test_category_set_matches_design_table_two
TDD-§2.3    -> RM-1.1.1 -> EP-M2 -> tests/test_package_manifest_contract.py::test_declared_ranges_match_installed_metadata
TDD-§13     -> RM-1.1.1 -> EP-M6 -> docs/syrupy-mdast-design.md §13 compatibility paragraph
DEC-14      -> RM-1.1.1 -> EP-M5 -> tests/test_compatibility_matrix_contract.py::test_matrix_floor_matches_declared_specifier
TDD-§2.1    -> RM-1.1.1 -> EP-M2 -> tests/test_package_manifest_contract.py::test_package_ships_py_typed_marker
DEC-3       -> RM-2.3.1 -> EP-M4 -> tests/test_public_api_contract.py::test_serialize_rejects_unsupported_inputs
```

## Verification plan

### Axioms

These are assumed, not verified. Do not attempt to verify third-party
internals.

1. Syrupy's `syrupy.extensions.single_file` module exposes
   `SingleFileSnapshotExtension` and `WriteMode`, and the base class reads the
   public `file_extension` class attribute when composing snapshot paths.
   Confirmed present in both 5.0.0 and 6.0.0 during planning. Guarded by
   `INV-4`, because this repository owns the subclass that depends on it.
2. `_write_mode` is a **private** Syrupy attribute carrying no compatibility
   promise. This is a known, accepted exposure; see Risk 4.
3. Hatchling includes non-Python files inside a package directory named in
   `[tool.hatch.build.targets.wheel] packages`. Checked once by manual wheel
   inspection at EP-M7 rather than by a suite test.
4. Skylos 4.33.2 matches whitelist entries on bare symbol names only. This is a
   tool behaviour established empirically during planning (Surprise 3), not an
   assumption; it is recorded here because DEC-7 depends on it.
5. Python's `BaseException.__reduce__` reconstructs an exception by calling
   `type(exc)(*exc.args)`. This is why DEC-6 requires an explicit `__reduce__`.

### Obligations

**INV-1 — Public surface equality.**
Statement: the set of non-underscore attributes reachable from the
`syrupy_mdast` namespace equals exactly `{"MarkdownAstError",
"MarkdownAstSnapshotExtension"}`, and equals `set(syrupy_mdast.__all__)`.
Method: explicit unit assertion. A property test is inappropriate — the domain
is a single fixed set, not a range.
Rationale: this is the roadmap's literal success criterion. Asserting `__all__`
alone would be theatre, because `__all__` governs `import *` and nothing else;
the namespace check is what catches a leaked public submodule.
Domain: the imported module namespace.
Artefact: `tests/test_public_api_contract.py`.
Evidence: fails before EP-M4 because `MarkdownAstSnapshotExtension` does not
exist; passes after.
Non-vacuity: the test must also assert the set is non-empty, so a failed import
cannot pass it silently. Negative control: temporarily rename `_extension.py`
to `extension.py` and confirm the test fails on the leaked `extension`
attribute. Revert immediately.

**INV-2 — Domain core import boundary.**
Statement: every module under `syrupy_mdast/_core/` imports only `__future__`,
an explicitly allowlisted stdlib set, and `level == 1` relative siblings.
Method: static `ast` scan over the directory.
Rationale: design §5's guard. A static scan is strictly stronger than a runtime
check here, and a runtime check is in fact *unsound*: importing
`syrupy_mdast._core` executes `syrupy_mdast/__init__.py` first, which imports
`_extension`, which imports Syrupy — so `"syrupy" in sys.modules` is
unavoidably true. The static scan also catches `if typ.TYPE_CHECKING:` imports,
which the repository's Ruff `TC` rules actively push code towards and which no
runtime probe can ever observe, plus imports on unexecuted branches.
Domain: all `*.py` files under `syrupy_mdast/_core/`, walked in full via
`ast.walk` so function-local imports are included.
Artefact: `tests/test_core_import_boundary.py`.
Evidence: passes at EP-M3 for the new core.
Non-vacuity: assert the discovered file set is non-empty and include the
discovered paths in the failure message — the commonest failure of an
architecture test is a glob that silently matches nothing after a move and
then passes forever. Negative control: write `import syrupy` into a temporary
copy of a core module in a `tmp_path` fixture and assert the scanner rejects
it, exercising the detector rather than merely the current tree.

The allowlist must be explicit, not `sys.stdlib_module_names`: `json`,
`pathlib`, `io`, and `os` are all stdlib and all violate §5's "performs no
snapshot lifecycle or JSON I/O". Start with `typing`, `collections.abc`,
`dataclasses`, `enum`. Reject `level >= 2` relative imports, every absolute
`syrupy_mdast.*` import, and any reference to `importlib` or `__import__`.

**INV-3 — Error construction and round-trip.**
Statement: for every category `c` in `CATEGORIES` and every message string `m`,
`MarkdownAstError(m, category=c)` has `.category == c`, renders `m` via `str()`,
is catchable as `Exception`, and survives a pickle round-trip preserving both.
A category outside `CATEGORIES` raises `ValueError`.
Method: parameterization over the five categories, plus one Hypothesis property
over `st.text()` for the message.
Rationale: the category set is closed and enumerable, so parameterization gives
exhaustive coverage there and reads better than `st.sampled_from`. Hypothesis
earns its place only on the message, where arbitrary text — newlines,
formatting characters, empty strings — can surprise message composition and
`str()` behaviour. This is the narrow, justified use.
Domain: five categories × generated text; plus a rejection case.
Artefact: `tests/test_error_contract.py`.
Evidence: fails before EP-M3; passes after.
Non-vacuity: each of the five categories must appear as a witness — assert the
parameterized case count is five, pinned against `CATEGORIES`, so a category
silently dropped from the tuple fails the suite. The `ValueError` case is the
negative control. The pickle round-trip is itself a seeded-fault detector for
DEC-6: remove the explicit `__reduce__` and it must fail with `TypeError`.

**INV-4 — Declared range matches reality.**
Statement: the Syrupy specifier in installed package metadata matches the
declared policy; `requires-python` matches design §2.3; and the installed
Syrupy exposes `SingleFileSnapshotExtension`, `WriteMode.TEXT`, and
`SingleFileSnapshotExtension._write_mode`.
Method: contract test reading `importlib.metadata` and importing the real
Syrupy interface.
Rationale: this is the repository-owned configuration logic that sits on an
external interface, so the ExecPlan methodology requires verifying it against
the real interface. It converts a Syrupy upgrade that moves the ground into a
failing test in the pull request that bumps it, rather than a downstream user's
broken suite weeks later.
Domain: installed distribution metadata and the resolved Syrupy release.
Artefact: `tests/test_package_manifest_contract.py`.
Evidence: fails before EP-M2 (no Syrupy dependency); passes after.
Non-vacuity: assert the specifier string is non-empty and equals the literal
declared in the test, so `pyproject.toml` drift fails the gate. Negative
control: temporarily alter the specifier in `pyproject.toml`, re-sync, and
confirm the test fails.

**INV-5 — Extension input contract.**
Statement: `serialize()` raises `TypeError` for any non-`str` `data`, and
`ValueError` when any of `exclude`, `include`, or `matcher` is not `None`,
naming the offending control. With valid input it raises `NotImplementedError`
whose message names roadmap task 2.3.1.
Method: parameterization over input types and over each of the three controls
independently.
Rationale: finite, explicitly enumerable partitions — exactly what
parameterization is for. This is the behaviour DEC-3 pulls forward, and it is
what makes the milestone a plateau rather than a facade.
Domain: `{int, bytes, None, list}` for `data`; each control set independently
and in combination.
Artefact: `tests/test_public_api_contract.py`.
Evidence: fails before EP-M4; passes after.
Non-vacuity: assert on the exception *message content* for the control case, so
a blanket `ValueError` cannot pass a test that claims to identify which control
was supplied. The `NotImplementedError` assertion must match the roadmap
reference in the message — otherwise it is tautological, asserting only that an
unimplemented method is unimplemented.

**INV-6 — Declared range and tested range agree.**
Statement: the Syrupy floor pinned by the `compatibility-matrix` job equals the
lower bound of the Syrupy specifier in `pyproject.toml`, and every Python
version admitted by `requires-python` and available to the runner appears in
the matrix.
Method: contract test parsing `pyproject.toml` and
`.github/workflows/ci.yml`, in the established style of
`tests/test_toolchain_contract.py`.
Rationale: a matrix is only worth having if it cannot silently stop testing
what the package claims. Without this, someone widens the declared range to
`>=4.0.0` and CI keeps testing 5.0.0 while the metadata promises more. This is
the same failure the repository already guards against for the Ruff and `ty`
pins, and it is the mechanism that turns Risk 3 from accepted into defended.
Domain: the declared specifier and the workflow matrix definition.
Artefact: `tests/test_compatibility_matrix_contract.py`.
Evidence: fails before EP-M5 because no matrix job exists; passes after.
Non-vacuity: assert the parsed matrix version list is non-empty and that the
job exists by name, so a renamed or deleted job fails loudly rather than
vacuously passing on an empty scan. Negative control: temporarily change the
`pyproject.toml` floor to `>=5.1.0` and confirm the test fails on the
disagreement.

### Residual gaps, stated explicitly

1. Largely retired by EP-M5. What remains: the matrix covers the Syrupy floor
   and the latest resolvable release, not every release between them, and it
   covers neither Wenmode releases nor pytest-xdist. Those stay with roadmap
   2.4.2, which this reduces rather than replaces.
2. No test proves the wheel's contents. EP-M7 inspects it manually once.
   Owned by roadmap 1.2.1 and 2.4.1.
3. `ambrleaks` will not scan this project's future `.mdast.json` snapshots.
   Recorded, with a roadmap item added at EP-M6; not closed here.

## Plan of work

**Stage A — orientation, no code changes.** Read the signposted material.
Confirm `make all` passes on the untouched tree, capturing the log. If it does
not, stop: you are debugging a pre-existing failure, not this task.

**Stage B — red tests.** For each milestone below, write the failing test
before the production code and observe it fail *for the expected reason*. Where
the failure would otherwise be a collection error rather than an assertion,
note that in the transcript. Do not leave `xfail` markers in the final tree.

**Stage C — implementation.** Smallest change that turns each red test green.

**Stage D — refactor, documentation, and the wider gate sweep.**

Each stage ends with validation. Do not proceed past a failing stage.

## Milestones and plateaus

The ordering below is load-bearing. It exists so that when the Skylos tier goes
red you know exactly which file caused it. Landing these as one commit would
mean facing six findings across two new modules with no way to attribute them.

### EP-M1 — Remove the generated stub

Outcome: the package is empty of generated scaffolding and every gate is green.
This is your known-good baseline and the reference point for every subsequent
failure.

Order within the milestone is mandatory: delete `tests/test_stub.py` **first**,
then `syrupy_mdast/pure.py` and the `hello`/`importlib` machinery in
`syrupy_mdast/__init__.py`. Reversing this breaks pytest at collection time,
which under `-n auto` surfaces as worker-crash output rather than a clean
failure.

Requirements: RM-1.1.1 bullet 3 (partial).
Acceptance evidence: `make all` green; `uv run python -c "import syrupy_mdast;
syrupy_mdast.hello()"` raises `AttributeError`.
Conformance check: no public interface added; no dependency change; design §5
not yet engaged.
Recovery: `git revert` the single commit.
Remaining gaps: the package now exports nothing. That is intentional and
transient within this plan.
Compatibility decision: none required. `hello()` is generated scaffolding,
pre-1.0, with no external consumer and no release tag exposing it.

### EP-M2 — Declare metadata and the Syrupy runtime dependency

Outcome: `pyproject.toml` describes the real product, declares
`syrupy>=5.0.0,<7.0.0`, and ships a `py.typed` marker; `uv.lock` is regenerated
and committed.

Run `make build` and then `make audit` **before writing any code against
Syrupy**. This isolates dependency-resolution and `pip-audit` surface failures
from code failures — this is the project's first ever runtime dependency, so
the `pip-audit` surface changes here for the first time.

Requirements: RM-1.1.1 bullet 1; TDD-§2.1; TDD-§2.3.
Acceptance evidence: `tests/test_package_manifest_contract.py` passes; `uv.lock`
contains a `syrupy` entry; `make audit` green.
Conformance check: exactly one runtime dependency; `requires-python` unchanged
at `>=3.12`; no public interface yet.
Recovery: revert `pyproject.toml` and `uv.lock` together; they must never
diverge.
Remaining gaps: the floor is not resolution-tested (Risk 3).
Compatibility decision: none.

### EP-M3 — Domain core and import guard

Outcome: `syrupy_mdast/_core/` exists with `MarkdownAstError` and the five
ratified category constants, and the architecture test guards it from the
moment it is created.

Land the guard with the boundary it guards. Design §5's architecture test is
nominally roadmap 2.1.2's, but this is the task that *creates* the core, and a
boundary is cheapest to defend before anyone has had the chance to violate it.

Requirements: TDD-§5; TDD-§9; RM-1.1.1 bullet 2 (partial).
Acceptance evidence: `tests/test_error_contract.py` and
`tests/test_core_import_boundary.py` pass; `make lint` green — Skylos was
confirmed during planning not to flag the error class or its constants.
Conformance check: `_core` imports nothing outside the allowlist; category set
matches §9 Table 2 exactly; no public surface change yet.
Recovery: the core is additive and self-contained; revert the commit.
Remaining gaps: nothing raises `MarkdownAstError` yet. Correct — raisers land
at roadmap 2.2.2.
Compatibility decision: none.

### EP-M4 — Syrupy adapter and public API contract

Outcome: the design §6 public surface exists, its input contract is enforced
and tested, and the Skylos findings are resolved.

This is the milestone that will fight you. Expect `SKY-U003` on
`file_extension` and `_write_mode`. Expect **no** `SKY-U006`, because DEC-3's
input validation reads all four `serialize` parameters — if you see `SKY-U006`,
your validation is incomplete. Follow this order:

1. Write `_extension.py` with the full §6 input contract.
2. Write the public API contract test.
3. Run `make lint` and read what actually fires. Do not pre-suppress.
4. For `PLR6301`, prefer naming the instance in a diagnostic message.
5. For the remaining `SKY-U003` findings, add **bare-name** entries to
   `[tool.skylos.whitelist.documented]` with evidence-bearing reasons, and
   update `_DOCUMENTED_WHITELIST_NAMES` in `tests/test_skylos_lint_contract.py`
   **in the same commit** — that frozenset is currently empty and a contract
   test enforces it, so it will otherwise fail in a file you never opened.

Requirements: TDD-§6; DEC-3; RM-1.1.1 bullets 2 and 4.
Acceptance evidence: `make all` green; the `Purpose` section's two-command
transcript reproduces exactly.
Conformance check: public surface is exactly two names; no unapproved
interface; `_write_mode` exposure recorded in Risks; trace links current.
Recovery: revert; EP-M3 remains a valid plateau.
Remaining gaps: serialization itself. This is the plateau boundary — one
`raise` becomes one pipeline call at roadmap 2.3.1, and nothing written here is
deleted then.
Compatibility decision: none. Pre-1.0, unreleased, no external consumer.
Constraint 5 forbids cutting a release before 2.3.1.

### EP-M5 — Python and Syrupy compatibility matrix

Outcome: `.github/workflows/ci.yml` gains a `compatibility-matrix` job that
exercises the package's public contract across the declared Python range and at
both ends of the declared Syrupy range, and a contract test binds that matrix
to the declarations in `pyproject.toml`.

This milestone must follow EP-M4, because the matrix runs the package contract
tests that EP-M4 creates.

Add a **new job**. Do not modify the existing `lint-test` job. Every existing
workflow contract test resolves its target job by name via
`tests/support/make_contract.py::workflow_job`, so an additional job is
invisible to them; editing `lint-test` risks breaking `sole_workflow_step`
assertions in `tests/test_skylos_lint_contract.py`.

The matrix runs **only** the package contract tests
(`tests/test_public_api_contract.py`, `tests/test_error_contract.py`,
`tests/test_package_manifest_contract.py`, `tests/test_core_import_boundary.py`).
It must not run the full suite: the infrastructure contract tests require the
Rust-built `makeutil` binary, which would add a nightly toolchain build to every
leg, and they assert Makefile and workflow structure that is invariant across
interpreter and Syrupy version. Keeping the matrix cheap is what makes it worth
having.

Pin the Syrupy floor by installing it explicitly after the sync, then run pytest
with `--no-sync` so `uv` does not silently restore the resolved version. Do not
use `uv sync --resolution lowest-direct`: it would also floor the dev group,
where `pytest` is declared without a lower bound, and resolve absurd tooling
versions.

Requirements: TDD-§2.3; DEC-8; DEC-14; retires most of residual gap 1.
Acceptance evidence: all matrix legs green on the pull request;
`tests/test_compatibility_matrix_contract.py` passes.
Conformance check: no change to the declared ranges, only to the evidence for
them; no public interface change; `lint-test` untouched.
Recovery: the job is additive and independent; revert the workflow hunk and the
contract test together.
Remaining gaps: Wenmode releases, pytest-xdist, and the wider combinatorial
coverage of design §11 remain roadmap 2.4.2's, which this milestone reduces
rather than replaces.
Compatibility decision: none.

### EP-M6 — Documentation and Skylos guidance correction

Outcome: `README.md` describes the real package and its compatibility policy;
design §13 carries the concrete Syrupy range and its rationale; `AGENTS.md` and
`docs/developers-guide.md` no longer point contributors at remedies that
silently fail; the `ambrleaks` blind spot is recorded with a roadmap item.

`docs/users-guide.md` is deliberately untouched (DEC-12).

Requirements: RM-1.1.1 bullet 3; TDD-§13.
Acceptance evidence: `make markdownlint` and `make fmt` green; the corrected
Skylos guidance states the bare-name matching rule and its repository-global
blast radius.
Conformance check: design §13 updated because this task *makes* the range
decision, per `AGENTS.md`'s rule that new decisions update the relevant
document.
Recovery: documentation-only; revert freely.
Remaining gaps: full user-guide replacement (roadmap 3.1.1); ADR-001 template
conformance (roadmap 3.1.2).

### EP-M7 — Full sweep and roadmap tick

Outcome: every gate green from a clean tree, all `compatibility-matrix` legs
green, the wheel inspected once by hand, `docs/roadmap.md` task 1.1.1 marked
`[x]`, and this plan set to `COMPLETE` after reconciling discoveries against
`Conformance basis`.

Acceptance evidence: `make clean && make all` green; `uv build --wheel` produces
a wheel containing `syrupy_mdast/_core/` and `syrupy_mdast/py.typed` and no
JavaScript asset.
Recovery: not applicable; this milestone only verifies.

## Concrete steps

Run everything from the repository root. Capture every gate run to a log, per
`AGENTS.md`, because long output is truncated in-terminal:

```bash
make lint 2>&1 | tee "/tmp/lint-syrupy-mdast-$(git branch --show-current).out"
```

Stage A baseline:

```bash
make all 2>&1 | tee "/tmp/baseline-syrupy-mdast-$(git branch --show-current).out"
```

Expect a green run. If `make test` fails immediately with a `makeutil` error,
bootstrap it using the command in `docs/developers-guide.md` — that is a first
run environment issue, not a code failure.

EP-M1:

```bash
git rm tests/test_stub.py
git rm syrupy_mdast/pure.py
# then edit syrupy_mdast/__init__.py to remove hello and the importlib fallback
make all 2>&1 | tee /tmp/m1-lint.out
```

EP-M2, after editing `[project]` in `pyproject.toml` and adding
`syrupy_mdast/py.typed` (an empty file):

```bash
make build
make audit
git add pyproject.toml uv.lock syrupy_mdast/py.typed
```

Confirm the lockfile actually moved:

```bash
grep -n 'name = "syrupy"' uv.lock
```

Expected: a match. Before this step there is none.

EP-M3 and EP-M4 follow the red-green-refactor loop per module. Run the focused
test first:

```bash
uv run pytest tests/test_error_contract.py -v
```

EP-M5 adds this job to `.github/workflows/ci.yml`. Reuse the action SHA pins
already used by `lint-test` rather than introducing new ones:

```yaml
  compatibility-matrix:
    name: py${{ matrix.python-version }} / syrupy ${{ matrix.syrupy-version }}
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.12', '3.13', '3.14']
        syrupy-version: ['5.0.0', 'latest']
    steps:
      - name: Check out repository
        uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v4
        with:
          persist-credentials: false

      - name: Set up Python
        uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install uv
        uses: astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990 # v8.3.2

      - name: Sync dependencies
        run: uv sync --group dev

      - name: Pin the declared Syrupy floor
        if: matrix.syrupy-version != 'latest'
        run: uv pip install "syrupy==${{ matrix.syrupy-version }}"

      - name: Run package contract tests
        run: |
          uv run --no-sync pytest -v \
            tests/test_public_api_contract.py \
            tests/test_error_contract.py \
            tests/test_package_manifest_contract.py \
            tests/test_core_import_boundary.py
```

Verify locally before pushing, in a throwaway environment so the working
`.venv` is not left holding a downgraded Syrupy:

```bash
uv run --isolated --with 'syrupy==5.0.0' --python 3.12 \
  pytest tests/test_public_api_contract.py -v
```

If that leaves `.venv` in an odd state, `make build` restores it.

EP-M7:

```bash
make clean && make all 2>&1 | tee /tmp/m6-all.out
uv build --wheel --out-dir /tmp/mdast-wheel
python -m zipfile -l /tmp/mdast-wheel/*.whl
```

Expect `syrupy_mdast/py.typed`, `syrupy_mdast/_core/__init__.py`, and
`syrupy_mdast/_core/errors.py` in the listing, and no `.js`, `.ts`,
`package.json`, or lockfile entry.

## Validation and acceptance

Acceptance is behavioural. After EP-M4:

1. `uv run python -c "import syrupy_mdast; print(sorted(syrupy_mdast.__all__))"`
   prints `['MarkdownAstError', 'MarkdownAstSnapshotExtension']`.
2. `syrupy_mdast.MarkdownAstSnapshotExtension.file_extension` is `"mdast.json"`.
3. Calling `serialize(123)` raises `TypeError` naming the received type.
4. Calling `serialize("# Title", exclude=object())` raises `ValueError` naming
   `exclude`.
5. Calling `serialize("# Title")` raises `NotImplementedError` whose message
   names roadmap task 2.3.1.
6. `syrupy_mdast.hello` does not exist.

Red-green-refactor evidence must be recorded for each milestone: the red
command and its failure reason, the green command and its pass, and the
post-refactor rerun.

Quality criteria:

1. Tests: `make test` passes. The new tests fail before their production code
   and pass after.
2. Verification: INV-1 through INV-5 discharged, each with its non-vacuity
   check performed and recorded. Residual gaps 1-3 remain open by design and
   are traced to their owning roadmap tasks.
3. Lint and typecheck: `make check-fmt`, `make lint`, `make typecheck` all
   green. At most two documented Skylos whitelist entries, both bare names,
   both with evidence-bearing reasons.
4. Documentation: `make markdownlint` and `make nixie` green.
5. Performance: not applicable.
6. Security: `make audit` green with the new runtime dependency.

Delegate full gate runs to the `scrutineer` subagent, which runs them
sequentially, captures each to a log, and returns a bounded report. When it
reports a failure, read the cited log rather than re-running the gate.

## Idempotence and recovery

Every step is re-runnable. `make build` is idempotent. `make clean` removes all
local build state and is safe at any point.

The one ordering hazard is EP-M1: deleting `hello()` before
`tests/test_stub.py` produces a confusing xdist collection failure. If you hit
it, delete the test and re-run; nothing is corrupted.

`pyproject.toml` and `uv.lock` must be committed together and reverted
together. A tree where they disagree will pass locally and fail in CI.

If a Skylos whitelist entry is added without the matching
`_DOCUMENTED_WHITELIST_NAMES` update, `make lint` passes and `make test` fails
in an apparently unrelated file. Change both together.

## Artefacts and notes

The Skylos probe output that drove DEC-3, captured during planning against a
package mirroring design §6 with a *stubbed* `serialize()`:

```plaintext
pkg/extension.py:21  SKY-U003  unused variable: file_extension
pkg/extension.py:22  SKY-U003  unused variable: _write_mode
pkg/extension.py:26  SKY-U006  unused parameter: data
pkg/extension.py:28  SKY-U006  unused parameter: exclude
pkg/extension.py:29  SKY-U006  unused parameter: include
pkg/extension.py:30  SKY-U006  unused parameter: matcher
EXIT 1
```

The four `SKY-U006` findings are what DEC-3 eliminates by implementing the
input contract. If they reappear, the validation is incomplete.

Whitelist matching behaviour, five spellings against one finding:

```plaintext
file_extension                                        -> suppressed
*file_extension                                       -> suppressed
MarkdownAstSnapshotExtension.file_extension           -> still flagged
extension.MarkdownAstSnapshotExtension.file_extension -> still flagged
pkg.extension.MarkdownAstSnapshotExtension.file_extension -> still flagged
```

## Interfaces and dependencies

At the end of EP-M4 these must exist exactly as written.

In `syrupy_mdast/_core/errors.py`:

```python
CATEGORY_SOURCE_ENCODING: typ.Final = "source-encoding"
CATEGORY_INPUT_TOO_LARGE: typ.Final = "input-too-large"
CATEGORY_PARSE: typ.Final = "parse"
CATEGORY_AST_SHAPE: typ.Final = "ast-shape"
CATEGORY_SERIALIZATION: typ.Final = "serialization"

CATEGORIES: typ.Final[tuple[str, ...]] = (
    CATEGORY_SOURCE_ENCODING,
    CATEGORY_INPUT_TOO_LARGE,
    CATEGORY_PARSE,
    CATEGORY_AST_SHAPE,
    CATEGORY_SERIALIZATION,
)


class MarkdownAstError(Exception):
    """Raised when Markdown cannot be compared as a canonical AST."""

    def __init__(self, message: str, *, category: str) -> None: ...

    def __reduce__(self) -> tuple[object, ...]: ...
```

`category` is validated against `CATEGORIES` in the constructor and a bad value
raises `ValueError`. That validation is genuine contract enforcement — the
category set is normative per §9 Table 2 — and it has the incidental benefit of
making all five constants live in-package.

In `syrupy_mdast/_extension.py`:

```python
class MarkdownAstSnapshotExtension(SingleFileSnapshotExtension):
    """Compare Markdown sources as canonical mdast-compatible JSON."""

    file_extension = "mdast.json"
    _write_mode = WriteMode.TEXT

    @typ.override
    def serialize(
        self,
        data: SerializableData,
        *,
        exclude: PropertyFilter | None = None,
        include: PropertyFilter | None = None,
        matcher: PropertyMatcher | None = None,
    ) -> SerializedData: ...
```

The `serialize` signature must match Syrupy's base class exactly — parameter
names, kinds, and defaults. The signature *is* the surface being ratified; a
stub with a divergent signature ratifies nothing.

In `syrupy_mdast/__init__.py`:

```python
from ._core import MarkdownAstError
from ._extension import MarkdownAstSnapshotExtension

__all__ = ["MarkdownAstError", "MarkdownAstSnapshotExtension"]
```

Dependencies. Runtime: `syrupy>=5.0.0,<7.0.0`, and nothing else. Development:
no additions — `pytest` and `hypothesis` are already in the `dev` group, and
`pytest-bdd` is deferred to roadmap 2.3.1 per DEC-9.

In `.github/workflows/ci.yml`, a new job `compatibility-matrix`, additive and
independent of `lint-test`. In
`tests/test_compatibility_matrix_contract.py`, a test binding the matrix's
pinned Syrupy floor to the lower bound of the `pyproject.toml` specifier, and
the matrix's Python versions to `requires-python`.

## Revision notes

### 2026-08-29 — correct a misread source reference

What changed: removed the eighth entry from `Surprises & discoveries`, which
recorded `docs/python-native-command-mocking-design.md` as a missing document
cited by the task brief.

Why: that citation was a slip for `docs/syrupy-mdast-design.md`, which does
exist and is this plan's primary upstream source. There is no missing document
and therefore no discovery to record.

Effect on remaining work: none. The technical design was already the plan's
governing artefact throughout — it heads the signposted reading, anchors the
`Conformance basis`, and supplies every `TDD-§` trace link. No milestone,
obligation, decision, or acceptance criterion changes. `Surprises &
discoveries` now holds seven entries.

### 2026-08-29 — add the compatibility matrix instead of deferring it

What changed: the untested-bound risk is no longer an accepted residual gap.
A new milestone `EP-M5` adds a `compatibility-matrix` job to
`.github/workflows/ci.yml` covering Python 3.12, 3.13, and 3.14 against the
declared Syrupy floor and the latest resolvable release, plus a new obligation
`INV-6` and a contract test binding the matrix to the declarations in
`pyproject.toml`. The documentation milestone became `EP-M6` and the final
sweep `EP-M7`; every cross-reference, trace link, and residual-gap entry was
updated. `Tolerances` scope rose from 16 to 20 files. Two decisions were added
(DEC-14, DEC-15) and one risk (Risk 8, unrelated matrix-leg failures).

Why: the plan had recorded the untested `>=5.0.0` floor as accepted debt owed
to roadmap 2.4.2. That was the wrong call — this is the task that ratifies the
bounds, and a bound nobody resolves against is a claim rather than a contract.
The user directed that the matrix be added now.

Effect on remaining work: one additional milestone between the adapter and the
documentation work, and one additional contract test. No change to the public
surface, the declared ranges, or any acceptance criterion for EP-M1 to EP-M4.
Residual gap 1 narrows from "the floor is never tested" to "releases between
the floor and latest, Wenmode, and pytest-xdist are not covered", which remains
roadmap 2.4.2's.
