# Migration guide for 0.2.x

This guide covers the pre-1.0 migration from the generated 0.1.x package stub
to the v1 public contract planned for the 0.2.x minor release.

## Public API

The generated `syrupy_mdast.hello()` function is removed. Consumers should
import the two supported package-level exports:

```python
from syrupy_mdast import MarkdownAstError, MarkdownAstSnapshotExtension
```

`MarkdownAstError` is the package error type. Its `category` is a required
keyword-only value from the documented failure taxonomy.

## Runtime requirements

The package now requires Python 3.12 or later and declares Syrupy
`>=5.0.0,<7.0.0`. Update environments and dependency constraints before
installing the 0.2.x release.

Register the extension through Syrupy's existing assertion configuration:

```python
from syrupy_mdast import MarkdownAstSnapshotExtension

def test_markdown_snapshot(snapshot):
    assertion = snapshot.with_defaults(
        extension_class=MarkdownAstSnapshotExtension,
    )
    value = "# heading"
    assert assertion == value
```

The extension is configured for text snapshots using the `mdast.json` suffix
once Markdown serialization is implemented. At the 0.2.x migration seam, valid
Markdown `str` input still raises `NotImplementedError` because that
serialization milestone is not yet delivered.

## Input and control changes

The extension accepts Markdown source only as `str`. Non-string input raises
`TypeError`. Syrupy's `exclude`, `include`, and `matcher` controls are not part
of this contract; supplying any of them raises `ValueError` before the
serialization seam is reached.
