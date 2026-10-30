# Add the exact Wenmode runtime dependency

Status: COMPLETE — implementation and local acceptance evidence recorded;
hosted review and CI pending.

Roadmap task: **1.2.1**. Baseline: `780a9081eb7f2a810165e1db2b8dc9b187b64972`.
Prepared 2026-10-20. Stack base: PR #76 (`1-2-1-dependency-audit-fix`), which
targets `main`.

This execution plan is a living document. Keep its constraints, tolerances,
risks, progress, discoveries, decisions, conformance basis, verification, and
outcomes current at each milestone. Approval includes the proposed dependency
policy change described below; the user approved implementation on 2026-10-29.

## Purpose and big picture

An editable checkout and an installed wheel must resolve the same reviewed
Wenmode release and parse Markdown using Python alone. Add `wenmode==0.15.2` to
runtime metadata, record its BSD-3-Clause licence, and demonstrate a real parse
in fresh environments without network access or JavaScript execution. The
package's own licence remains ISC.

This slice establishes dependency and distribution contracts. It does not
implement the production parser adapter (1.2.2), normative parser conformance
(1.2.3), canonicalization, or the public snapshot serialization pipeline. A
direct Wenmode call in a test is a dependency smoke test, not that adapter.

## Constraints

Execution approval was supplied with the implementation assignment on
2026-10-30; this revision records the delivered slice and its evidence. Adding
further dependencies, changing accepted policy, or widening the slice still
requires fresh approval.

Retain Python >=3.12, `syrupy>=5.0.0,<7.0.0`, the public exports, and the
Python-only architecture. Do not import Wenmode into `syrupy_mdast/_core/`. Do
not add a runtime version guard, compatibility shim, Rust extension, JavaScript
toolchain, or speculative parser abstraction. No existing snapshot or canonical
corpus payload may change in this slice.

Use the reviewed 0.15.2 release, not the newest available release. Preserve
historical ADR decisions while explicitly superseding their dependency-range
policy after approval. Keep source files below 400 lines. Read `AGENTS.md`
before edits and use sequential Make gates with captured logs before commits.

## Tolerances (exception triggers)

Stop implementation, set Status to BLOCKED, and record options in the decision
log if the approved release cannot be installed on a supported interpreter, its
digest or licence differs, an additional runtime dependency is required, or any
test needs a production parser/canonicalizer change. Escalate changes to public
APIs, snapshot bytes, Python support, or unrelated tool pins.

Approval must explicitly cover replacing the previously accepted bounded
Wenmode requirement. If approval excludes that change, do not choose between
conflicting documents silently. Failure to enforce isolation is a failed
acceptance condition, not grounds for skipping the test. Infrastructure gate
failures must be reported without suppressions or unrelated repairs.

## Risks

ADR-003 and ADR-004 explicitly record a maintainer-selected range, whereas the
roadmap and design require exact pinning. A new, narrow ADR must preserve that
history and state which dependency clauses it supersedes.

An import from the checkout or a warm environment can hide missing metadata.
Use separate fresh virtual environments and run the wheel probe outside the
repository with isolated Python mode. Check module origins and installed
metadata, rather than trusting the installer exit status.

`--offline` and `--no-index` govern installation, not parser network access.
Runtime denial and negative controls are separate evidence. A restricted PATH
alone does not exclude execution through absolute paths.

A wheel tag is not evidence of its contents. Inspect the actual archives and
installed runtime distributions. Network-dependent preparation may fail before
runtime testing; report these phases separately. Avoid repeating expensive
builds per behavioural scenario or Hypothesis example.

## Progress

