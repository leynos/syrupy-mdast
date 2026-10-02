# Developer guide

This guide explains the contributor workflow for this repository.

## Local workflow

The public entrypoint for formatting, linting, typechecking, and tests is
`make all`. Narrower Make targets may be invoked when investigating a specific
failure, and changes should be reconciled with the aggregate gate before being
considered complete.

`make lint` runs Ruff (pinned to `$(RUFF_VERSION)`),
`interrogate --fail-under 100 $(PYTHON_TARGETS)` for 100% docstring coverage
across `$(PYTHON_TARGETS)`, the PyPy-backed Pylint runner, the
`df12-python-lints` Pylint pass under CPython `$(DF12_PYTHON)`, `ambrleaks` over
`tests/`, and the strict Skylos dead-code gate. See
[ADR-001](adr-001-python-lint-architecture.md) for the four-tier lint
architecture.

Ruff and ty versions are pinned in three places: `RUFF_VERSION` and
`TY_VERSION` in the `Makefile`, the matching environment variables in
`.github/workflows/ci.yml`, and the `==`-pinned entries in the `dev` dependency
group of `pyproject.toml`. `tests/test_toolchain_contract.py` asserts the three
sites agree; bump them together.

### Skylos dead-code gate

Skylos (pinned to `$(SKYLOS_VERSION)`) scans production modules only —
`$(SKYLOS_PRODUCTION_TARGETS)`, excluding `$(SKYLOS_EXCLUDE_FOLDERS)` — with
the strict gate configuration in `pyproject.toml`, so any unreviewed production
dead-code finding fails `make lint`. The tool runs under Python 3.14 because
Skylos parses source with its own runtime AST; pinning the interpreter prevents
phantom findings on newer syntax.

Investigate every finding before responding to it. Remove genuine dead code.
For verified false positives, prefer a typed
`[[tool.skylos.dead_code.entrypoints]]` rule in `pyproject.toml` when an
implicit runtime caller can be modelled. Class attributes are not modelled by
entry-point rules: record those as documented allow-list entries using the bare
symbol name, because qualified names silently do not suppress the finding:

```bash
make skylos-allow SYMBOL=<symbol> REASON="<evidence for the runtime caller>"
```

`SYMBOL` and `REASON` are both required and must contain non-whitespace text;
the target exits with status 2 otherwise. The variable is named `SYMBOL` (not
`NAME`) because WSL injects `NAME` with the hostname. The write is serialized
with `flock` on the ignored `.skylos-whitelist.lock` file, so concurrent
recordings cannot lose entries.

Bare-name allow-list entries apply repository-wide. Record a concrete runtime
reader in the reason and update `tests/test_skylos_lint_contract.py` in the
same change, so a later symbol with the same name cannot inherit an exception
silently.

### How the Makefile workflows are covered

Two complementary layers protect the `lint` and `typecheck` workflows:

- **Structural contracts** (`tests/test_lint_pipeline_contract.py`,
  `tests/test_skylos_lint_contract.py`) parse the Makefile with `makeutil` and
  assert what it *declares*: the tier order, each invocation's shape, and
  agreement between the sites that pin a tool.
- **Execution-boundary tests** (`tests/test_make_execution_boundary.py`)
  assert what Make actually *does*. They run `make -f <repository Makefile>`
  from a temporary directory with `UV` overridden to a recorder script, so
  every tier is dispatched and its expanded arguments captured without any real
  linter, type checker, or `uv` download running. They cover the dispatch
  order, the arguments each tier receives, and failure propagation — that a
  failing tier fails the target and that no later tier runs.

Add to both layers when changing a workflow: the structural contract guards the
recipe, and the execution test guards the behaviour.

### Makefile parser for contract tests

`make test` requires the `makeutil` Makefile parser on `PATH`; the contract
tests use it to assert Make interfaces structurally instead of matching source
text. CI installs it with the shared `install-makeutil` action, which downloads
a prebuilt release and checks it against a pinned digest and the release's own
`.sha256` file. Locally, download `makeutil-x86_64-unknown-linux-musl` (or the
`aarch64` build) from the release the `install-makeutil` action defaults to,
listed at <https://github.com/leynos/makeutil/releases>, verify it against the
matching `.sha256` file, and put it on `PATH` as `makeutil`.

