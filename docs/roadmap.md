# syrupy-mdast roadmap

This roadmap translates the [technical design](syrupy-mdast-design.md) into an
outcome-oriented delivery sequence. It does not promise dates. Each phase
carries a testable idea at the Goals, Ideas, Steps, Tasks (GIST) level; steps
answer sequencing questions, and tasks are review-sized execution units.

The technical design is the primary source. Future Requests for Comments (RFCs)
and Architecture Decision Records (ADRs) under `docs/` will take precedence
where the design identifies them as authoritative.

## 1. Foundational contracts and reproducible package boundary

Idea: if syrupy-mdast settles its comparison contract and reproduces
`simulacat`'s installed Python-and-Bun asset boundary before feature work, the
first snapshot slice can use one public API and one runtime layout in editable
checkouts, wheels, and Continuous Integration (CI).

### 1.1. Ratify the v1 comparison and compatibility contracts

This step answers which differences v1 removes, preserves, and defers. Its
outcome bounds every parser, serializer, and compatibility decision. See
[technical design](syrupy-mdast-design.md) §§2-4, §8, and §13.

- [ ] 1.1.1. Replace the generated package stub with the v1 public contract.
  - Declare the supported Python and Syrupy ranges in `pyproject.toml`.
  - Export the extension and exception hierarchy without exposing runner
    internals.
  - Remove the generated `hello` API and document the compatibility policy.
  - Success: import and API-stability checks expose only the names defined in
    design §6.
- [ ] 1.1.2. Create the canonical Markdown contract corpus.
  - Requires 1.1.1.
  - Pair syntax-equivalent emphasis and line-ending inputs.
  - Include distinct hard breaks, code whitespace, list ordering, table
    alignment, references, raw HTML, and GFM nodes.
  - Success: every normalization and preservation rule in design §8 maps to a
    focused, reviewer-readable fixture.
- [ ] 1.1.3. Record the parser-profile and snapshot-version policy in an ADR.
  - Requires 1.1.2.
  - Fix CommonMark plus all GFM constructs as v1 and record the SemVer migration
    rules.
  - See design §§7, 13, and 15.
  - Success: later syntax additions have an accepted decision process rather
    than silently changing snapshots.

### 1.2. Prove the installed Bun asset layout

This step answers whether an installed wheel can find and prepare the same
TypeScript parser assets as an editable checkout. It applies the prior art in
design §7 before parsing logic depends on it.

- [ ] 1.2.1. Add the locked TypeScript package skeleton.
  - Requires 1.1.3.
  - Add `src/markdown-to-mdast.ts`, `package.json`, and `bun.lock` with exact
    parser dependency versions.
  - Configure Hatch to force-include the three assets beneath `syrupy_mdast/`.
  - Success: wheel inspection finds each asset at its designed installed path.
- [ ] 1.2.2. Implement installed and editable asset resolution.
  - Requires 1.2.1.
  - Resolve package assets with `importlib.resources` and use a repository
    fallback only for editable development.
  - Add `python -m syrupy_mdast.js_root` as the stable package-root query.
  - Success: both layouts resolve absolute entrypoint and manifest paths
    without depending on the current working directory.
- [ ] 1.2.3. Add the explicit parser-dependency installer.
  - Requires 1.2.2.
  - Implement `python -m syrupy_mdast.install_parser_deps` with an explicit Bun
    argument vector, packaged lockfile, bounded timeout, and typed failures.
  - See design §§7, 9, and 12.
  - Success: successful, missing-Bun, non-zero, and timeout outcomes are
    deterministic, and no shell is invoked.

## 2. Vertical slice: AST-aware Markdown snapshots

Idea: if one assertion can traverse the packaged Bun parser, canonicalize
mdast, and use Syrupy's native single-file lifecycle, users gain meaningful
Markdown snapshot comparisons before configurable profiles or performance
machinery exist.

### 2.1. Prove canonical mdast captures the intended distinctions

This step answers whether the fixed parser profile and normalization algorithm
produce a stable, conservative tree contract. Its result determines whether the
Python extension is safe to expose. See design §§7-8 and §11.

