# syrupy-mdast

AST-aware Markdown snapshot support for [Syrupy](https://github.com/syrupy-project/syrupy).

The current pre-alpha public contract exports `MarkdownAstError` and
`MarkdownAstSnapshotExtension`. It supports Python 3.12 or later and Syrupy
5.x or 6.x. Parsing and canonical JSON serialisation arrive in roadmap task
2.3.1; until then, the extension validates its input and raises
`NotImplementedError` for valid Markdown source.

The package uses Python dependencies only. It does not require Bun, Node.js,
TypeScript, JavaScript packages, or JavaScript build assets.