Every CI job that runs the full pytest suite installs Makeutil independently
through that action and smoke-tests the binary in a `Verify makeutil` step;
`tests/test_skylos_lint_contract.py` asserts the pinned action reference, the
absence of a from-source pin, and the smoke step in each applicable workflow.
The assertions themselves live in `tests/support/makeutil_contract.py`; bump
the pinned action reference there and in the workflows together.

Run `make audit` as the dependency vulnerability gate. It runs `pip-audit` for
Python dependencies, and Rust-enabled projects also run `cargo audit` from the
`rust_extension` crate directory.

## Maintain syrupy-mdast

Treat the [technical design](syrupy-mdast-design.md) as the normative v1
architecture and follow the [roadmap](roadmap.md) for its implementation
sequence.

V1 uses Python dependencies only. Bun, Node.js, TypeScript, JavaScript
manifests, lockfiles, and installed JavaScript package assets are not runtime,
build, test, or wheel dependencies.

### V1 public contract

The package-level public surface is deliberately limited to `MarkdownAstError`
and `MarkdownAstSnapshotExtension`. The dependency-free `syrupy_mdast._core`
package owns the error taxonomy and must not import Syrupy or Wenmode.
`_extension.py` is the thin Syrupy adapter: it uses the `mdast.json` filename
suffix and text write mode, accepts only `str` input, and rejects unsupported
Syrupy property controls before the unimplemented serialization seam.

The package targets Python 3.12 or later and declares Syrupy `>=5.0.0,<7.0.0`.
`syrupy_mdast/py.typed` is part of the wheel so type checkers can use the
package's annotations from installed distributions.

### Upgrade Wenmode

1. Keep Wenmode exactly pinned.
2. Run the canonical corpus against the pinned and candidate versions.
3. Classify every snapshot payload difference before merge.
4. Record any required snapshot migration and release-note work.

### Verify a wheel

1. Build and install the wheel in an isolated Python environment.
2. Run CommonMark and GitHub Flavoured Markdown (GFM) assertions.
3. Inspect the wheel and reject JavaScript source, JavaScript manifests,
   JavaScript lockfiles, and installed JavaScript package directories.

### Run the verification layers

- Run dependency-free domain tests directly.
- Test the Wenmode, canonical JSON, and Syrupy adapters independently.
- Run end-to-end tests from the source tree and an installed wheel.
- Reject Wenmode and Syrupy imports from the domain core with architecture
  tests.
- Run same-process contention, interleaving, and re-entrant parser-isolation
  tests.
- Cover both serial pytest and pytest-xdist execution.

## Automation scripts

The [Scripting standards](scripting-standards.md) document provides guidance
for adding or updating helper scripts. New and updated scripts are expected to
use `Cyclopts` for command-line interfaces, `cuprum` for typed and
catalogue-bound external command execution, `pathlib` for filesystem paths, and
`cmd-mox` for tests that mock external executables.

Script changes should update the scripting guide when they introduce a new
convention, command catalogue, testing pattern, or operational expectation that
future contributors need to follow.

## GitHub Actions

This repository includes GitHub Actions workflows and local composite actions
under `.github/`.

- `.github/workflows/ci.yml` runs on pushes to `main` and on pull requests. It
  sets up Python 3.13, installs `uv`, validates the `Makefile` with `mbake`,
  installs the pinned Makeutil parser, runs `make build`, `make check-fmt`,
  `make lint` (Ruff + `interrogate --fail-under 100 $(PYTHON_TARGETS)` + the
  PyPy-backed Pylint runner + the `df12-python-lints` pass + `ambrleaks` + the
  strict Skylos dead-code gate), `make typecheck`, and `make audit`. On a pull
  request it then delegates test execution and coverage generation to the
  shared coverage action, which ratchets coverage against the baseline `main`
  last saved. When the Rust extension is enabled, it also sets up Rust,
  installs Rust lint and test tools, and passes `rust_extension/Cargo.toml` to
  coverage.
- The same workflow's additive `compatibility-matrix` job uses
  `fail-fast: false` and tests Python 3.12, 3.13, and 3.14 against the Syrupy
  floor (`5.0.0`) and the newest release below 7.0.0. The floor lane explicitly
  installs `syrupy==5.0.0` after dependency synchronization; the latest lane
  runs `uv pip install --upgrade "syrupy<7.0.0"` so it explicitly upgrades
  within the declared upper bound. Each lane runs the package contract tests.
  The `tests/test_compatibility_matrix_contract.py` test checks the matrix
  dimensions, their relationship to the package dependency range, and the
  explicit latest-lane installation command.