- [ ] 2.1.1. Implement the CommonMark and GFM TypeScript parser.
  - Requires 1.1.2 and 1.2.1.
  - Compose `mdast-util-from-markdown`, `micromark-extension-gfm`, and
    `mdast-util-gfm` through standard input and standard output.
  - Emit exactly one JSON value and one final newline.
  - Success: the contract corpus produces the expected core and GFM node types
    without source-dependent file access.
- [ ] 2.1.2. Implement recursive canonicalization with generated invariants.
  - Requires 2.1.1.
  - Remove `position`, remove only empty plain-object `data`, normalize CRLF and
    CR in strings, and order keys by the normative sequence.
  - Preserve unknown fields, false values, zeroes, nulls, empty arrays, and
    array order.
  - Verify idempotence, position invariance, and line-ending invariance with
    property-generated JSON trees.
  - Success: the corpus detects every named preservation change while each
    equivalence pair produces identical normalized JSON.

### 2.2. Deliver bounded Python process and protocol handling

This step answers whether untrusted Markdown can cross the Bun boundary with
predictable resources and actionable errors. Its outcome unlocks the public
Syrupy adapter. See design §§5, 9, and 12.

- [ ] 2.2.1. Implement the typed parser runner and canonical JSON writer.
  - Requires 1.2.2 and 2.1.2.
  - Resolve and validate Bun, pass Markdown on standard input, impose the input
    and execution bounds, and validate the root protocol shape.
  - Re-serialize valid trees as UTF-8, two-space JSON with unescaped Unicode
    and one final newline.
  - Success: source-tree and installed-wheel calls return byte-identical
    payloads without a shell or network access.
- [ ] 2.2.2. Implement bounded failure translation.
  - Requires 2.2.1.
  - Distinguish environment, execution, parse, and protocol failures.
  - Cap output excerpts and avoid echoing complete source documents or
    environments.
  - Success: each failure in design §9 raises its declared public category with
    an actionable, bounded diagnostic.

### 2.3. Make canonical mdast a native Syrupy assertion

This step answers whether the parser contract fits Syrupy's update, deletion,
and diff lifecycle without a parallel snapshot mechanism. See design §§6 and 10.

- [ ] 2.3.1. Implement `MarkdownAstSnapshotExtension`.
  - Requires steps 2.1-2.2.
  - Subclass `SingleFileSnapshotExtension`, select text mode and
    `.mdast.json`, accept only `str`, and reject unsupported Syrupy property
    controls.
  - Success: create, compare, update, and delete operations use Syrupy's native
    lifecycle and produce readable JSON diffs.
- [ ] 2.3.2. Publish the documented pytest fixture recipe.
  - Requires 2.3.1.
  - Demonstrate `snapshot.with_defaults(extension_class=...)` with a typed
    fixture and representative Markdown.
  - See design §6.
  - Success: a consumer can copy the recipe without importing internal modules
    or configuring parser paths.

### 2.4. Demonstrate the supported combinations end to end

This step answers whether packaging, parser profile, errors, and concurrency
work together rather than only behind mocked boundaries. See design §§10-11 and
§16.

- [ ] 2.4.1. Build the installed-wheel end-to-end suite.
  - Requires 2.3.2.
  - Build and install a wheel into an isolated environment, install its locked
    parser dependencies through the public module command, and run real
    assertions against the packaged entrypoint.
  - Success: the suite proves that no repository-relative parser asset is used.
- [ ] 2.4.2. Add the cross-runtime combinatorial suite.
  - Requires 2.4.1.
  - Cover CommonMark and GFM, LF/CRLF/CR, mandatory error categories, serial
    pytest and pytest-xdist, and the supported Python, Syrupy, and Bun matrix.
  - Use pairwise reduction only after the mandatory combinations in design §11
    remain explicit.
  - Success: each supported combination either completes a real assertion or
    produces its specified failure category.

## 3. Trustworthy adoption and dependency evolution

Idea: if users can install, diagnose, and upgrade the mixed-runtime extension
without reading its source, syrupy-mdast can be adopted as a normal test
dependency rather than a repository-specific tool.

### 3.1. Deliver the consumer and maintainer workflows

This step answers whether both audiences can operate the package from its
documented interfaces. It also reconciles the generated scaffold documentation
with the implemented product. See design §§6-7, §§9-10, and §§13-16.

