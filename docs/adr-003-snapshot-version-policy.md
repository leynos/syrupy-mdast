# Architectural decision record (ADR) 003: Snapshot-version policy

## Status

Accepted (2026-10-11): retain unmarked `.mdast.json` payloads and use the
recorded contract/package release and Wenmode upgrade policy.

[Maintainer acceptance](https://github.com/leynos/syrupy-mdast/pull/58#issuecomment-6113067258).

## Date

2026-10-11.

## Context and problem statement

`Syrupy-mdast` stores a canonical Markdown syntax tree as a `.mdast.json`
snapshot. The policy for communicating snapshot versions and releasing changes
must avoid broad, uninformative rewrites while giving maintainers a clear
migration path when payloads change. The
[normalization contract in ADR-004](adr-004-parser-profile-and-normalization.md)
defines the parser, canonical payload bytes, and the integer contract version
to which this policy applies.

The technical design requires an explicit record of snapshot-version and
dependency-upgrade policy before implementation or fixture changes. Wenmode is
beta software, and its AST can determine persisted snapshot bytes. The
maintainer selected `>=0.15.2,<0.16.0`; 0.15.2 is the evidence baseline, not a
claim that every later release in the range has identical output.

## Decision Drivers

- Keep snapshot diffs focused on changes to canonical Markdown structure.
- Give payload changes a visible and reviewable migration path.
- Make Wenmode changes deliberate because parser output contributes to
  persisted snapshot bytes.
- Preserve reproducibility guidance without imposing a runtime version check
  or freezing downstream dependency resolution.
- Keep the payload itself limited to the canonical tree defined in ADR-004.

## Requirements

### Functional requirements

- Keep snapshot-version metadata outside the `.mdast.json` payload and file
  suffix.
- Use ordinary Syrupy diffs to show changed snapshots and release notes to
  explain why they changed.
- Distinguish a package release version from the integer contract version.
- Evaluate dependency moves before they change repository snapshots.

### Technical requirements

- Use the bounded Wenmode requirement selected by the maintainer,
  `>=0.15.2,<0.16.0`.
- Require a dedicated upgrade report for each Wenmode requirement or
  repository-resolved release move.
- Prevent automatic repository dependency updates from bypassing that review.
- Recommend consumer lockfiles for reproducibility while acknowledging that
  the requirement does not freeze downstream resolution.

## Options considered

The version marker and suffix alternatives below were considered for snapshot
contract metadata. The separate choice to merge exact-shape adjacent text nodes
is defined in ADR-004.

### Option A: No version marker

Keep the payload as the canonical tree alone and retain the `.mdast.json`
suffix. Ordinary Syrupy diffs show affected snapshots; release notes explain
the migration, and the users' guide maps package releases to contract versions.
This avoids changing every snapshot at a contract-version increment. The
maintainer selected this direction and accepted this written record on
2026-10-11.

### Option B: In-payload version member

Add a contract-version member to every serialized tree. This makes the version
visible in each file, but changes every snapshot at every version increment
even when the tree itself is unchanged. It also adds a member that is not part
of Wenmode's canonical tree.

### Option C: Versioned file suffix

Change the extension to include the contract version. This keeps version
metadata outside the JSON tree, but changes every snapshot path at each version
increment and risks leaving old snapshots that Syrupy reports as unused.

### Option D: Header with taint

Add a serializer-version header that marks snapshots with an unfamiliar version
as tainted. Syrupy's amber serializer uses this model, but a tainted snapshot
fails comparison even when its content is identical. It would force broad
updates and does not match the current single-file extension's comparison
behaviour.

### Option E: Informational header ignored by comparison

Add a version header that does not affect comparison, as in tools that treat
metadata as informational. This avoids taint but still adds parser and writer
policy outside the canonical tree, and a future metadata change would need
separate comparison semantics.

| Factor                                  | Option A | Option B | Option C            | Option D       | Option E                   |
| --------------------------------------- | -------- | -------- | ------------------- | -------------- | -------------------------- |
| Payload remains the canonical tree      | Yes      | No       | Yes                 | No             | No                         |
| Changes all snapshots on a version bump | No       | Yes      | Paths change        | Yes            | Header changes             |
| Compatible with ordinary Syrupy diffs   | Yes      | Yes      | Risk of stale paths | No             | Requires custom comparison |
| Adds comparison or storage machinery    | No       | No       | No                  | Taint handling | Header handling            |

_Table 1: Payload versioning options._

## Decision outcome / proposed direction

Adopt Option A: snapshots contain no contract-version marker and retain the
`.mdast.json` suffix. The users' guide maps syrupy-mdast package versions to
snapshot contract versions. Payload changes appear as ordinary Syrupy diffs of
affected snapshots, and release notes explain the affected constructs and the
review-then-`pytest --snapshot-update` step. Adding a marker later is itself a
payload change.

### Normalization contract

[ADR-004](adr-004-parser-profile-and-normalization.md) is the authoritative
record for the parser profile, normalization rules, member order, JSON writer,
and comparison key. This ADR owns the versioning and release policy; it does
not duplicate ADR-004's manifest.

### Contract and package versions

The snapshot contract version is an integer beginning at `1`, recorded in
ADR-004's machine-readable manifest. It is a migration signal, not the
equivalence key. ADR-004 defines the package-version, parser-version, profile,
and interpreter conditions for payload equivalence. The bounded Wenmode
requirement permits several parser versions and therefore does not prove equal
output across all allowed installations.

Version policy follows any known change to a snapshot payload, whether caused
by a contract change, a canonicalizer conformance fix, or a non-neutral parser
move:

1. Deliberate syrupy-mdast patch-release changes, evaluated with the same
   installed parser, never knowingly change a payload. A downstream parser
   update within the approved range may change payloads without a syrupy-mdast
   release; this policy cannot freeze unlocked consumer installations.
2. A knowingly adopted payload change requires a minor package release before
   1.0.0 (`0.y.z` to `0.(y+1).0`) and a major release from 1.0.0 onward.
   Release notes list the affected constructs and the review-then-
   `pytest --snapshot-update` step.
3. Increment the contract version when its payload definition changes,
   including the parser profile, normalization rules, key order, or writer.
   Changes that do not alter the definition do not increment it.

Before the first release whose `serialize()` writes payloads, a correction to
the v1 definition may be made in ADR-004 with a dated amendment. After that
release, a payload-definition change requires a new normalization ADR and
supersedes ADR-004. It does not by itself supersede this snapshot-version
policy. Changes to versioning policy that do not alter payload bytes may be
recorded as dated amendments here; after the first payload release, `## Date`
means the last update date.

### Wenmode upgrade workflow

Every change to the Wenmode requirement or repository-resolved release must
land in a dedicated pull request with the roadmap 3.2.1 upgrade report. The
report compares the corpus and classifies every intervening Wenmode changelog
entry as an addition, parser fix, intentional migration, or regression. Each
entry that can affect GitHub-profile `to_ast()` output receives a fixture. A
move is payload-neutral only when the corpus diff is empty and every relevant
entry has a fixture with no change. The move is blocked if the v1 parser
construction emits any warning under `-W error`.

Roadmap 1.2.1 will add a `wenmode` ignore to the repository's Dependabot pip
block and a contract check. Evaluation is triggered by a new Wenmode release,
Wenmode 1.0, a Wenmode security advisory, or a newly supported Python minor
version. A security fix ships promptly under the applicable version rule, and
the advisory is named in the release notes. ADR-004 records the evidence
baseline, wheel archive hash, probe output, and limits of the empirical result.

Consumers should lock their test dependencies when they need to reproduce
parser output. The planned repository Dependabot ignore will protect its
reviewed updates; it does not freeze downstream resolution. A downstream lock
refresh may change payload bytes without a syrupy-mdast release and produce
ordinary Syrupy diffs. The bounded requirement may conflict with another
downstream Wenmode constraint, and a security fix outside the range requires a
syrupy-mdast release. Installing syrupy-mdast in a test-only dependency group
limits conflicts. No runtime version-enforcement mechanism or extra dependency
is introduced.

## Goals and non-goals

- Goals:
  - Make payload migrations visible and reviewable.
  - Keep release notes and contract-version references aligned with ADR-004.
  - Require explicit review of repository Wenmode updates.
- Non-goals:
  - Add a version marker to payloads or filenames.
  - Guarantee equal payloads across all versions allowed by the Wenmode range.
  - Freeze downstream dependency resolution or enforce parser versions at
    runtime.
  - Replace Syrupy's snapshot diff and update lifecycle.

## Migration plan

1. Accept this versioning record and the normalization record in ADR-004 before
   implementation or fixture changes.
2. Implement the normative corpus and parser, canonicalizer, writer, and
   dependency checks in the roadmap tasks identified by ADR-004.
3. For each later Wenmode requirement or repository-resolved release move,
   prepare the dedicated 3.2.1 upgrade report and review its corpus and
   changelog classifications before merging.
4. For an adopted payload change, update affected snapshots through the
   documented review-then-`pytest --snapshot-update` process and release under
   the package-version rule above.

## Known risks and limitations

- Wenmode is beta software and may change AST output outside the finite probe
  or committed corpus. ADR-004 records the parser's observed behaviour; the
  upgrade report and dedicated review reduce but do not eliminate this risk.
- An unlocked consumer may resolve a later allowed parser patch without a
  syrupy-mdast release and see snapshot diffs. Consumer locks improve
  reproducibility, while the planned Dependabot ignore will affect only the
  repository itself.
- An upstream security fix outside the bounded requirement requires a package
  release. Other Wenmode constraints in a consumer's environment may conflict
  with the selected range.
- A parser move may emit warnings that downstream suites treat as errors. The
  upgrade workflow blocks moves that warn under `-W error`.
- Parser-specific divergences and output limits are defined with the parser
  fixtures in ADR-004; a future upstream correction may be a payload change.

## Outstanding decisions

None. The maintainer selected Option A on 2026-10-11. The bounded Wenmode
requirement was directed on 2026-10-10. The maintainer accepted this written
record on 2026-10-11.
