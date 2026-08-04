# syrupy-mdast roadmap

This roadmap translates the [technical design](syrupy-mdast-design.md) into an
outcome-oriented delivery sequence. It does not promise dates. Each phase
carries a testable idea at the Goals, Ideas, Steps, Tasks (GIST) level; steps
answer sequencing questions, and tasks are review-sized execution units.

The technical design is the primary source. Future Requests for Comments (RFCs)
and Architecture Decision Records (ADRs) under `docs/` take precedence where
the design identifies them as authoritative.

## 1. Foundational Wenmode contracts

Idea (re-architecting): if syrupy-mdast ratifies Wenmode's GitHub profile and
its Python-only package boundary before feature work, every later slice can use
one parser contract in editable checkouts, wheels, and Continuous Integration
(CI).

### 1.1. Ratify the v1 comparison and compatibility contracts

This step answers which differences v1 removes, preserves, and defers. Its
outcome bounds every parser, serializer, and compatibility decision. See the
[technical design](syrupy-mdast-design.md) §§2-4, §8, and §13.

- [ ] 1.1.1. Replace the generated package stub with the v1 public contract.
  - Declare the supported Python and Syrupy ranges in `pyproject.toml`.
  - Define the base domain error in a dependency-free core and export it with
    the extension without exposing parser internals.
  - Remove the generated `hello` API and document the compatibility policy.
  - Success: import and API-stability checks expose only the names defined in
    design §6.
- [ ] 1.1.2. Record the parser-profile and snapshot-version policy in an ADR.
  - Requires 1.1.1.
  - Fix the exact Wenmode release and its GitHub profile as v1.
  - Version the parser profile, normalization policy, comparison contract, and
    their normative fixtures together.
  - Record resolved ordinary references, structural footnotes, omitted
    nullable fields, and Wenmode's GitHub HTML policy.
  - See design §§7, 13, and 15.
  - Success: the explicitly versioned ADR is accepted before implementation or
    normative fixtures encode its decisions.
- [ ] 1.1.3. Create the canonical Markdown contract corpus.
  - Requires 1.1.2.
  - Pair syntax-equivalent emphasis, line-ending, and direct/reference-link
    inputs.
  - Include distinct hard breaks, code whitespace, list ordering, table
    alignment, footnotes, raw HTML, and other GitHub-profile nodes.
  - Cover full, collapsed, shortcut, forward, unresolved, and unused ordinary
    references.
  - Success: every normalization and preservation rule in design §8 maps to a
    focused, reviewer-readable fixture.

### 1.2. Prove the Python-only dependency boundary

This step answers whether editable and installed use the same exact Wenmode
contract without cross-runtime assets. It replaces the previous Bun package
boundary before parsing logic depends on it.

- [ ] 1.2.1. Add the exact Wenmode runtime dependency.
  - Requires 1.1.3.
  - Pin the reviewed Wenmode release in `pyproject.toml` and record its licence.
  - Confirm the wheel contains no Bun, Node.js, TypeScript, JavaScript manifest,
    lockfile, or installed JavaScript package assets.
  - Success: an isolated Python installation imports the selected Wenmode
    release without a JavaScript runtime or network access at parse time.
- [ ] 1.2.2. Define the narrow internal Wenmode adapter seam.
  - Requires 1.2.1.
  - Construct a fresh `Parser(github, positions=False)` for every adapter call.
  - Return Wenmode's public `to_ast()` data without a speculative pluggable
    backend abstraction.
  - Success: sequential documents do not leak ordinary reference or footnote
    state; barrier-controlled thread contention and interleaving plus a
    re-entrant parser double prove that every call has independent parser
    state; and pytest-xdist workers use independent per-call parser instances.
- [ ] 1.2.3. Prove Wenmode's normative AST decisions.
  - Requires 1.2.2.
  - Add focused probes for resolved ordinary references, structural footnotes,
    omitted nullable fields, and raw HTML under the GitHub profile.
  - Success: the fixtures fail if a parser upgrade changes any ratified
    decision.