- [ ] 3.1.1. Replace the generated user guide with the product workflow.
  - Requires phase 2.
  - Document Python and Bun prerequisites, installation, parser dependency
    installation, fixture setup, supported syntax, snapshot interpretation,
    failure remediation, and migrations.
  - Success: every public command and error category has one executable or
    copyable example.
- [ ] 3.1.2. Document the mixed-runtime maintainer workflow.
  - Requires 3.1.1.
  - Update the developer guide and repository layout for TypeScript source,
    lockfile updates, asset force-inclusion, wheel inspection, and matrix
    validation.
  - Success: the documentation index links each normative guide exactly once,
    and no generated-project wording remains.

### 3.2. Make parser upgrades reviewable

This step answers whether dependency updates can be classified before they
rewrite snapshots. See design §§4, 13, and 15.

- [ ] 3.2.1. Add a parser-upgrade contract report.
  - Requires 1.1.2 and phase 2.
  - Compare canonical corpus output before and after lockfile changes and
    classify additions, fixes, and breaking reinterpretations.
  - Success: CI attaches or prints a focused payload diff for any parser update.
- [ ] 3.2.2. Establish release and audit gates for mixed dependencies.
  - Requires 3.2.1.
  - Audit Python and JavaScript dependency graphs, inspect wheel contents, and
    validate licence notices before release.
  - Success: a release cannot omit parser assets, use an unlocked dependency,
    or ship an unreviewed canonical-output change.

### 3.3. Measure before changing the process model

This step answers whether short-lived Bun processes are adequate for real test
suites and supplies evidence for any later worker design. See design §§3 and 15.

- [ ] 3.3.1. Add reproducible serialization benchmarks.
  - Requires 2.3.1.
  - Measure process startup and parse time separately across small, medium, and
    large Markdown fixtures.
  - Record environment metadata without turning benchmark variance into a CI
    correctness failure.
  - Success: results identify whether startup or parsing dominates and define a
    measured threshold for reconsidering a persistent worker.

## 4. Deferred extensions after the v1 promise

Idea: if the fixed CommonMark-plus-GFM contract is trustworthy and routine to
operate, broader comparison policies can be evaluated on user value without
destabilizing the initial snapshot format.

### 4.1. Evaluate additional syntax profiles

This step asks which syntax ecosystems justify expanding the parser-profile
matrix. See design §§2, 7, and 15.

- [ ] 4.1.1. Design opt-in frontmatter, math, and directive profiles.
  - Requires phase 3.
  - Compare adoption evidence, mdast extension contracts, compatibility costs,
    and combinatorial coverage requirements.
  - Success: an accepted design update either defines named, versioned profiles
    or records why the fixed v1 profile remains sufficient.
- [ ] 4.1.2. Evaluate MDX as a separate compatibility boundary.
  - Requires 4.1.1.
  - Treat executable expressions and JSX nodes as a security and schema change,
    not another transparent parser switch.
  - Success: an ADR accepts a bounded MDX contract or rejects it with explicit
    reconsideration criteria.

### 4.2. Evaluate richer semantic policies

This step asks whether users need deliberate equivalence beyond mdast's native
structure. See design §§2, 8, and 15.

- [ ] 4.2.1. Design named normalization policies.
  - Requires phase 3.
  - Evaluate ignored table alignment, normalized reference labels, and other
    requested policies as enums or immutable option objects rather than Boolean
    flags.
  - Success: any accepted policy defines its snapshot-version effect and
    interaction matrix before implementation.
- [ ] 4.2.2. Evaluate hast normalization for raw HTML nodes.
  - Requires 4.2.1.
  - Define renderer assumptions, sanitization boundaries, and the loss of raw
    Markdown structure.
  - Success: evidence supports a separate HTML-aware extension rather than an
    implicit change to `MarkdownAstSnapshotExtension`.
- [ ] 4.2.3. Reconsider a persistent parser only from benchmark evidence.
  - Requires 3.3.1.
  - Design worker ownership, cancellation, pytest-xdist isolation, teardown,
    and protocol recovery if the measured threshold is exceeded.
  - Success: the short-lived model remains the default unless an accepted ADR
    demonstrates a material suite-level improvement.
