"""Tests for forbidden JavaScript assets at the package boundary."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

import pytest
from hypothesis import event, given
from hypothesis import strategies as st

from tests.support.package_boundary import find_javascript_assets, is_javascript_asset

_FORBIDDEN_SUFFIXES = (".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".mts", ".cts")
_FORBIDDEN_NAMES = (
    "package.json",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "bun.lock",
    "bun.lockb",
    "pnpm-lock.yaml",
    "yarn.lock",
    "tsconfig.json",
    "tsconfig.build.json",
    "tsconfig.base.json",
    "tsconfig.test.json",
    "bun",
    "bun.exe",
    "node",
    "node.exe",
    "nodejs",
)
_SAFE_PATHS = (
    "package/module.py",
    "package/py.typed",
    "package/LICENSE",
    "package/fixtures/example.json",
    "package/uv.lock",
    "package/syrupy_mdast-0.1.0.dist-info/METADATA",
)


@pytest.mark.parametrize("suffix", _FORBIDDEN_SUFFIXES)
def test_source_extension_is_forbidden_at_root_and_when_nested(suffix: str) -> None:
    """Source suffixes are rejected regardless of archive nesting."""
    assert is_javascript_asset(f"module{suffix}"), (
        f"root asset suffix {suffix} was permitted"
    )
    assert is_javascript_asset(f"package/vendor/module{suffix}"), (
        f"nested asset suffix {suffix} was permitted"
    )


@pytest.mark.parametrize("name", _FORBIDDEN_NAMES)
def test_manifest_lockfile_or_runtime_name_is_forbidden(name: str) -> None:
    """Known manifests, locks, compiler settings and runtimes are rejected."""
    assert is_javascript_asset(f"package/vendor/{name}"), (
        f"forbidden package asset {name} was permitted"
    )


@pytest.mark.parametrize("path", _SAFE_PATHS)
def test_python_metadata_licence_and_json_data_are_safe(path: str) -> None:
    """Ordinary Python package files and metadata stay permitted."""
    assert not is_javascript_asset(path), (
        f"safe Python package path {path} was rejected"
    )


def test_node_modules_component_is_forbidden_at_any_depth() -> None:
    """A nested dependency tree is rejected even without a source suffix."""
    assert is_javascript_asset("node_modules/dep/README"), (
        "a root node_modules path component was permitted"
    )
    assert is_javascript_asset("package/vendor/node_modules/dep/package.json"), (
        "a nested node_modules path component was permitted"
    )


def _forbidden_member_strategy() -> st.SearchStrategy[tuple[str, str]]:
    """Return forbidden members drawn from every supported asset family."""
    source = st.sampled_from(_FORBIDDEN_SUFFIXES).map(
        lambda suffix: ("source suffix", f"payload{suffix}")
    )
    named = st.sampled_from(_FORBIDDEN_NAMES).map(
        lambda name: ("manifest, lockfile or runtime", name)
    )
    tsconfig = st.from_regex(r"tsconfig(\.[a-z0-9_-]+)?\.json", fullmatch=True).map(
        lambda name: ("TypeScript settings", name)
    )
    node_modules = st.just(("dependency tree", "node_modules/dependency/README"))
    return st.one_of(source, named, tsconfig, node_modules)


@given(
    prefix=st.lists(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-", min_size=1),
        min_size=0,
        max_size=6,
    ),
    forbidden=_forbidden_member_strategy(),
)
def test_forbidden_member_is_found_at_constructed_archive_path(
    prefix: list[str], forbidden: tuple[str, str]
) -> None:
    """A forbidden member remains detectable at any generated path depth."""
    family, member = forbidden
    path = str(PurePosixPath(*prefix, *PurePosixPath(member).parts))
    event(f"forbidden family: {family}")
    event("forbidden path at root" if not prefix else "forbidden path nested")
    assert is_javascript_asset(path), (
        f"generated forbidden asset path {path} was permitted"
    )


@given(
    safe_members=st.lists(
        st.sampled_from(_SAFE_PATHS), min_size=0, max_size=8, unique=True
    ),
    forbidden=_forbidden_member_strategy(),
)
def test_archive_member_position_cannot_hide_forbidden_member(
    safe_members: list[str], forbidden: tuple[str, str]
) -> None:
    """A forbidden wheel entry is found at every generated archive position."""
    family, member = forbidden
    nested_member = str(
        PurePosixPath("package", "nested", *PurePosixPath(member).parts)
    )
    event(f"forbidden family: {family}")
    event("archive with safe entries" if safe_members else "single-entry archive")
    for position in range(len(safe_members) + 1):
        members = [
            *safe_members[:position],
            nested_member,
            *safe_members[position:],
        ]
        findings = find_javascript_assets(members)
        assert findings == [nested_member], (
            f"forbidden wheel member at archive position {position} was missed"
        )


@given(path=st.sampled_from(_SAFE_PATHS))
def test_generated_safe_member_stays_permitted(path: str) -> None:
    """Constructed safe archive entries produce no forbidden findings."""
    event("safe package path")
    assert find_javascript_assets([path]) == [], (
        f"safe package path {path} was rejected"
    )


def test_nested_node_modules_in_synthetic_wheel_is_rejected(tmp_path: Path) -> None:
    """Inspect an archive whose nested package tree contains no source suffix."""
    from zipfile import ZipFile

    wheel = tmp_path / "synthetic.whl"
    with ZipFile(wheel, "w") as archive:
        archive.writestr("example/vendor/node_modules/dep/README", "asset")
    with ZipFile(wheel) as archive:
        findings = find_javascript_assets(archive.namelist())
        assert findings == ["example/vendor/node_modules/dep/README"], (
            "the archive inspector missed the nested node_modules asset"
        )