- [x] 2026-10-20: Rename branch and inspect prerequisite corpus and packaging.
- [x] 2026-10-20: Research reviewed release metadata with Firecrawl.
- [x] 2026-10-20: Draft implementation and verification together.
- [x] 2026-10-20: Six-perspective community review and revisions.
- [x] 2026-10-20: Validate the plan and prepare it for draft publication.
- [x] 2026-10-29: Obtain approval, including the dependency-policy amendment.
- [x] 2026-10-30: Rebase onto the audit-fix bottom layer (PR #76); focused
  EP-M1 suites pass (291 tests).
- [x] EP-M1: Ratify exact pin, add dependency, and prove Python-only installs.
- [x] EP-M2: Complete documentation, gates, and roadmap reconciliation.
- [x] 2026-10-30: Repair the two hosted CodeScene Complex Method findings in
  the test-support harness, then rerun the full gates and republish.
- [x] 2026-10-30: Close the assessment verification gaps: inventory the whole
  installed runtime closure, share the wheelhouse with the manifest contract,
  and generate every forbidden asset family in the property tests.
- [x] 2026-10-30: Repair the follow-up review's public-docstring finding and
  the CodeScene duplication it exposed, then rerun the full gates.

## Surprises & discoveries

2026-10-30: The hosted CodeScene code-health check scans test-support Python,
not only production modules, and failed both new harness files on Complex
Method (9.69 each). Splitting the offline-install attempt and the isolation
negative controls into small helpers raises each file to 10.00 locally
(`cs check`), without weakening any assertion.

2026-10-30: The inherited audit blocker was resolved as a separate bottom
layer. PR #76 (`1-2-1-dependency-audit-fix`) upgrades only development lockfile
entries and targets `main`; this branch was rebased onto it, and the two PRs
form GitHub stack #77. The focused EP-M1 suites passed (291 tests) on the
rebased candidate, including the wheel and editable probes and the archive
classifier property tests. Audit evidence is in
`/tmp/audit-syrupy-mdast-1-2-1-dependency-audit-fix.out`.

2026-10-29: The implementation candidate passed `make fmt`, `make check-fmt`,
`make typecheck`, `make lint`, and `make test` (393 passed at that candidate,
superseded by the 395 below). `make audit` failed on 16 advisories in four
pre-existing development dependencies: `certifi` 2026.7.22, `filelock` 3.32.2,
`msgpack` 1.2.1, and `pylint` 4.0.7. All four versions match the base lockfile.
Audit evidence is in
`/tmp/audit-syrupy-mdast-1-2-1-wenmode-runtime-dependency.out`.

The Python 3.12, 3.13, and 3.14 rootless Podman matrix passed both wheel and
editable modes with networking disabled; logs are in
`/tmp/wenmode-container-acceptance-final.out` and image IDs in
`.wenmode-acceptance.VSaqO0/images.txt`. The executable inventory found no Bun
or Node executables. An isolated mutation removing TypeScript detection caused
three classifier tests to fail (`/tmp/wenmode-mutation-1-2-1.out`).

2026-10-29: The initial manifest assertion failed as expected because Wenmode
was absent (`/tmp/wenmode-red-1-2-1.out`). After adding the pin and locking,
the focused metadata checks passed; Wenmode 0.15.2 reports BSD-3-Clause and no
runtime requirements. Full boundary evidence remains in progress.

Roadmap 1.1.3 is checked complete and the checkout contains its 101-case
canonical corpus. The corpus records `wenmode_evidence_version = "0.15.2"`; it
does not itself execute Wenmode. The earlier plan's review status is
historical, not evidence of current GitHub status.

`tests/test_package_manifest_contract.py` already builds a wheel and imports it
in a fresh virtual environment. Its asset check omits TypeScript and its
installation currently permits network access. Extend this boundary rather than
inventing a second packaging framework.

`docs/repository-layout.md` is referenced by repository instructions but absent
at the baseline. Use `docs/contents.md` and this plan's concrete paths for
orientation; creating a general layout guide is outside this slice.

## Decision log

2026-10-30 — Accepted: the follow-up review asked for structured NumPy-style
docstrings on `require_tool`, `run_command`, and
`run_command_expecting_failure`. Writing them duplicated the two near-identical
success/failure wrappers enough for CodeScene to report Code Duplication (9.38,
twice). The two private status checks are now one `_require_exit_status` helper
taking a keyword-only `expected_failure` flag; call sites read explicitly and
the module scores 10.00.

2026-10-30 — Accepted: the formal CodeRabbit review requested seven trivial
repairs, all valid against `0c87868`. Command execution moved to a new
`tests/support/local_commands.py`, which exposes `run_command`,
`run_command_expecting_failure`, `require_tool`, `environment_python`, and
`clean_dependency_environment` without leading underscores, so cross-module use
no longer relies on private names and the harness module stays under the
400-line limit; the offline installer reuses the shared runner instead of
duplicating `subprocess.run`. `Wheelhouse.project_version` carries the
`Version:` header from the built wheel, so installed metadata is compared with
the artefact instead of a `0.1.0` literal. `clean_dependency_environment` keeps
only credential-routing removals, because a host-specific `PATH` filter and a
forced `GIT_SSH_COMMAND` path are not portable. The manifest contract compares
`SpecifierSet` objects and reports the actual requirements on failure; the
Dependabot contract requires exactly one unconditional `wenmode` ignore; and
the index entry and plan text now describe the completed record with one
consistent 395-test count.

2026-10-30 — Accepted: the ExecPlan assessment found three verification gaps,
and all three were valid against the published head. First, the installed
inventory inspected only `wenmode`, `syrupy-mdast`, and `syrupy`, although the
fresh environment also installs Syrupy's pytest closure (`pytest`, `pluggy`,
`iniconfig`, `packaging`, `pygments`). The child probe now enumerates every
installed distribution with `importlib.metadata.distributions()` and applies
the forbidden-asset classifier to each distribution's file inventory, so a
growing closure cannot fall outside E-ASSETS. Second, the manifest contract
built a second wheel, installed it with network access, and called
`subprocess.run` without bounds. It now consumes the session wheelhouse fixture
moved to `tests/conftest.py`, installs through the shared offline
`install_project` helper, and runs its import probe through the harness's
bounded runner (30 s). Third, the generated archive-path properties sampled
only source suffixes while the outcome claimed every forbidden family.
`_forbidden_member_strategy` now draws source suffixes, named manifests,
lockfiles and runtimes, generated `tsconfig*.json` names, and a `node_modules`
tree, and both position properties use it. The finite matrix gains
`tsconfig.base.json` and `tsconfig.test.json`.

