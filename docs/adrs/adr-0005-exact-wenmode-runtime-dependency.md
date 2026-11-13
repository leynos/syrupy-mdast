# Architectural decision record (ADR) 005: Exact Wenmode runtime dependency

## Status

Accepted (2026-10-29): require Wenmode 0.15.2 as the exact Python runtime
dependency and retain the reviewed upgrade workflow for later moves.

## Date

2026-10-29.

## Context and problem statement

The canonical Markdown contract corpus records Wenmode 0.15.2 as its evidence
baseline. The roadmap and technical design require syrupy-mdast to pin that
reviewed release and keep its installed package boundary Python-only. ADR-003
and ADR-004 were accepted on 2026-10-11 and record a maintainer-selected
`>=0.15.2,<0.16.0` requirement. That range permits repository resolution to a
release whose parser behaviour has not been checked against the corpus.

The implementation of roadmap item 1.2.1 needs one active dependency contract
that agrees with the reviewed baseline. This decision changes only the Wenmode
requirement and the corresponding downstream-resolution policy. It does not
change the parser profile, normalization rules, snapshot bytes, or contract
version recorded in ADR-004.

## Decision Drivers

- Keep editable and installed package use on one reviewed parser release.
- Make the runtime requirement agree with the evidence corpus and roadmap.
- Preserve deliberate review of any later parser release.
- Keep Python as the only runtime and introduce no version guard.

## Requirements

### Functional requirements

- Declare `wenmode==0.15.2` as the sole Wenmode runtime requirement.
- Record the selected release's BSD-3-Clause licence and reviewed wheel digest.
- Keep the package free of Bun, Node.js, and installed JavaScript assets.

### Technical requirements

- Preserve ADR-003's corpus comparison and changelog classification for every
  Wenmode release move after this initial adoption.
- Do not run the roadmap 3.2.1 upgrade report for the initial adoption of the
  already-reviewed 0.15.2 baseline. That report does not yet exist; this
  exception does not waive it for later release moves.
- Keep the Dependabot ignore and its contract check for Wenmode updates.
- Do not add runtime version enforcement or compatibility machinery.

## Options considered

### Option A: Retain the bounded range

Keep `>=0.15.2,<0.16.0` and rely on review of repository lockfile changes. This
allows an unreviewed 0.15.x release to become the resolved runtime and does not
make the manifest itself express the corpus baseline.

### Option B: Pin the reviewed release

Require `wenmode==0.15.2`. This aligns source metadata, the lockfile, the
package installation contract, and the corpus evidence. Later upgrades remain
possible through a reviewed dependency change and the existing upgrade workflow.

## Decision outcome / proposed direction

Adopt Option B. The project runtime requirement is exactly `wenmode==0.15.2`.
The reviewed 0.15.2 release is licensed under BSD-3-Clause; its `py3-none-any`
wheel SHA-256 is
`a1be9a2d91ef7f5020148daf615edca0c9a4a6d54d074a808e6d5e9de95726f6`. The
implementation must verify the downloaded wheel and installed metadata; this
ADR records the reviewed baseline, not a substitute for that test.

For this initial adoption only, no 3.2.1 upgrade report is required because the
selected version is the existing reviewed baseline and that report has not yet
been implemented. Every subsequent Wenmode requirement or repository-resolved
release move remains subject to ADR-003's dedicated upgrade report, corpus
comparison, and review of relevant changelog entries.

This ADR supersedes ADR-003 and ADR-004 only where they specify the bounded
Wenmode requirement or imply that downstream resolution may select another
release. Their other decisions and their historical records remain in force.

## Goals and non-goals

- Goals:
  - Align the runtime dependency with the reviewed corpus baseline.
  - Preserve review and evidence requirements for future release moves.
  - Keep runtime packaging and parsing Python-only.
- Non-goals:
  - Change the parser profile, normalization, or snapshot contract.
  - Add a runtime version guard or promise compatibility with other releases.
  - Claim that the package wheel or offline runtime tests have passed; those
    are implementation acceptance criteria for roadmap item 1.2.1.

## Known risks and limitations

An exact requirement can conflict with another dependency that requires a
different Wenmode release. A security fix that requires a new version must be
reviewed and released promptly under ADR-003's upgrade process. The recorded
wheel digest identifies the reviewed archive; implementation tests must still
verify the acquired artifact and its installed licence metadata.

## Architectural rationale

Parser output contributes to persisted snapshot content, so one release pin
makes the package's declared runtime contract match the release used to build
the evidence corpus. Python-only installation checks establish the distribution
boundary separately from the semantic parser corpus. Keeping the existing
upgrade process for later moves makes new parser evidence explicit without
changing the snapshot format or runtime architecture.