## 2. Vertical slice: AST-aware Markdown snapshots

Idea (capability): if one assertion can parse with in-process Wenmode,
canonicalize its mdast-compatible tree, and use Syrupy's native single-file
lifecycle, users gain meaningful Markdown snapshot comparisons without a second
language runtime.

### 2.1. Prove canonical trees capture the intended distinctions

This step answers whether the fixed parser profile and normalization algorithm
produce a stable, conservative tree contract. Its result determines whether the
Python extension is safe to expose. See design §§7-8 and §11.

- [ ] 2.1.1. Implement GitHub-profile Markdown parsing.
  - Requires 1.1.2, 1.2.2, and 1.2.3.
  - Parse strings through `Parser(github, positions=False)` and obtain ordinary
    Python data through `to_ast()`.
  - Validate that the result is a root mapping with a children array.
  - Success: the contract corpus produces expected CommonMark, GFM, and
    footnote nodes without file, network, shell, or child-process access.
- [ ] 2.1.2. Implement recursive canonicalization with generated invariants.
  - Requires 2.1.1.
  - Remove `position`, remove only empty plain-object `data`, normalize CRLF and
    CR in strings, and order keys by the normative sequence.
  - Preserve unknown fields, false values, zeroes, empty strings, empty arrays,
    non-empty `data`, and array order; do not synthesize omitted `null` fields.
  - Verify idempotence, position invariance, and line-ending invariance with
    property-generated JSON trees.
  - Keep canonicalization and AST-shape validation in a dependency-free domain
    core with no Wenmode or Syrupy imports.
  - Success: the corpus detects every named preservation change while each
    equivalence pair produces identical normalized JSON; core tests run without
    infrastructure dependencies, and an architecture test enforces the import
    boundary.

### 2.2. Deliver bounded in-process parsing and serialization

This step answers whether repository-controlled Markdown produces deterministic
output and actionable errors within the v1 resource policy. See design §§5, 9,
and 12.

- [ ] 2.2.1. Implement the canonical JSON writer.
  - Requires 2.1.2.
  - Re-serialize valid trees as UTF-8, two-space JSON with unescaped Unicode
    and one final newline.
  - Keep JSON serialization behind a narrow adapter that accepts only a
    validated canonical tree.
  - Define the shared `MAX_INPUT_BYTES = 1_048_576` limit, count strict UTF-8
    bytes in fixed-size source slices, and stop before Wenmode as soon as the
    limit is exceeded.
  - Success: source-tree and installed-wheel calls return byte-identical
    payloads using Python dependencies only, and boundary tests accept the
    limit and reject the next UTF-8 byte. An instrumented encoder proves that
    oversized input does not produce a complete encoded copy.
- [ ] 2.2.2. Implement narrow failure translation.
  - Requires 2.2.1.
  - Preserve `TypeError` and `ValueError` for caller contract errors.
  - Catch only `UnicodeEncodeError` from strict UTF-8 input encoding and
    translate it to the core `MarkdownAstError`, with surrogate remediation,
    before invoking Wenmode.
  - Translate documented Wenmode parse failures and invalid AST or JSON output
    to the core `MarkdownAstError` at the application pipeline boundary without
    catching unrelated programming failures.
  - Define the shared `MAX_DIAGNOSTIC_EXCERPT_CHARS = 512` limit and append
    ordinary code points or complete `\uXXXX` control tokens to a bounded
    builder until the next token would exceed it.
  - Success: every failure in design §9 has its declared type and an actionable
    message; boundary tests accept 512-character excerpts and truncate longer
    excerpts without splitting escape tokens. A counting iterator proves that
    control-heavy input does not produce a complete escaped copy. An
    unpaired-surrogate test proves the encoding failure is translated and
    Wenmode is not invoked.

