MDLINT ?= markdownlint-cli2
NIXIE ?= nixie
MDFORMAT_ALL ?= mdformat-all
export PATH := $(HOME)/.local/bin:$(HOME)/.bun/bin:$(PATH)
UV ?= $(shell command -v uv 2>/dev/null || printf '%s/.local/bin/uv' "$$HOME")
USER_CARGO := $(HOME)/.cargo/bin/cargo
USER_WHITAKER := $(HOME)/.local/bin/whitaker
USER_BIN_PATH := $(HOME)/.cargo/bin:$(HOME)/.local/bin:$(HOME)/.bun/bin
TOOLS = $(MDFORMAT_ALL) $(MDLINT)
VENV_TOOLS = pytest
UV_ENV = PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 UV_CACHE_DIR=.uv-cache UV_TOOL_DIR=.uv-tools
# Pin Ruff so `make` invokes the same version as the `ruff==` dev dependency
# in pyproject.toml and the RUFF_VERSION environment variable in
# .github/workflows/ci.yml. Bump all three sites together: a version mismatch
# causes version-skew lint failures because rule sets differ between Ruff
# releases. tests/test_toolchain_contract.py enforces the agreement.
RUFF_VERSION ?= 0.16.4
RUFF = $(UV_ENV) $(UV) tool run --from ruff==$(RUFF_VERSION) ruff
# Pin ty so `make` and CI invoke the same typechecker release. ty is pre-1.0
# and diagnostics shift between releases, so an unpinned install breaks the
# typecheck gate without any code change. Bump deliberately, alongside the
# `ty==` dev dependency in pyproject.toml and TY_VERSION in
# .github/workflows/ci.yml, and fix new diagnostics in the same commit.
TY_VERSION ?= 0.0.74
TY = $(UV_ENV) $(UV) tool run --from ty==$(TY_VERSION) ty
WITH_ACT ?= 0
ACT_TEST_ENV = $(if $(filter 1 true yes on,$(WITH_ACT)),RUN_ACT_VALIDATION=1,)
PYTEST_XDIST_WORKERS ?= auto
PYTHON_TARGETS ?= syrupy_mdast tests
PYLINT_PYTHON ?= pypy
PYLINT_TARGETS ?= $(PYTHON_TARGETS)
PYLINT_PYPY_SHIM_REF ?= 726d09f968b4d729ee4b29c71fc732e744854f3b
PYLINT_PYPY_SHIM = git+https://github.com/leynos/pylint-pypy-shim.git@$(PYLINT_PYPY_SHIM_REF)
# The PyPy-backed pass runs the classic Pylint messages only; plugins are
# disabled because df12-python-lints requires CPython semantics.
PYLINT = $(UV_ENV) $(UV) tool run --python $(PYLINT_PYTHON) --from '$(PYLINT_PYPY_SHIM)' pylint-pypy --load-plugins=
DF12_PYTHON_LINTS_REF ?= v0.3.0
DF12_PYTHON_LINTS = git+https://github.com/leynos/df12-python-lints.git@$(DF12_PYTHON_LINTS_REF)
# df12-python-lints runs under CPython so the plugin sees full CPython AST
# semantics; the PyPy shim above covers only the classic messages.
DF12_PYTHON ?= 3.14
# C9112 (redundant-future-annotations) is omitted deliberately: it targets a
# 3.14+ baseline, while this project keeps `from __future__ import
# annotations` on its 3.12 baseline (Ruff's FA family enforces the import).
DF12_PYLINT_MESSAGES = R9101,C9102,R9103,R9104,C9105,C9106,C9107,R9108,R9109,R9110,R9111,R9112
DF12_PYLINT = $(UV_ENV) $(UV) run --python $(DF12_PYTHON) pylint \
	--disable=all --load-plugins=df12_python_lints --enable=$(DF12_PYLINT_MESSAGES)
AMBRLEAKS = $(UV_ENV) $(UV) tool run --python $(DF12_PYTHON) \
	--from '$(DF12_PYTHON_LINTS)' ambrleaks


.PHONY: help all audit clean build build-release lint lint-python fmt check-fmt \
        markdownlint nixie test typecheck $(TOOLS) $(VENV_TOOLS)

.DEFAULT_GOAL := all

all: build check-fmt lint typecheck test

define ensure_uv
	@command -v $(UV) >/dev/null 2>&1 || { \
	  printf "Error: uv is required, but '%s' was not found or is not executable\n" "$(UV)" >&2; \
	  exit 1; \
	}
endef

.venv: pyproject.toml
	$(call ensure_uv)
	$(UV_ENV) $(UV) venv --clear

build: .venv ## Build virtual-env and install deps
	$(UV_ENV) $(UV) sync --group dev

build-release: ## Build artefacts (sdist & wheel)
	$(call ensure_uv)
	$(UV_ENV) $(UV) run python -m build --sdist --wheel

clean: ## Remove build artifacts
	rm -rf build dist *.egg-info \
	  .mypy_cache .pytest_cache .coverage coverage.* \
	  lcov.info htmlcov .venv .uv-cache .uv-tools
	find . -type d -name '__pycache__' -print0 | xargs -0 -r rm -rf

define ensure_tool
	@command -v $(1) >/dev/null 2>&1 || { \
	  printf "Error: '%s' is required, but not installed\n" "$(1)" >&2; \
	  exit 1; \
	}
endef

define ensure_tool_venv
	@$(UV_ENV) $(UV) run which $(1) >/dev/null 2>&1 || { \
	  printf "Error: '%s' is required in the virtualenv, but is not installed\n" "$(1)" >&2; \
	  exit 1; \
	}
endef

ifneq ($(strip $(TOOLS)),)
$(TOOLS): ## Verify required CLI tools
	$(call ensure_tool,$@)
endif


ifneq ($(strip $(VENV_TOOLS)),)
.PHONY: $(VENV_TOOLS)
$(VENV_TOOLS): build ## Verify required CLI tools in venv
	$(call ensure_tool_venv,$@)
endif


fmt: build $(MDFORMAT_ALL) ## Format sources
	$(RUFF) format $(PYTHON_TARGETS)
	$(RUFF) check --select I --fix $(PYTHON_TARGETS)

	$(MDFORMAT_ALL)

check-fmt: build ## Verify formatting
	$(RUFF) format --check $(PYTHON_TARGETS)

	# mdformat-all doesn't currently do checking

lint: lint-python ## Run linters

lint-python: build ## Run Python linters
	$(RUFF) check $(PYTHON_TARGETS)
	$(UV_ENV) $(UV) run interrogate --fail-under 100 $(PYTHON_TARGETS)
	$(PYLINT) $(PYLINT_TARGETS)
	$(DF12_PYLINT) $(PYLINT_TARGETS)
	$(AMBRLEAKS) tests


typecheck: build ## Run typechecking
	$(TY) --version
	$(TY) check $(PYTHON_TARGETS)

audit: build ## Audit dependencies for known vulnerabilities
	$(UV_ENV) $(UV) run pip-audit


markdownlint: $(MDLINT) ## Lint Markdown files
	env -u NO_COLOR $(MDLINT) '**/*.md'

nixie: ## Validate Mermaid diagrams
	$(call ensure_tool,$(NIXIE))
	$(NIXIE) --no-sandbox

test: build $(VENV_TOOLS) ## Run tests
	$(UV_ENV) $(ACT_TEST_ENV) $(UV) run pytest -v -n $(PYTEST_XDIST_WORKERS)


help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS=":.*##"; printf "Available targets:\n"} {gsub(/^[[:space:]]+/, "", $$2); printf "  %-20s %s\n", $$1, $$2}'