2026-10-30 — Accepted: the same assessment noted that the PR comment claimed
eight hosted matrix jobs and that the container evidence was not inspectable.
The actual hosted matrix is six jobs (Python 3.12/3.13/3.14 x Syrupy
5.0.0/latest); the correction belongs in the assessment follow-up rather than
the plan. The container evidence is now reproducible from recorded image IDs:
`podman run --rm --network=none <image-id> sh -c ...` reports `bun`, `node`, and
`nodejs` absent, and an outbound
`socket.create_connection(("192.0.2.1", 443))` fails with
`OSError: [Errno 101] Network is unreachable` on all three images
(`/tmp/wenmode-container-evidence-20261030.out`). The retained six mode/
interpreter parse passes are in `/tmp/wenmode-container-acceptance-final.out`,
and the TypeScript-detection mutation fails three classifier tests in
`/tmp/wenmode-mutation-1-2-1.out`.

2026-10-30 — Accepted: the milestone CodeRabbit pass found that the installed
runtime inventory omitted Syrupy, even though E-ASSETS requires installed
distribution inventories and Syrupy is a declared runtime dependency. The
inventory probe now includes `syrupy`, so its installed files receive the same
forbidden-asset check. A second suggestion to add the third-party Syrupy wheel
to `_assert_python_only_wheels` is declined: E-ASSETS scopes archive-member
inspection to the built project and selected Wenmode wheels, and the installed
inventory already covers Syrupy.

2026-10-30 — Accepted: the second review pass asked for full parameter
documentation on `install_without_wenmode` and a stronger missing-candidate
assertion. Both are applied; the helper and the behavioural step now require
the resolver's `wenmode==0.15.2` "not found" diagnostic. An unrelated-wheel
negative control is declined because the exact pin, the withheld wheel, and the
empty offline index already isolate the failure cause.