### 2.3. Make canonical trees a native Syrupy assertion

This step answers whether the parser contract fits Syrupy's update, deletion,
and diff lifecycle without a parallel snapshot mechanism. See design §§6 and 10.

- [ ] 2.3.1. Implement `MarkdownAstSnapshotExtension`.
  - Requires steps 2.1-2.2.
  - Subclass `SingleFileSnapshotExtension`, set
    `file_extension = "mdast.json"` and `_write_mode = WriteMode.TEXT`, accept
    only `str`, and reject unsupported Syrupy property controls.
  - Keep the extension as a thin Syrupy adapter that delegates parsing,
    canonicalization, failure translation, and serialization to the internal
    application pipeline.
  - Success: create, compare, update, and delete operations use Syrupy's native
    single-file lifecycle, producing one readable text `.mdast.json` snapshot
    per assertion and readable JSON diffs.
- [ ] 2.3.2. Publish the documented pytest fixture recipe.
  - Requires 2.3.1.
  - Demonstrate `snapshot.with_defaults(extension_class=...)` with a typed
    fixture and representative Markdown.
  - See design §6.
  - Success: a consumer can copy the recipe without importing internal modules
    or configuring parser paths.

### 2.4. Demonstrate supported combinations end to end

This step answers whether packaging, parser semantics, errors, and independent
pytest-xdist parser instances work together rather than only behind mocked
boundaries. Parsing remains in-process by default; v1 provides neither a Python
worker nor crash or process isolation. See design §§10-11 and §16.

- [ ] 2.4.1. Build the installed-wheel end-to-end suite.
  - Requires 2.3.2.
  - Build and install a wheel into an isolated Python environment and run real
    CommonMark and GFM assertions.
  - Inspect the wheel to exclude JavaScript source, manifests, lockfiles, and
    package directories.
  - Success: the suite parses with the exact Wenmode dependency and no
    repository-relative or cross-runtime asset.
- [ ] 2.4.2. Add the combinatorial compatibility suite.
  - Requires 2.4.1.
  - Cover CommonMark and GFM, LF/CRLF/CR, documented errors, parser isolation,
    same-process contention and re-entrancy, serial pytest and pytest-xdist, and
    the supported Python and Syrupy matrix.
  - Exercise the pinned Wenmode release and candidate upgrades against the same
    mandatory fixtures.
  - Use pairwise reduction only after the combinations in design §11 remain
    explicit.
  - Success: each supported combination completes a real assertion or produces
    its specified failure type.

## 3. Trustworthy adoption and dependency evolution

Idea (capability): if users can install, understand, diagnose, and upgrade the
Python-only extension without reading its source, syrupy-mdast can be adopted
as a normal test dependency rather than a repository-specific tool.

### 3.1. Deliver consumer and maintainer workflows

This step answers whether both audiences can operate the package from its
documented interfaces. It also reconciles generated scaffold documentation with
the implemented product. See design §§6-7, §§9-10, and §§13-16.

- [ ] 3.1.1. Replace the generated user guide with the product workflow.
  - Requires phase 2.
  - Document Python installation, fixture setup, supported syntax, ordinary
    reference equivalence, structural footnotes, snapshot interpretation,
    failure remediation, and migrations.
  - State that Bun, Node.js, TypeScript, and JavaScript packages are not needed.
  - Success: every public interface and error type has one executable or
    copyable example.
- [ ] 3.1.2. Document the Python-only maintainer workflow.
  - Requires 3.1.1.
  - Update the developer guide and repository layout for Wenmode upgrades,
    corpus diffs, wheel inspection, and compatibility validation.
  - Remove obsolete mixed-runtime installation and packaging guidance.
  - Success: the documentation index links each normative guide exactly once,
    and no generated-project or Bun-era wording remains.

### 3.2. Make parser upgrades reviewable

