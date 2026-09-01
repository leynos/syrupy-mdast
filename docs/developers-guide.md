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
`df12-python-lints` Pylint pass under CPython `$(DF12_PYTHON)`, `ambrleaks`
over `tests/`, and the strict Skylos dead-code gate. See
[ADR-001](adr-001-python-lint-architecture.md) for the four-tier lint
architecture.

Ruff and ty versions are pinned in three places: `RUFF_VERSION` and
`TY_VERSION` in the `Makefile`, the matching environment variables in
`.github/workflows/ci.yml`, and the `==`-pinned entries in the `dev`
dependency group of `pyproject.toml`. `tests/test_toolchain_contract.py`
asserts the three sites agree; bump them together.

### Skylos dead-code gate

Skylos (pinned to `$(SKYLOS_VERSION)`) scans production modules only —
`$(SKYLOS_PRODUCTION_TARGETS)`, excluding `$(SKYLOS_EXCLUDE_FOLDERS)` — with
the strict gate configuration in `pyproject.toml`, so any unreviewed
production dead-code finding fails `make lint`. The tool runs under
Python 3.14 because Skylos parses source with its own runtime AST; pinning
the interpreter prevents phantom findings on newer syntax.

Investigate every finding before responding to it. Remove genuine dead code.
For verified false positives, prefer a typed
`[[tool.skylos.dead_code.entrypoints]]` rule in `pyproject.toml` when an
implicit runtime caller can be modelled; otherwise record a documented
allow-list entry with:

```bash
make skylos-allow SYMBOL=<qualified.symbol> REASON="<evidence for the caller>"
```

`SYMBOL` and `REASON` are both required and must contain non-whitespace text;
the target exits with status 2 otherwise. The variable is named `SYMBOL`
(not `NAME`) because WSL injects `NAME` with the hostname. The write is
serialized with `flock` on the ignored `.skylos-whitelist.lock` file, so
concurrent recordings cannot lose entries.

### How the Makefile workflows are covered

Two complementary layers protect the `lint` and `typecheck` workflows:

- **Structural contracts** (`tests/test_lint_pipeline_contract.py`,
  `tests/test_skylos_lint_contract.py`) parse the Makefile with `makeutil`
  and assert what it *declares*: the tier order, each invocation's shape,
  and agreement between the sites that pin a tool.
- **Execution-boundary tests** (`tests/test_make_execution_boundary.py`)
  assert what Make actually *does*. They run `make -f <repository Makefile>`
  from a temporary directory with `UV` overridden to a recorder script, so
  every tier is dispatched and its expanded arguments captured without any
  real linter, type checker, or `uv` download running. They cover the
  dispatch order, the arguments each tier receives, and failure propagation
  — that a failing tier fails the target and that no later tier runs.

Add to both layers when changing a workflow: the structural contract guards
the recipe, and the execution test guards the behaviour.

### Makefile parser for contract tests

`make test` requires the `makeutil` Makefile parser on `PATH`; the contract
tests use it to assert Make interfaces structurally instead of matching
source text. Bootstrap it locally with the same pins CI uses:

```bash
rustup toolchain install nightly-2026-05-28 --profile minimal
RUSTFLAGS="-Zpolonius=next" cargo +nightly-2026-05-28 install \
  --git https://github.com/leynos/makeutil \
  --rev 29fc5a1634ffbaa18a773eed9dff1b2838a45d9c \
  --locked \
  --force \
  makeutil
```

Every CI job that runs the full pytest suite provisions Makeutil
independently with these pins; `tests/test_skylos_lint_contract.py` asserts
the environment pins and installation command in each applicable workflow.

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

Repository-owned Linux CI, release, and maintenance jobs run on
`namespace-profile-default`: the shared Ubuntu 22.04 Linux/amd64 profile with
4 vCPU and 16 GB memory. Its Namespace cache volume is disabled for this
baseline rollout. Existing workflow cache actions remain unchanged; they are
not backed by a Namespace cache volume. `act-validation.yml` remains on
GitHub-hosted Linux because it requires a local Docker daemon; migrate it only
after a Namespace preflight proves that requirement. The reusable
`build-wheels.yml` matrix retains caller-selected GitHub-hosted Linux, Windows,
and macOS runners because the shared estate does not yet provide equivalent
profiles for every target.

This repository includes GitHub Actions workflows and local composite actions
under `.github/`.

- `.github/workflows/ci.yml` runs on pushes to `main` and on pull requests. It
  sets up Python 3.13, installs `uv`, validates the `Makefile` with
  `mbake`, installs the pinned Makeutil parser, runs `make build`,
  `make check-fmt`, `make lint` (Ruff +
  `interrogate --fail-under 100 $(PYTHON_TARGETS)` + the PyPy-backed Pylint
  runner + the `df12-python-lints` pass + `ambrleaks` + the strict Skylos
  dead-code gate), `make typecheck`, and `make audit`, then delegates
  coverage generation to the shared coverage action. When the Rust extension
  is enabled, it also sets up Rust, installs Rust lint and test tools, and
  passes `rust_extension/Cargo.toml` to coverage.
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
- `.github/workflows/get-codescene-sha.yml` is manually dispatched. It fetches
  the CodeScene coverage CLI installer, computes its SHA-256 digest, and writes
  the result to the `CODESCENE_CLI_SHA256` repository variable.
- `.github/actions/build-wheels` wraps `cibuildwheel` with `uvx` and uploads
  architecture-specific wheel artifacts.
- `.github/actions/pure-python-wheel` builds a pure Python wheel with
  `uv build --wheel` and uploads the resulting artifact.
- `.github/dependabot.yml` enables dependency update pull requests for GitHub
  Actions and Python packages. Rust-enabled projects also receive Cargo updates.

The `CS_ACCESS_TOKEN` secret must be configured when CodeScene coverage upload
is required. The `CODESCENE_CLI_SHA256` variable should be populated using the
refresh workflow, so CI can verify the downloaded CodeScene installer before
upload.