2026-10-30 — Resolved: the user directed the audit findings into a separate
draft PR (#76) targeting `main`, with this branch stacked on it in GitHub stack
number 77. The narrow development-dependency upgrade (`certifi`, `filelock`,
`msgpack`, `pylint`, and `astroid`) was validated by the full gate set and
changes no runtime dependency. The BLOCKED status is cleared without
suppressing findings or expanding 1.2.1's production scope.

2026-10-29 — Blocked: resolving the inherited audit findings requires a scope
decision because this plan escalates unrelated tool changes. A read-only lock
trial would update `certifi` to 2026.10.23, `filelock` to 4.2.4, `msgpack` to
1.2.4, `pylint` to 4.1.3, and its `astroid` dependency to 4.3.4. The options
are to approve and validate that narrow dependency update, or to repair the
base branch separately and rebase. Do not suppress the findings or mark the
roadmap item complete while the audit remains red.

2026-10-29 — Accepted: the user approved the exact-pin amendment and
implementation. The PR target was already the branch base; the rebase was a
no-op and the four requested gates passed on commit `1da75a7`.

2026-10-20 — Proposed: select `wenmode==0.15.2`, matching the reviewed corpus
baseline and the current requested exact-pin requirement. On approval, add
`docs/adr-005-exact-wenmode-runtime-dependency.md` (check numbering first),
superseding only the range and downstream-resolution clauses of ADR-003 and
ADR-004. Link it from both ADRs and the design. Preserve their dated historical
rationale; update active manifest/policy text and affected guide statements. No
normalization or snapshot-version decision changes.

2026-10-20 — Proposed: use one shared test-only packaging harness, extending
existing wheel helpers, for pytest and pytest-bdd. It owns environment setup,
archive inspection, and the child probe; it is not a production port. Before
extracting helpers, search existing `tests/support/` for equivalents. Document
its limited reuse in the developer guide. New scripts must follow
`docs/scripting-standards.md`; do not proliferate subprocess suppressions.

2026-10-20 — Proposed: use real fresh-environment integration tests for the
installation boundary, finite unit cases and Hypothesis for archive-path
classification, and no formal prover. This slice introduces no domain business
logic requiring universal proof. Adding Rust solely to prove test scaffolding
would contradict its Python-only scope. Third-party parser correctness remains
an explicit external assumption.

## Conformance basis

All local references below are at the baseline commit above. No separate Terms
of Reference document exists for this task.

- R-PIN: `docs/roadmap.md`, 1.2.1, and
  `docs/syrupy-mdast-design.md`, sections 2.3 and 13, require an exact release.
  EP-M1 discharges this through E-META and the proposed ADR amendment.
- R-ASSETS: the same roadmap item and design section 13 exclude cross-runtime
  assets. EP-M1 discharges this through E-ASSETS.
- R-OFFLINE: roadmap 1.2.1 and design sections 2.3 and 12 require Python-only,
  local parsing. EP-M1 discharges this through E-RUNTIME.
- R-POLICY: ADR-003's upgrade review/Dependabot policy and ADR-004's parser
  profile remain binding except for the explicitly proposed range amendment.
  EP-M1 updates policy; EP-M2 records E-DOC and E-GATES.
- R-PREREQ: roadmap 1.1.3 and
  `tests/fixtures/markdown_contract/manifest.toml` establish the reviewed
  baseline. Keep their corpus unchanged and re-run its integrity tests.

Read `docs/contents.md`, `docs/users-guide.md`, `docs/developers-guide.md`,
`docs/documentation-style-guide.md`, `docs/syrupy-mdast-design.md`, both ADRs,
and `docs/complexity-antipatterns-and-refactoring-strategies.md` before
editing. Use `.rules/python-00.md`, `.rules/python-pyproject.md`, and
`.rules/python-typing.md`; consult the other `.rules/python-*.md` files for
exceptions, contexts, generators, and return conventions as applicable.

Load `codegraph-mcp` for structural discovery, `python-router` and
`python-testing` for test design, and `hypothesis` for the generated path
invariant. Use `execplans` to maintain this document, `firecrawl-mcp` for
external research, `logisphere-experts` for design review, `commit-message` for
commits, and `pr-creation` for publication. Use a `scrutineer` agent for
sequential gates. Team code excerpts must travel through `context_pack`.

## Verification plan

E-META: the source requirement, built wheel's `Requires-Dist`, editable
metadata, installed wheel metadata, and `metadata.version("wenmode")` agree on
0.15.2. Extend `tests/test_package_manifest_contract.py`. Parse requirements
semantically rather than depending on header order. Reject missing, ranged,
wrong-version, optional-only, and environment-marker-qualified Wenmode
requirements; keep the approved Syrupy requirement. Negative controls mutate
metadata fixtures, not the real environment. The initial exact-pin assertion
must fail because Wenmode is absent. Agreement is a repository configuration
contract, not proof of resolver internals.

E-ASSETS: inspect every member of the built syrupy-mdast wheel and the selected
Wenmode wheel, then the installed runtime distribution file inventories. Reject
`.js`, `.mjs`, `.cjs`, `.jsx`, `.ts`, `.tsx`, `.mts`, `.cts`, package
manifests, JavaScript lockfiles, `tsconfig*.json`, `node_modules` path
components, and Bun/Node executable assets (`bun`, `bun.exe`, `node`,
`node.exe`, `nodejs`). Cover `package.json`, `package-lock.json`,
`npm-shrinkwrap.json`, `bun.lock`, `bun.lockb`, `pnpm-lock.yaml`, and
`yarn.lock`. Ordinary Python metadata, licence files, JSON fixture data, and
Python lockfiles are not JavaScript assets.

Keep a small, pure test-support classifier in
`tests/support/package_boundary.py` if extraction is needed. Parameterized
cases cover every forbidden family plus safe Python and metadata examples.
Hypothesis generates non-empty safe POSIX path prefixes and arbitrary path
positions for forbidden components: nesting or permutation of an archive's
members must not conceal a forbidden member. Generate cases constructively,
record classifications with `event`, and require witnesses for root, nested,
and safe paths. A synthetic wheel containing a nested `.ts` file and one
containing `node_modules` must fail the same inspection used on real wheels. A
mutation dropping TypeScript detection must fail the unit/property suite. This
proves the declared classifier's tested relation; it does not detect malicious
JavaScript disguised as arbitrary data.

E-RUNTIME: run a shared child probe from
`tests/support/wenmode_runtime_probe.py` in fresh wheel and editable virtual
environments. Use `python -I` and an external working directory. Assert
Wenmode's version and origin inside the selected environment; assert the
project origin is inside the environment for a wheel and the expected checkout
for editable installation. Never use `PYTHONPATH` to make imports pass.

Prepare a local wheelhouse before isolation, including the project wheel,
resolved runtime wheels, and the editable build backend and its requirements.
Inspect the downloaded Wenmode wheel's digest, licence, and dependency
metadata. Install with
`uv pip install --offline --no-index --find-links <wheelhouse>
--python <environment-python> <project-wheel>`;
use `--editable <checkout>` for the second environment. Empty shared-cache
assumptions must not be needed: all required distributions must be in the
prepared wheelhouse. Do not disable build isolation merely to make a missing
backend pass. A missing Wenmode wheel must produce a clear installation failure
in an independently empty cache.

Before importing Wenmode, the child installs a Python audit hook that raises on
socket creation/resolution/connect events and subprocess, spawn, fork, and exec
events. Restrict PATH to the fresh environment and verify `bun`, `node`, and
`nodejs` are absent. Exercise deliberate socket and child-process attempts as
negative controls; each must fail with the sentinel denial before its side
effect. Never patch the parser or its return values. Then call
`Parser(github(), positions=False).parse(source).to_ast()` for empty Markdown,
a heading, and a task-list example. Use exact inputs `""`, `"# Hello\n"`, and
`"- [x] done\n- [ ] todo\n"`; require empty root children, a depth-one heading
with text `Hello`, and list items with `checked` values true and false. Run with
`-W error` so parser construction warnings fail. Assert root and child
semantics, absence of positions, and equal results between wheel and editable
installations.

The audit hook is a boundary test for trusted pure-Python code, not a security
sandbox against native code. For acceptance, additionally run the prepared
probe in a pre-provisioned Python-only rootless Podman image with
`--network=none`, no source mount for the wheel case, and no JavaScript
runtime. Installation and execution inside the container use only mounted local
wheels; image acquisition happens beforehand. An outbound TCP connection to a
non-loopback address and an attempted JavaScript launch are negative controls.
Socket creation alone is not a container-network negative control: local
sockets remain available. Missing Podman/image preparation is an explicit
unfulfilled acceptance item, never a silent skip. Record the image digest,
interpreter, commands, and successful parse output. This bounded smoke test
does not claim parser conformance for every Markdown document.

External axioms: Python import metadata and audit events obey their documented
interfaces; uv honours local/offline installation; the OS/container enforces
network isolation; Wenmode's public Parser/GitHub/to_ast interface is stable at
0.15.2. Exercise these interfaces directly; do not prove their internals. There
is no new non-trivial algorithmic lemma or contractual business logic. Do not
snapshot entire metadata/archive listings. Exact semantic assertions suffice
here; multivariant canonical output snapshots remain in later slices.

## Milestones and plateaus

### EP-M1: Exact dependency and executable boundary evidence

After approval, add failing E-META tests and the behavioural specification
below. Capture the missing-dependency failure before changing `pyproject.toml`.
In the same atomic change, add `wenmode==0.15.2` to `project.dependencies`,
refresh `uv.lock` without unrelated upgrades, and add pytest-bdd to the dev
group for these scenarios. Add the policy ADR and cross-links, including the
`wenmode` ignore in the pip ecosystem entry of `.github/dependabot.yml`
required by ADR-003. Cover that ignore in a focused configuration test.
Reconcile all active dependency-policy statements in the design and guides in
this commit so the plateau contains no contradictory requirements. The new ADR
must explicitly permit initial adoption of the already-reviewed 0.15.2 baseline
without the not-yet-implemented 3.2.1 upgrade report; do not weaken the report
requirement for subsequent release moves.

Extend existing wheel tests and factor only shared test support as needed.
Implement E-ASSETS and E-RUNTIME, keeping all assertions independent of the new
production dependency declaration. Put behavioural steps in
`tests/test_wenmode_dependency_bdd.py` and their shared setup in test fixtures.
Existing Make test discovery must execute them. Build one immutable wheelhouse
per worker session; share its evidence between pytest and BDD. Create fresh
mutable environments per mode/case and never reuse a failed environment. Use a
separate empty cache for the missing-wheel case. Bound build/install children
to 300 seconds, probes to 30 seconds, and network controls to one second;
retain stdout/stderr on timeout or failure. Compiler admission waits are
governed separately by AGENTS.md, not these probe limits.

E-META, E-ASSETS, E-RUNTIME, the focused corpus tests, and all major gates must
pass before the milestone commit. Check R-PIN/R-ASSETS/R-OFFLINE/R-POLICY,
verify no production interface or persistent format changed, and update trace
links and evidence. This is a coherent dependency-only plateau; public parser
functionality remains deferred. No compatibility machinery is needed. On
failure, retain logs and fix the candidate; revert the atomic commit if a
completed plateau must be withdrawn.

### EP-M2: Documentation and completion evidence

Update design section 13 with the concrete release/licence and accepted ADR.
Update `docs/users-guide.md` with the dependency and installation guarantee,
without claiming public parsing is implemented. Update
`docs/developers-guide.md` with wheelhouse preparation, isolation commands,
negative controls, the test-support interface, and upgrade policy. Link the new
ADR through `docs/contents.md`. Record internal architecture in the design; no
new component architecture document is necessary for test scaffolding.

Run every gate again after documentation changes. Record E-DOC and E-GATES,
check all trace links and accepted ADR amendments, and mark only roadmap 1.2.1
done after all acceptance evidence exists. Update this plan's progress and
outcomes, then commit. Any missing acceptance evidence leaves the roadmap
unchecked. Recovery is to correct documentation or revert this final commit;
EP-M1 remains a coherent plateau. No implementation gaps remain within 1.2.1;
1.2.2 and 1.2.3 remain separate work.

## Behavioural specification

Create `tests/features/wenmode_dependency.feature` with this specification.
Step definitions must exercise the real shared boundary harness, not canned
results. Run the happy scenarios for both wheel and editable installations.

```gherkin
Feature: Python-only Wenmode dependency
  Scenario Outline: The reviewed parser works in isolation
    Given a fresh <mode> installation from the prepared local wheelhouse
    And JavaScript execution and network access are denied
    When the reviewed GitHub parser parses the smoke documents
    Then Wenmode version 0.15.2 is imported from that environment
    And the expected root and child semantics are returned

    Examples:
      | mode     |
      | wheel    |
      | editable |

  Scenario: A missing offline dependency fails visibly
    Given a local wheelhouse without Wenmode and an empty installer cache
    When a fresh wheel installation is attempted offline
    Then installation fails because Wenmode cannot be resolved

  Scenario: A forbidden wheel asset is rejected
    Given a synthetic wheel containing a nested TypeScript file
    When the Python-only archive contract is checked
    Then the forbidden asset is identified
```

## Concrete steps and validation

Run commands from the repository root. Use the clean environment required by
`AGENTS.md` for dependency fetches and Git-backed tools. After writing tests,
run the focused suite before production metadata edits and record the actual
failure; a strict expected-failure marker may be used temporarily but must be
removed in the green stage. Do not commit an intentionally failing plateau.

```bash
uv run pytest -v tests/test_package_manifest_contract.py
uv run pytest -v tests/test_wenmode_dependency_bdd.py
uv run pytest -v tests/test_markdown_contract.py tests/test_markdown_contract_loading.py
uv lock
uv sync --locked
make build-release
```

After the minimal change, repeat focused tests and expect all assertions and
BDD scenarios to pass. Record actual counts, not predicted counts. Run the
archive classifier's unit/property tests through `make test`; add their exact
file/command here when implemented. Run container acceptance separately and
record the runtime version and AST semantic assertions, with exit status zero.

At each major milestone, the scrutineer runs these gates sequentially with
`set -o pipefail` and one `/tmp/<action>-syrupy-mdast-<branch>.out` log per
gate:

```bash
make fmt
make check-fmt
make typecheck
make lint
make test
make audit
make markdownlint
make nixie
git diff --check
```

Inspect formatter changes before committing; do not sweep unrelated files into
the change. All gates must exit zero. `make test` needs `makeutil` on PATH. If
Makefile recipes change, update both structural and execution-boundary tests as
required by `AGENTS.md`; no recipe change is currently anticipated.

### Reproducible container acceptance recipe

The acceptance matrix is CPython 3.12, 3.13, and 3.14 on Linux, matching the
advertised classifiers. Metadata remains >=3.12; future interpreter versions
require later validation, not an unbounded claim here. Ordinary host tests
retain portable virtual-environment paths. Container setup is one separate
acceptance job, not repeated by every pytest scenario.

Implement `tests/support/wenmode_runtime_probe.py` as a standard-library-only
executable test probe. It reads `WENMODE_INSTALL_MODE` (`wheel` or `editable`)
and `WENMODE_CHECKOUT_PATH` from the environment, performs E-RUNTIME, and prints
`wenmode=0.15.2 mode=<mode> isolation=passed` only after all assertions pass.
The delivered probe remains standard-library-only. Do not require pytest or
Cyclopts inside the consumer environment. If this becomes a maintainer CLI
instead of test support, follow the scripting standards and escalate the added
dependency scope.

The following Bash recipe runs from the repository root after EP-M1's tests and
probe exist. It provisions public official Python images online, records their
immutable IDs, downloads all install/build requirements into a dedicated
ignored output directory, then runs by image ID with networking disabled. Use a
fresh output directory for each execution; do not reuse previous wheels. The
pipeline runs the three interpreter versions sequentially.

```bash
set -euo pipefail
repository=$(pwd)
acceptance_dir=$(mktemp -d "$repository/.wenmode-acceptance.XXXXXX")
uv build --wheel --out-dir "$acceptance_dir/project"
for minor in 3.12 3.13 3.14; do
  image_tag="docker.io/library/python:${minor}-slim"
  podman pull "$image_tag"
  image_id=$(podman image inspect --format '{{.Id}}' "$image_tag")
  printf '%s %s\n' "$minor" "$image_id" >> "$acceptance_dir/images.txt"
  mkdir -p "$acceptance_dir/$minor"
  podman run --rm --userns=keep-id \
    -v "$acceptance_dir:/evidence:Z" "$image_id" \
    sh -ec "python -m pip download --only-binary=:all: \
      --dest /evidence/$minor /evidence/project/*.whl hatchling editables"
  for mode in wheel editable; do
    source_mount=()
    if [ "$mode" = editable ]; then
      source_mount=(-v "$repository:/source:ro,Z")
    fi
    podman run --rm --network=none --userns=keep-id \
      -e WENMODE_INSTALL_MODE="$mode" -e WENMODE_CONTAINER_ACCEPTANCE=1 \
      -v "$acceptance_dir/$minor:/wheels:ro,Z" \
      -v "$repository/tests/support/wenmode_runtime_probe.py:/probe.py:ro,Z" \
      "${source_mount[@]}" "$image_id" sh -ec '
        python -m venv /tmp/consumer
        if [ "$WENMODE_INSTALL_MODE" = editable ]; then
          mkdir /tmp/checkout
          cp -R /source/pyproject.toml /source/README.md /source/LICENSE /tmp/checkout/
          cp -R /source/syrupy_mdast /tmp/checkout/
          export WENMODE_CHECKOUT_PATH=/tmp/checkout
          /tmp/consumer/bin/python -m pip install --no-index --find-links /wheels \
            --editable /tmp/checkout
        else
          /tmp/consumer/bin/python -m pip install --no-index --find-links /wheels syrupy-mdast
        fi
        cd /tmp
        WENMODE_ORIGINAL_PATH="$PATH" PATH=/tmp/consumer/bin \
          /tmp/consumer/bin/python -I -W error /probe.py
      '
  done
done
```

The editable copy includes the baseline Hatch source directory `syrupy_mdast`,
project metadata, README, and licence. The wheel invocation has no checkout
mount. The explicit probe mount is test instrumentation, not an import
fallback. Record `podman image inspect` results and the executed
`--network=none` command as configuration evidence. Containers are removed
after execution, so post-run container inspection is not required. Use the same
image ID throughout preparation and execution. Clean only the recorded
`acceptance_dir` after retaining its evidence and successful results. Ignore
`.wenmode-acceptance.*` in the implementation's `.gitignore` if needed; never
commit these artefacts.

The child probe also verifies
`socket.create_connection(("192.0.2.1", 443), timeout=1)` fails before
installing its audit hook in the container-only mode. Add
`WENMODE_CONTAINER_ACCEPTANCE=1` for that invocation. The test-net address is
an unreachable witness, not independently conclusive evidence; retain the Podman
`--network=none` invocation with it. The audit-hook socket and process denial
controls run afterwards in every mode. Before enabling the hook, check
JavaScript executable absence against the image default PATH and the restricted
PATH, and retain an executable inventory for Bun/Node paths in the image. A
denial caused only by the audit hook does not establish executable absence.
Pass the original image PATH in a dedicated `WENMODE_ORIGINAL_PATH` environment
variable before restricting PATH. Expected evidence comprises six successful
probes and six matching version/origin checks; a missing case fails matrix
acceptance.

## Idempotence and recovery

Each integration run creates fresh disposable environments and a distinct wheel
output directory. Never select an arbitrary stale wheel with an unchecked glob.
Use session fixtures or per-worker directories to avoid xdist collisions.
Temporary wheelhouses and environments must be cleaned by fixtures; record
failure logs before cleanup. Do not use `/tmp` for compiler build targets.
Dependency downloads are preparation; their failure cannot count as a parser
failure or successful isolation proof. Do not change global Git configuration,
kill unrelated jobs, or bypass compiler admission. Commit only gated atomic
milestones and revert through ordinary Git commits when rollback is needed.

## Interfaces and dependencies

The only new production dependency is `wenmode==0.15.2`. The test-only probe
uses `wenmode.Parser`, `wenmode.presets.github`, `Parser.parse`, and
`Document.to_ast`. The production package gains no parser function in this
slice. Test-support routines accept explicit wheel paths, interpreter paths,
and installation modes, and return evidence or raise focused assertions; keep
process execution, metadata comparison, and path classification separate. Use
existing pytest, Hypothesis, and Syrupy dependencies; add pytest-bdd only to
development dependencies. Do not add a runtime packaging/testing library.

## Artefacts and research notes

Firecrawl verified the release-specific [Wenmode 0.15.2 PyPI page][wenmode] on
2026-10-20: BSD-3-Clause, Python >=3.10, and `wenmode-0.15.2-py3-none-any.whl`,
with SHA-256
`a1be9a2d91ef7f5020148daf615edca0c9a4a6d54d074a808e6d5e9de95726f6`. This
matches ADR-004. The implementation must inspect the downloaded archive; this
research is not the future wheel test result.

The [uv package installation guide][uv-packages] documents local/editable
installation. Installer flags alone do not establish runtime isolation. The
concrete preparation recipe above separates online acquisition from offline
execution; record the actual image digests and resolved wheel versions in the
acceptance evidence.

[wenmode]: https://pypi.org/project/wenmode/0.15.2/
[uv-packages]: https://docs.astral.sh/uv/pip/packages/

The
[Python audit-hook documentation](https://docs.python.org/3/library/sys.html#sys.addaudithook)
confirms hooks are not a security sandbox. That limitation is why this plan
keeps interpreter instrumentation and container isolation evidence distinct.

## Outcomes & retrospective

Planning history. The six-perspective review requested concrete container
commands, a bounded interpreter matrix, coherent milestone documentation, and
an outbound rather than local-socket negative control. These revisions are
incorporated. All three Bash examples passed `bash -n`.

Implementation outcome (2026-10-30). Roadmap 1.2.1 now declares
`wenmode==0.15.2` (BSD-3-Clause) in runtime metadata, carries ADR-005 and its
cross-links, and proves the Python-only boundary through the shared
`tests/support/wenmode_installation.py` harness. Focused evidence:

- `tests/test_package_manifest_contract.py` requires the built and installed
  metadata to agree on the exact pin; negative controls reject absent, ranged,
  wrong-version, extra-qualified, and marker-qualified requirements. It now
  reuses the session wheelhouse and offline `install_project` helper instead of
  building and installing a second wheel with network access.
- `tests/test_package_boundary.py` covers 35 classifier cases, including
  Hypothesis-generated archive positions drawn from every forbidden family:
  source suffixes, named manifests, lockfiles and runtimes, `tsconfig*.json`
  settings, and `node_modules` trees. A synthetic nested `node_modules` archive
  is rejected by the same inspector used on release wheels.
- `tests/test_wenmode_dependency_bdd.py` runs four scenarios across wheel and
  editable installs, parses the three smoke documents offline behind audit-hook
  isolation controls, and requires a missing-Wenmode install to fail visibly.
  Its probe inventories and inspects every distribution in the fresh runtime
  closure, including Syrupy's pytest dependencies.
- The Python 3.12, 3.13, and 3.14 rootless Podman matrix passed both modes with
  `--network=none`, six mode/interpreter combinations in total; evidence is in
  `/tmp/wenmode-container-acceptance-final.out` and
  `.wenmode-acceptance.VSaqO0/images.txt`. Re-run read-only controls on the
  recorded image IDs (`ae4e8b7c...`, `bdfc738a...`, `b37832cc...`) show `bun`,
  `node`, and `nodejs` absent and outbound TCP denied with `Errno 101`
  (`/tmp/wenmode-container-evidence-20261030.out`).

Full gates on the rebased candidate passed sequentially: `make check-fmt`,
`make typecheck`, `make lint`, `make test` (395 passed after the assessment
repairs), `make audit`, `make markdownlint`, `make nixie`, and
`git diff --check`. Logs follow the
`/tmp/<action>-syrupy-mdast-1-2-1-wenmode-runtime-dependency.out` pattern.

No production parser adapter, public parsing function, snapshot bytes, or
canonical corpus changed. Hosted CodeRabbit review and CI are not established
by local gates and remain delivery work for `pr-babysitting`. The main lesson
is that an empirical release baseline and an allowed dependency range are
distinct contracts; exact pinning needed an explicit policy amendment. A second
lesson is that an inherited red audit gate must be repaired at its own layer
rather than suppressed or folded into unrelated scope.

## Revision notes

2026-10-20: Created the draft with prerequisite evidence, the proposed
exact-pin ADR amendment, real installation checks, and non-vacuous isolation
tests. Implementation remains subject to explicit approval.

2026-10-20: Expert review bounded the interpreter matrix, made policy
reconciliation part of EP-M1, and specified container preparation and probe
contracts. Approval and all implementation work remain outstanding.

2026-10-20: Recorded passing planning gates and clarified that recorded
container invocations provide network-configuration evidence before automatic
removal. Implementation acceptance remains pending approval and execution.

2026-10-29: User approved the plan and its dependency-policy amendment and
requested implementation after rebasing onto the PR target.

2026-10-30: Cleared the inherited audit blocker through stacked PR #76, rebased
the implementation candidate onto it, and completed EP-M1 and EP-M2. Full local
gates pass (395 tests after the assessment repairs). Hosted review and CI
remain outstanding.
