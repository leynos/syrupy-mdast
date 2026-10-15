# Canonical Markdown contract corpus

This corpus records source examples and independently authored expected
canonical JSON for the comparison rules in ADR-004. It is test data; it does
not run Wenmode, canonicalize trees, or implement snapshot serialization.

Markdown sources use the `.txt` suffix so their bytes remain visible and are
not rewritten by tools that treat `.md` as prose. Synthetic AST inputs use
`.json`; expected payloads are hand-authored `.json` files. The TOML manifest
names each case, its governing rule, and its relation to other cases.

## Representative cases

This table highlights four fixture families. The complete case-to-rule map is in
[`assertions/contract-assertions.json`](assertions/contract-assertions.json).

| Case IDs                                                  | Rule  | Contract                                                                    |
| --------------------------------------------------------- | ----- | --------------------------------------------------------------------------- |
| `emphasis-asterisk`, `emphasis-underscore`                | NF-1  | Delimiter spelling preserves the same emphasis node.                        |
| `strong-asterisk`, `strong-underscore`                    | NF-1  | Delimiter spelling preserves the same strong node.                          |
| `break-soft`, `break-hard-spaces`, `break-hard-backslash` | NF-10 | A soft line break remains distinct from the two equal hard-break spellings. |
| `line-endings-lf`, `line-endings-crlf`, `line-endings-cr` | NF-8  | LF, CRLF, and CR source bytes map to one expected paragraph.                |

The manifest's `line_endings` field classifies source bytes. The corpus does
not infer this declaration from a decoded string: `lf` contains LF and no CR,
`crlf` contains only paired CR and LF bytes, `cr` contains CR and no LF, and
`none` contains neither. In this table, visible `LF`, `CRLF`, and `CR` names
refer to the actual byte sequences `0A`, `0D 0A`, and `0D` respectively.

## Layout

- `manifest.toml` stores ordered case and relation records.
- `assertions/contract-assertions.json` records the exact case-to-rule map,
  relation groups, node types, preferred JSON member order, and semantic
  markers used by independent test checks.
- `sources/` stores raw UTF-8 Markdown bytes with declared line endings.
- `synthetic/` stores root-shaped input trees for rules Markdown cannot expose.
- `expected/` stores complete expected canonical JSON payloads.

The five transformation rule IDs and the accepted `NF-1` through `NF-13`
vocabulary are defined by the test support module and ADR-004. Expected files
and their assertions are reviewed as data; tests check their formatting and
relationships without regenerating them from a parser or canonicalizer.
