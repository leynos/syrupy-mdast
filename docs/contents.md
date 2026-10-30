# Documentation contents

[Documentation contents](contents.md) is the index for syrupy-mdast's
documentation set.

## Project guides

- [Technical design](syrupy-mdast-design.md) defines the comparison contract,
  Python-only Wenmode architecture, canonical AST format, and verification
  properties.
- [Development roadmap](roadmap.md) translates the technical design into
  dependency-aware, outcome-oriented implementation slices.
- [User guide](users-guide.md) explains how to use the generated project and
  its public build and test commands.
- [Migration guide for 0.2.x](migration-0.2.md) records the pre-1.0 changes
  from the generated package stub to the v1 public contract.
- [Developer guide](developers-guide.md) explains the contributor workflow and
  points maintainers to script automation standards.
- [Canonical Markdown contract corpus](../tests/fixtures/markdown_contract/README.md)
  records the normative examples and authored expected payloads for future
  parser and canonicalizer conformance work.
- [Documentation style guide](documentation-style-guide.md) defines the
  spelling, structure, Markdown, Architecture Decision Record (ADR), Request
  for Comments (RFC), and roadmap conventions used by this documentation set.

## Decision records

- [ADR-001: Four-tier Python lint architecture](adr-001-python-lint-architecture.md)
  records the blocking lint tiers (Ruff, Interrogate, Pylint, and Skylos
  dead-code detection), their version pins, and the verified false-positive
  policy.
- [ADR-002: `main` owns CodeScene coverage publication](adr-002-main-owns-codescene-coverage-publication.md)
  records why only the push-to-`main` publisher contacts CodeScene, and how
  pull requests ratchet coverage without it.
- [ADR-003: Snapshot-version policy](adr-003-snapshot-version-policy.md)
  records the accepted absence of a payload marker, package and contract
  versioning, and Wenmode upgrade policy.
- [ADR-004: Parser profile and normalization](adr-004-parser-profile-and-normalization.md)
  records the accepted Wenmode parser profile, canonicalization rules, writer,
  and normative fixture decisions.
- [ADR-005: Exact Wenmode runtime dependency](adr-005-exact-wenmode-runtime-dependency.md)
  records the reviewed exact runtime dependency and upgrade policy.

## Engineering practice

- [Complexity antipatterns and refactoring strategies](complexity-antipatterns-and-refactoring-strategies.md)
  explains cognitive complexity, the bumpy-road antipattern, and refactoring
  approaches for maintainable code.
- [Local validation of GitHub Actions with act and pytest](local-validation-of-github-actions-with-act-and-pytest.md)
  explains how to validate workflow behaviour locally before relying on remote
  Continuous Integration (CI) runs.
- [Scripting standards](scripting-standards.md) explains the preferred Python
  scripting stack, command execution patterns, and test expectations for helper
  scripts.

## Execution plans

- [Exact Wenmode runtime dependency](execplans/1-2-1-wenmode-runtime-dependency.md)
  proposes roadmap 1.2.1 and its approval-gated verification work.
