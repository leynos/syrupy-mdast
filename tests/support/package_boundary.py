"""Pure classifiers for Python-only wheel asset contracts."""

from __future__ import annotations

import typing as typ
from pathlib import PurePosixPath

if typ.TYPE_CHECKING:
    import collections.abc as cabc

_FORBIDDEN_SUFFIXES = (
    ".js",
    ".mjs",
    ".cjs",
    ".jsx",
    ".ts",
    ".tsx",
    ".mts",
    ".cts",
)
_FORBIDDEN_NAMES = {
    "package.json",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "bun.lock",
    "bun.lockb",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun",
    "bun.exe",
    "node",
    "node.exe",
    "nodejs",
}


def is_javascript_asset(path: str) -> bool:
    """Return whether a wheel path names JavaScript tooling or source.

    Returns
    -------
    bool
        Whether the path identifies a forbidden JavaScript asset.

    Examples
    --------
    >>> is_javascript_asset("syrupy_mdast/parser.ts")
    True
    >>> is_javascript_asset("syrupy_mdast/fixtures/example.json")
    False
    """
    parts = tuple(part.lower() for part in PurePosixPath(path).parts)
    if "node_modules" in parts:
        return True

    name = parts[-1] if parts else ""
    return (
        name.endswith(_FORBIDDEN_SUFFIXES)
        or name in _FORBIDDEN_NAMES
        or (name.startswith("tsconfig") and name.endswith(".json"))
    )


def find_javascript_assets(paths: cabc.Iterable[str]) -> list[str]:
    """Return every forbidden asset path in input order.

    Returns
    -------
    list[str]
        Forbidden asset paths in their original input order.

    Examples
    --------
    >>> find_javascript_assets(["pkg/module.py", "pkg/node_modules/dep/index.js"])
    ['pkg/node_modules/dep/index.js']
    """
    return [path for path in paths if is_javascript_asset(path)]