- `.github/workflows/coverage-main.yml` runs on pushes to `main` and on manual
  dispatch. It runs the test suite through the shared coverage action, which
  writes the ratchet baseline, and uploads the report to CodeScene. It is the
  only workflow that contacts CodeScene; see
  [CodeScene coverage publication](#codescene-coverage-publication).
- `.github/workflows/act-validation.yml` runs rendered workflow validation in a
  separate workflow. It installs `act`, checks Docker availability, installs
  the pinned Makeutil parser, and runs `make test WITH_ACT=1` outside the
  coverage path.
- `.github/workflows/release.yml` publishes wheels when a `v*.*.*` tag is
  pushed. It builds a pure Python wheel, creates a GitHub release with
  generated release notes, downloads wheel artifacts, and uploads them to the
  tag release.
- `.github/workflows/build-wheels.yml` is a reusable workflow for extension
  builds. It accepts a Python version and builds wheels across Linux, Windows,
  and macOS architectures via `.github/actions/build-wheels`.
- `.github/actions/build-wheels` wraps `cibuildwheel` with `uvx` and uploads
  architecture-specific wheel artifacts.
- `.github/actions/pure-python-wheel` builds a pure Python wheel with
  `uv build --wheel` and uploads the resulting artifact.
- `.github/dependabot.yml` enables dependency update pull requests for GitHub
  Actions and Python packages. Rust-enabled projects also receive Cargo updates.

### Dependabot policy

Every ecosystem is checked for updates daily. Each has one wildcard `groups`
rule limited to `minor` and `patch` updates, so routine bumps arrive as a
single pull request per ecosystem. Ungrouped bumps each edit the same files, so
whichever merges first leaves the remaining pull requests out of date, which
disables their auto-merge and strands them until someone rebases them by hand.
One group removes the same-file collision. Major updates stay ungrouped: each
arrives in its own pull request, where it can be reviewed and built on its own.

The `github-actions` entry uses `directories` rather than `directory`, because
`/` covers only `.github/workflows` and the root action manifest. Dependabot
does not descend into `.github/actions`, so each composite action needs its own
glob entry; without one, those action pins silently fall behind the workflows
that call them.

`tests/test_dependabot_config_contract.py` enforces these properties. It
derives the expected action directories from the repository, so adding a
composite action fails the suite until Dependabot is configured to watch it.

### CodeScene coverage publication

[ADR-002](adr-002-main-owns-codescene-coverage-publication.md) records the
decision and the options it rejected.

Main owns CodeScene. `.github/workflows/coverage-main.yml` is the one
publisher: on each push to `main` it measures coverage, writes the ratchet
baseline, and uploads the report. Pull requests measure coverage in `ci.yml`
and ratchet it against that baseline, but never contact CodeScene. A pull
request runs arbitrary head-repository code, so a CodeScene step it could reach
would either hand `CS_ACCESS_TOKEN` to a fork or leave a secret-less fork
waiting on a check that can never be produced.

- The pull-request lane's `Test and Measure Coverage` step runs only on pull
  requests, sets `with-ratchet: 'true'` and `publish-artefact: 'false'`, and
  holds no CodeScene step, client, host, or credential. The rule covers every
  workflow a pull request can start, including local reusable workflows and
  local composite actions those workflows run.
- Both coverage steps set `UV_PYTHON: '3.13'` in their `env`, and the contract
  requires the two `env` mappings to match. `generate-coverage` builds its own
  venv with `uv venv`, which takes the newest Python uv can find. The lint step
  downloads CPython 3.14 for its tools, so an unpinned pull-request lane
  measured under 3.14 while the publisher measured under 3.13. The two count
  lines differently, which put every pull request about three points below the
  baseline with no code change.
- The publisher's check step runs one exact command,
  `echo "available=${{ secrets.CS_ACCESS_TOKEN != '' }}" >> "$GITHUB_OUTPUT"`.
  The upload step runs only when that output is `true` and the ref is
  `refs/heads/main`, and passes the secret straight to the uploader's
  `access-token` input. No `env` block holds the token, because the uploader is
  a composite action that hands its step's `env` to the nested steps it runs.
- No checksum input is passed. The uploader verifies the CLI archive it
  downloads against `archive_sha256` in its own `cli-manifest.json` on every
  run, so the manifest the pinned revision carries is the single source of
  truth for that digest.
- The publisher's concurrency group is `coverage-main-${{ github.ref }}`, never
  cancelled. Runs for `main` never overlap, and a newer trigger replaces an
  older pending run rather than queueing behind it. GitHub does not promise to
  start runs in trigger order, so this does not guarantee commit order. A
  manual re-run of an older run keeps its SHA and its run id: it republishes
  that commit's coverage to CodeScene, but replaces no ratchet baseline unless
  the original run saved none.
- The publisher's job declares `environment: codescene`, whose deployment
  policy admits `main` alone. A `workflow_dispatch` aimed at a branch is
  therefore refused for the whole job rather than running and skipping the
  upload; dispatch the publisher on `main`. The token belongs in that
  environment, but moving it there is a pending owner step. Until it moves,
  `CS_ACCESS_TOKEN` is a repository secret that any workflow could read, and
  the contracts above, not the environment, keep it out of what a pull request
  can start. Once it moves, branch code cannot be given the token whatever a
  workflow says. The shared contract's `environment.placement` clause holds the
  placement: every job invoking the uploader declares the environment, no other
  job does, nothing a pull request can start does, names are compared without
  case, and a name computed by an expression is refused.
- With no `CS_ACCESS_TOKEN` secret, as on a fork or before the owner provisions
  one, the check step answers `false` and the upload is skipped; the run shows
  the upload step as skipped rather than failing `main`.
- Merges made by the Dependabot automerge workflow with `GITHUB_TOKEN` fire no
  push, so they reach the publisher only through a later push or a dispatch.
- A dispatch that replaces a pending push uploads the same or a newer commit.
  `generate-coverage` saves the baseline only on a push, so the baseline can
  lag by more than one commit until a later push saves it.

`make test-workflow-contracts` holds this shape by running
`cv005-contracts check`, the shared contract library in `leynos/shared-actions`
(`packages/cv005-contracts`), from a full commit named by `CV005_CONTRACTS_REF`
in the Makefile, and CI runs it as its own step. A fix to the rules is
therefore a pin bump. The target needs `uv`, which fetches the Python 3.13 the
library runs under. The repository's parameters are in `.github/cv005.toml`: its
`repository` name and a `[selection]` table whose
`python-source = "./syrupy_mdast"` is the scope both coverage lanes measure, so
coverage covers the package and not its tests. The publisher's generator must
carry it and every pull-request lane must match it; the ratchet baseline
re-saves at that scope on the next push to `main`. The library reads every
workflow and local action a pull request can reach, and its own suite proves
each rule refuses the shape it exists to refuse, so this repository keeps no
copy of the readers or the refusal cases. Workflows are read strictly: a
duplicate key, or a workflow declaring both a quoted and an unquoted `on` key,
is refused rather than silently resolved.

### Why an immutable pin still needs maintenance

Pinning to a full commit SHA stops a *tag* from moving. It does not freeze the
pins inside the pinned thing. A composite action runs its own `uses:` entries,
so `leynos/shared-actions/…@<sha>` resolves to whatever *that* revision pins,
and a third-party action there can be retired without the composite's own SHA
changing at all.

That is not hypothetical. The `upload-codescene-coverage` revision at
`395f8e86…` nested `actions/cache@6849a648…`, which is v4.1.2. GitHub retired
that release, and any job reaching it fails during **action preparation** —
before the first step runs:

```text
This request has been automatically failed because it uses a deprecated
version of `actions/cache: 6849a648...`.
```

Two properties make this failure mode worth its own maintenance rule. It is
invisible to every local gate, because nothing local resolves a composite's
transitive pins; and it presents as a workflow that passed yesterday and fails
today with no commit in between, which invites the wrong diagnosis (a flaky
runner, or the repository's own change).

So the rule is: a full-SHA pin buys immutability, not staleness immunity. Treat
the transitive dependency set of every pinned composite as scheduled
maintenance. `tests/support/approved_action_revisions.json` records each
approved revision and the dependencies nested inside it, and
`tests/test_action_revision_contract.py` fails when a selected revision is
unrecorded, or when a recorded revision reaches a SHA listed as retired. The
record is checked in rather than fetched, because the contract tests must run
without network access; refresh it when a pin moves, and let the reviewer see
the dependency list change alongside the pin.

Adding a pin therefore takes two edits: the `uses:` line, and the fixture entry
that names what the new revision pulls in. A new dependency the fixture records
as retired is a hard stop, not a warning — it will fail on GitHub regardless of
what the local gates say.
