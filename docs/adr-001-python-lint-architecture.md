# ADR-001: Four-tier Python lint architecture

- Status: accepted
- Date: 2026-08-27
- Amendments: [2026-09-25](#amendment-2026-09-25-plain-pylint-on-pypy-312)

## Context

The project inherits the df12 house lint policy from `leynos/lading`,
`leynos/episodic`, and `leynos/cuprum`. A single `make lint` invocation must
give contributors the complete Python lint verdict, and CI must run exactly the
same command with exactly the same tool releases. Dead code is a distinct
failure mode from style or correctness findings: it accumulates silently,
survives review, and misleads readers about which code paths matter.

## Decision

`make lint` runs four blocking Python lint tiers, in order:

1. **Ruff** — fast, broad lint rules and docstring style, pinned to
   `RUFF_VERSION` and configured in `pyproject.toml`.
2. **Interrogate** — 100 per cent docstring presence across
   `$(PYTHON_TARGETS)`.
3. **Pylint** — two focused passes: the classic selected messages under PyPy,
   and the `df12-python-lints` plugin messages under CPython `$(DF12_PYTHON)`.
   The original PyPy pass ran through the pinned `pylint-pypy-shim` runner; see
   the [2026-09-25 amendment](#amendment-2026-09-25-plain-pylint-on-pypy-312)
   for the current shape.
4. **Skylos** — strict production dead-code detection, pinned to
   `SKYLOS_VERSION` and run under Python 3.14.

`ambrleaks` accompanies the tiers as a snapshot-hygiene sweep of `tests/`.

Skylos scans production targets only (`SKYLOS_PRODUCTION_TARGETS`), excludes
the test tree (`SKYLOS_EXCLUDE_FOLDERS`), and uses the strict gate
configuration in `pyproject.toml`. Its standalone tool environment is pinned to
Python 3.14 because Skylos parses source with its own runtime AST; an older
interpreter would report phantom findings on newer syntax.

False positives follow a verified-exception policy. Implicit runtime callers
are modelled as typed `[[tool.skylos.dead_code.entrypoints]]` rules with
reasons. Only when an entry-point rule cannot model the boundary is a
documented allow-list entry recorded, through
`make skylos-allow SYMBOL=<symbol> REASON="<evidence>"`. The `skylos-allow`
target validates that both values contain non-whitespace text, reads `SYMBOL`
rather than WSL's caller-owned `NAME` environment variable, and serializes the
read-modify-write update with `flock` on an ignored repository-local lock file,
so concurrent recordings remain intact.

Contract tests in `tests/test_skylos_lint_contract.py` and
`tests/test_skylos_whitelist_boundary.py` parse the Makefile with the pinned
`makeutil` binary and the workflows with PyYAML, asserting the tier order, tool
pins, strict configuration, and whitelist argument forwarding rather than
matching source text.

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
- Skylos, Ruff, ty, and the PyPy-backed Pylint pass are separate version pins
  that must be maintained (contract tests enforce the cross-site agreements).

## Amendment (2026-09-25): plain Pylint on PyPy 3.12

The original PyPy-backed Pylint pass ran through the pinned `pylint-pypy-shim`
repository, which patched the object-build step so Pylint could parse source
under PyPy. It also disabled `syntax-error` in `pyproject.toml`.

uv 0.12.19 (2026-09-25) ships PyPy 8 as a managed interpreter, and PyPy 8
implements Python 3.12. Plain Pylint now runs on it without the shim's
object-build patch, so the pass runs `uv tool run` with
`--python $(PYLINT_PYTHON)` (pinned to `pypy@3.12`, not bare `pypy`, so a new
PyPy release cannot change the parsed grammar without a commit) and
`--from 'pylint==$(PYLINT_VERSION)'`, dropping `PYLINT_PYPY_SHIM_REF` and
`PYLINT_PYPY_SHIM`.

`pyproject.toml` no longer disables `syntax-error`. While it was disabled, any
module the PyPy runtime could not parse produced no messages at all and the
lint passed without linting it. In this repository no modules were skipped
under the shim's PyPy 3.11 (count zero), so this change prevents a silent skip
rather than surfacing previously hidden findings; a parse failure now fails the
lint.

The df12 tier (CPython `$(DF12_PYTHON)`, `df12-python-lints` plugin) is
unchanged.
