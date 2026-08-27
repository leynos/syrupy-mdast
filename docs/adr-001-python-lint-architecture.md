# ADR-001: Four-tier Python lint architecture

- Status: accepted
- Date: 2026-08-27

## Context

The project inherits the df12 house lint policy from `leynos/lading`,
`leynos/episodic`, and `leynos/cuprum`. A single `make lint` invocation must
give contributors the complete Python lint verdict, and CI must run exactly
the same command with exactly the same tool releases. Dead code is a distinct
failure mode from style or correctness findings: it accumulates silently,
survives review, and misleads readers about which code paths matter.

## Decision

`make lint` runs four blocking Python lint tiers, in order:

1. **Ruff** — fast, broad lint rules and docstring style, pinned to
   `RUFF_VERSION` and configured in `pyproject.toml`.
2. **Interrogate** — 100 per cent docstring presence across
   `$(PYTHON_TARGETS)`.
3. **Pylint** — two focused passes: the classic selected messages through the
   PyPy-backed `pylint-pypy-shim` runner, and the `df12-python-lints` plugin
   messages under CPython `$(DF12_PYTHON)`.
4. **Skylos** — strict production dead-code detection, pinned to
   `SKYLOS_VERSION` and run under Python 3.14.

`ambrleaks` accompanies the tiers as a snapshot-hygiene sweep of `tests/`.

Skylos scans production targets only (`SKYLOS_PRODUCTION_TARGETS`), excludes
the test tree (`SKYLOS_EXCLUDE_FOLDERS`), and uses the strict gate
configuration in `pyproject.toml`. Its standalone tool environment is pinned
to Python 3.14 because Skylos parses source with its own runtime AST; an older
interpreter would report phantom findings on newer syntax.

False positives follow a verified-exception policy. Implicit runtime callers
are modelled as typed `[[tool.skylos.dead_code.entrypoints]]` rules with
reasons. Only when an entry-point rule cannot model the boundary is a
documented allow-list entry recorded, through
`make skylos-allow SYMBOL=<symbol> REASON="<evidence>"`. The `skylos-allow`
target validates that both values contain non-whitespace text, reads `SYMBOL`
rather than WSL's caller-owned `NAME` environment variable, and serializes the
read-modify-write update with `flock` on an ignored repository-local lock
file, so concurrent recordings remain intact.

Contract tests in `tests/test_skylos_lint_contract.py` and
`tests/test_skylos_whitelist_boundary.py` parse the Makefile with the pinned
`makeutil` binary and the workflows with PyYAML, asserting the tier order,
tool pins, strict configuration, and whitelist argument forwarding rather
than matching source text.

## Consequences

### Positive

- Contributors run one command, `make lint`, for the complete Python lint
  policy, and CI runs the identical pinned toolchain.
- Dead code cannot land silently: the strict Skylos gate blocks merges, and
  every exception carries an auditable reason.
- The policy stays aligned with the sibling df12 repositories.

### Negative

- The full lint target is slower than Ruff alone, and first runs download
  PyPy, CPython 3.14, and the pinned tool environments.
- The `makeutil` parser is a Rust toolchain dependency for the test suite,
  pinned per workflow and installed locally with a nightly toolchain.
- Skylos, Ruff, ty, and the Pylint shim are separate version pins that must
  be maintained (contract tests enforce the cross-site agreements).
