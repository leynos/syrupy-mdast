"""Architecture contract for the dependency-free domain core."""

from __future__ import annotations

import ast

from tests.support.make_contract import REPO_ROOT

_ALLOWED_ABSOLUTE_IMPORTS = frozenset({
    "__future__",
    "typing",
    "collections.abc",
    "dataclasses",
    "enum",
})


def _is_allowed_from_import(node: ast.ImportFrom) -> bool:
    """Return whether a from-import stays within the core's boundary."""
    return node.level == 1 or node.module in _ALLOWED_ABSOLUTE_IMPORTS


def _disallowed_imports(source: str) -> list[str]:
    """Return imports that would leak an adapter dependency into the core."""
    violations: list[str] = []
    for node in ast.walk(ast.parse(source)):
        match node:
            case ast.Import(names=names):
                violations.extend(
                    name.name
                    for name in names
                    if name.name not in _ALLOWED_ABSOLUTE_IMPORTS
                )
            case ast.ImportFrom() if not _is_allowed_from_import(node):
                violations.append(node.module or "relative import")
    return violations


def test_core_imports_only_allowlisted_modules() -> None:
    """Core modules remain independent of Syrupy, Wenmode, and I/O adapters."""
    core_directory = REPO_ROOT / "syrupy_mdast" / "_core"
    core_modules = sorted(core_directory.rglob("*.py"))
    assert core_modules, "the import guard must scan at least one core module"
    violations = {
        module.relative_to(REPO_ROOT): _disallowed_imports(
            module.read_text(encoding="utf-8")
        )
        for module in core_modules
    }
    assert not any(violations.values()), (
        f"core import boundary violations: {violations}"
    )


def test_import_guard_rejects_syrupy_import() -> None:
    """The guard detects the adapter dependency it is designed to exclude."""
    assert _disallowed_imports("import syrupy") == ["syrupy"], (
        "the guard must reject a direct Syrupy import"
    )
