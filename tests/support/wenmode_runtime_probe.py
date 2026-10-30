"""Exercise the installed Wenmode dependency with process and network denial."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- negative-control probe.
import sys
from importlib import metadata
from pathlib import Path

_JAVASCRIPT_RUNTIMES = ("bun", "node", "nodejs")
_CONTAINER_NETWORK_WITNESS = ("192.0.2.1", 443)


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


def main() -> None:
    """Check isolated import origins and the reviewed parser smoke documents."""
    mode = os.environ["WENMODE_INSTALL_MODE"]
    assert mode in {"wheel", "editable"}, 'Expected mode in {"wheel", "editable"}'
    verify_isolation()

    import wenmode
    from wenmode import Parser
    from wenmode.presets import github

    import syrupy_mdast

    prefix = Path(sys.prefix).resolve()
    assert metadata.version("wenmode") == "0.15.2", (
        'Expected metadata.version("wenmode") == "0.15.2"'
    )
    assert Path(wenmode.__file__).resolve().is_relative_to(prefix), (
        "Expected Path(wenmode.__file__).resolve().is_relative_to(prefix)"
    )
    project_path = Path(syrupy_mdast.__file__).resolve()
    expected_root = (
        prefix
        if mode == "wheel"
        else Path(os.environ["WENMODE_CHECKOUT_PATH"]).resolve()
    )
    assert project_path.is_relative_to(expected_root), (
        "Expected project_path.is_relative_to(expected_root)"
    )
    parser = Parser(github(), positions=False)
    empty, heading, tasks = [
        parser.parse(text).to_ast()
        for text in ("", "# Hello\n", "- [x] done\n- [ ] todo\n")
    ]
    assert empty == {"type": "root", "children": []}, (
        'Expected empty == {"type": "root", "children": []}'
    )
    assert heading["type"] == "root", 'Expected heading["type"] == "root"'
    assert heading["children"][0]["depth"] == 1, (
        'Expected heading["children"][0]["depth"] == 1'
    )
    assert heading["children"][0]["children"][0]["value"] == "Hello", (
        'Expected heading["children"][0]["children"][0]["value"] == "Hello"'
    )
    items = tasks["children"][0]["children"]
    assert [item["checked"] for item in items] == [True, False], (
        'Expected [item["checked"] for item in items] == [True, False]'
    )
    assert "position" not in repr((empty, heading, tasks)), (
        'Expected "position" not in repr((empty, heading, tasks))'
    )
    print(json.dumps([empty, heading, tasks], sort_keys=True, separators=(",", ":")))
    print(f"wenmode=0.15.2 mode={mode} isolation=passed")


if __name__ == "__main__":
    main()