This step answers whether dependency updates can be classified before they
rewrite snapshots. See design §§4, 13, and 15.

- [ ] 3.2.1. Add a Wenmode-upgrade contract report.
  - Requires 1.1.2 and phase 2.
  - Run the canonical corpus against the pinned and candidate Wenmode releases.
  - Classify payload differences as additions, parser fixes, intentional
    migrations, or regressions requiring an upstream report.
  - Success: CI attaches or prints a focused payload diff for every proposed
    Wenmode update.
- [ ] 3.2.2. Establish release and audit gates.
  - Requires 3.2.1.
  - Audit the Python dependency graph, inspect wheel contents, validate licence
    notices, and reject unreviewed canonical-output changes.
  - Success: a release cannot loosen the Wenmode pin, introduce an undeclared
    cross-runtime asset, or ship an unclassified snapshot change.

### 3.3. Measure the in-process implementation

This step answers whether parsing and canonicalization remain practical for
real test suites. See design §15.

- [ ] 3.3.1. Add reproducible serialization benchmarks.
  - Requires 2.3.1.
  - Measure Wenmode parsing and Python canonicalization separately across small,
    medium, and large Markdown fixtures.
  - Record environment metadata without turning benchmark variance into a CI
    correctness failure.
  - Success: results identify material scaling costs and establish a baseline
    for future parser or canonicalizer changes.

## 4. Deferred extensions after the v1 promise

Idea (capability): if the fixed Wenmode GitHub-profile contract is trustworthy
and routine to operate, broader comparison and isolation policies can be
evaluated on user value without destabilizing the initial snapshot format.

### 4.1. Evaluate additional syntax profiles

This step asks which syntax ecosystems justify expanding the parser-profile
matrix. See design §§2, 7, and 15.

- [ ] 4.1.1. Design opt-in frontmatter, math, and directive profiles.
  - Requires phase 3.
  - Compare adoption evidence, Wenmode extension contracts, compatibility
    costs, and combinatorial coverage requirements.
  - Success: an accepted design update either defines named, versioned profiles
    or records why the fixed v1 profile remains sufficient.
- [ ] 4.1.2. Evaluate MDX as a separate compatibility boundary.
  - Requires 4.1.1.
  - Treat executable expressions and JSX nodes as a security and schema change,
    not another transparent parser switch.
  - Success: an ADR accepts a bounded MDX contract or rejects it with explicit
    reconsideration criteria.

### 4.2. Evaluate richer semantic and isolation policies

This step asks whether users need deliberate equivalence or containment beyond
the v1 contract. See design §§2, 8, 12, and 15.

- [ ] 4.2.1. Design named normalization policies.
  - Requires phase 3.
  - Evaluate ignored table alignment and other requested policies as enums or
    immutable option objects rather than Boolean flags.
  - Success: any accepted policy defines its snapshot-version effect and
    interaction matrix before implementation.
- [ ] 4.2.2. Evaluate preservation of ordinary reference source structure.
  - Requires 4.2.1.
  - Establish user evidence for retaining definitions, identifiers, and
    full/collapsed/shortcut forms before designing custom Wenmode rules.
  - Success: an accepted design either adds a separate source-structural mode
    or retains resolved references as the sole contract.
- [ ] 4.2.3. Evaluate hast normalization for raw HTML nodes.
  - Requires 4.2.1.
  - Define renderer assumptions, sanitization boundaries, and the loss of raw
    Markdown structure.
  - Success: evidence supports a separate HTML-aware extension rather than an
    implicit change to `MarkdownAstSnapshotExtension`.
- [ ] 4.2.4. Design a Python worker only for a hostile-input requirement.
  - Requires phase 3 and an accepted threat-model change.
  - Define process ownership, timeouts, bounded protocol, pytest-xdist
    isolation, teardown, and denial-of-service tests.
  - Success: in-process parsing remains the default unless an ADR demonstrates
    that hostile-input containment is a product requirement.
