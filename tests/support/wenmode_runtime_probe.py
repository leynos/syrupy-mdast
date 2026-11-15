"""Exercise the installed adapter seam with process and network denial."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- negative-control probe.
import sys
import typing as typ
from importlib import metadata
from pathlib import Path

if typ.TYPE_CHECKING:
    import collections.abc as cabc

_JAVASCRIPT_RUNTIMES = ("bun", "node", "nodejs")
_CONTAINER_NETWORK_WITNESS = ("192.0.2.1", 443)
_DEFINITION_DOCUMENT = (
    "See [key] and a footnote[^note].\n"
    "\n"
    "[key]: https://example.com/first\n"
    "[^note]: First footnote text.\n"
)
_UNRESOLVED_DOCUMENT = "See [key] and a footnote[^note].\n"
_UNRESOLVED_TEXT = "See [key] and a footnote[^note]."


class IsolationDeniedError(RuntimeError):
    """Signal that an isolation audit event was denied."""


def deny_external_activity(event: str, _args: tuple[object, ...]) -> None:
    """Deny socket and process events before they can perform side effects."""
    if event.startswith(("socket.", "subprocess.")) or event in {
        "os.system",
        "os.fork",
        "os.forkpty",
        "os.posix_spawn",
        "os.spawn",
        "os.exec",
    }:
        raise IsolationDeniedError(event)


def verify_isolation() -> None:
    """Check network and process controls before importing the parser."""
    _assert_no_javascript_runtimes()
    if os.environ.get("WENMODE_CONTAINER_ACCEPTANCE") == "1":
        _assert_container_network_denied()
    sys.addaudithook(deny_external_activity)
    _assert_socket_denied()
    _assert_process_denied()


def _assert_no_javascript_runtimes() -> None:
    """Require Bun and Node to be absent from the restricted PATH."""
    assert all(shutil.which(binary) is None for binary in _JAVASCRIPT_RUNTIMES), (
        "Expected all(shutil.which(binary) is None for binary in binaries)"
    )


def _assert_container_network_denied() -> None:
    """Require the container to have no JavaScript runtime or network route."""
    original_path = os.environ["WENMODE_ORIGINAL_PATH"]
    assert all(
        shutil.which(binary, path=original_path) is None
        for binary in _JAVASCRIPT_RUNTIMES
    ), "Original image PATH must contain no JavaScript runtime"
    try:
        socket.create_connection(_CONTAINER_NETWORK_WITNESS, timeout=1)
    except OSError:
        return
    message = "container network control unexpectedly connected"
    raise AssertionError(message)


def _assert_socket_denied() -> None:
    """Require the audit hook to deny socket creation before a side effect."""
    try:
        socket.socket()
    except IsolationDeniedError:
        return
    message = "socket audit control did not deny the operation"
    raise AssertionError(message)


def _assert_process_denied() -> None:
    """Require the audit hook to deny child-process creation."""
    try:
        subprocess.run([sys.executable, "-c", "pass"], check=True)
    except IsolationDeniedError:
        return
    message = "process audit control did not deny the operation"
    raise AssertionError(message)


def _children(node: dict[str, object]) -> list[dict[str, object]]:
    """Return a container node's child mappings, rejecting a malformed tree.

    The adapter returns ``dict[str, object]``, so nested values need narrowing
    before they can be indexed. Wenmode omits ``children`` on leaf nodes, which
    is why this helper is only used on nodes known to be containers.

    Parameters
    ----------
    node
        Container node whose children are required.

    Returns
    -------
    list[dict[str, object]]
        Mapping children in document order.
    """
    children = node.get("children")
    assert isinstance(children, list), "Expected a list-valued children field"
    return [child for child in children if isinstance(child, dict)]


def _node_types(node: dict[str, object]) -> cabc.Iterator[str]:
    """Yield every node type in a Wenmode tree in document order.

    Unlike `_children`, this walks leaves too, so a missing ``children`` field
    ends that branch instead of failing.

    Parameters
    ----------
    node
        Mapping node to start from, normally the document root.

    Yields
    ------
    str
        The ``type`` of each node, including nested children.
    """
    yield str(node["type"])
    nested = node.get("children")
    if isinstance(nested, list):
        for child in nested:
            if isinstance(child, dict):
                yield from _node_types(child)


def _installation_mode() -> str:
    """Return the validated installation mode requested by the harness."""
    mode = os.environ["WENMODE_INSTALL_MODE"]
    assert mode in {"wheel", "editable"}, 'Expected mode in {"wheel", "editable"}'
    return mode


def _assert_installed_identity(
    mode: str, package_file: str | None, adapter_file: str | None
) -> None:
    """Require Wenmode, the package, and the adapter to come from this install."""
    import wenmode

    prefix = Path(sys.prefix).resolve()
    expected_root = (
        prefix
        if mode == "wheel"
        else Path(os.environ["WENMODE_CHECKOUT_PATH"]).resolve()
    )
    assert metadata.version("wenmode") == "0.15.2", (
        'Expected metadata.version("wenmode") == "0.15.2"'
    )
    assert wenmode.__file__ is not None, "Expected Wenmode to record its module file"
    assert package_file is not None, "Expected the package to record its module file"
    assert adapter_file is not None, "Expected the adapter to record its module file"
    assert Path(wenmode.__file__).resolve().is_relative_to(prefix), (
        "Expected Wenmode to be imported from the installed environment"
    )
    assert Path(package_file).resolve().is_relative_to(expected_root), (
        "Expected the package to be imported from the installed project"
    )
    assert Path(adapter_file).resolve().is_relative_to(expected_root), (
        "Expected the adapter to come from the same installed project"
    )


def _parse_smoke_documents(
    parse_markdown: cabc.Callable[[str], dict[str, object]],
) -> list[dict[str, object]]:
    """Parse the smoke documents, defining labels only after using them.

    Parameters
    ----------
    parse_markdown
        The installed adapter callable under test.

    Returns
    -------
    list[dict[str, object]]
        One root tree per smoke document, in the order parsed.
    """
    return [
        parse_markdown(""),
        parse_markdown("# Hello\n"),
        parse_markdown("- [x] done\n- [ ] todo\n"),
        parse_markdown(_DEFINITION_DOCUMENT),
        parse_markdown(_UNRESOLVED_DOCUMENT),
    ]


def _assert_smoke_semantics(trees: list[dict[str, object]]) -> None:
    """Require each smoke document's expected structure and label scope."""
    empty, heading, tasks, defined, unresolved = trees
    assert empty == {"type": "root", "children": []}, (
        'Expected empty == {"type": "root", "children": []}'
    )
    assert heading["type"] == "root", 'Expected heading["type"] == "root"'
    assert _children(heading)[0]["depth"] == 1, (
        "Expected the heading document to produce a depth-one heading"
    )
    assert _children(_children(heading)[0])[0]["value"] == "Hello", (
        "Expected the heading document to carry its text"
    )
    checked = [item["checked"] for item in _children(_children(tasks)[0])]
    assert checked == [True, False], (
        "Expected the task list to preserve both checked states"
    )
    assert "position" not in repr(trees), (
        "Expected no position data in any tree the adapter returns"
    )
    defined_types = set(_node_types(defined))
    unresolved_types = set(_node_types(unresolved))
    assert {"link", "footnoteDefinition"} <= defined_types, (
        "Expected the adapter to resolve its own reference and footnote"
    )
    assert "link" not in unresolved_types, (
        "Expected an undefined reference to stay unresolved"
    )
    assert "footnoteDefinition" not in unresolved_types, (
        "Expected an undefined footnote to stay unresolved"
    )
    assert _children(_children(unresolved)[0]) == [
        {"type": "text", "value": _UNRESOLVED_TEXT}
    ], "Expected the later document to remain literal text"


def _report(mode: str, trees: list[dict[str, object]]) -> None:
    """Print the parsed trees and one machine-readable success line."""
    print(json.dumps(trees, sort_keys=True, separators=(",", ":")))
    print(f"wenmode=0.15.2 mode={mode} isolation=passed")


def main() -> None:
    """Check isolated import origins and the installed adapter smoke documents."""
    mode = _installation_mode()
    verify_isolation()

    import syrupy_mdast
    import syrupy_mdast._wenmode as wenmode_adapter

    _assert_installed_identity(mode, syrupy_mdast.__file__, wenmode_adapter.__file__)
    trees = _parse_smoke_documents(wenmode_adapter.parse_markdown)
    _assert_smoke_semantics(trees)
    _report(mode, trees)


if __name__ == "__main__":
    main()
