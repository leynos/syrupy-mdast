"""Build and exercise isolated Wenmode installations for package contracts."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- used only for fixed argv vectors.
import sys
import typing as typ
from pathlib import Path
from zipfile import ZipFile

import pytest

from tests.support.package_boundary import find_javascript_assets

if typ.TYPE_CHECKING:
    import collections.abc as cabc
_EXPECTED_WENMODE_SHA256 = (
    "a1be9a2d91ef7f5020148daf615edca0c9a4a6d54d074a808e6d5e9de95726f6"
)
_WHEELHOUSE_REQUIREMENTS = (
    "wenmode==0.15.2",
    "syrupy>=5.0.0,<7.0.0",
    "hatchling",
    "editables",
)


@dataclasses.dataclass(frozen=True, slots=True)
class Wheelhouse:
    """Paths and inspected release evidence for one immutable local wheelhouse."""

    path: Path
    project_wheel: Path
    wenmode_wheel: Path
    repository: Path
    project_sha256: str
    wenmode_sha256: str


def prepare_wheelhouse(temporary_path: Path) -> Wheelhouse:
    """Build the project wheel and prepare all runtime/build wheels locally."""
    repository = Path(__file__).parents[2].resolve()
    output = temporary_path / "wheelhouse"
    output.mkdir()
    project_wheel = _build_project_wheel(repository, temporary_path, output)
    _download_runtime_wheels(output, temporary_path)
    wenmode_wheels = tuple(output.glob("wenmode-0.15.2-*.whl"))
    assert len(wenmode_wheels) == 1, (
        f"expected one Wenmode wheel, found {wenmode_wheels!r}"
    )
    wenmode_wheel = wenmode_wheels[0]
    wenmode_digest = _assert_wenmode_wheel(wenmode_wheel)
    _assert_project_wheel(project_wheel)
    _assert_python_only_wheels((project_wheel, wenmode_wheel))
    return Wheelhouse(
        output,
        project_wheel,
        wenmode_wheel,
        repository,
        hashlib.sha256(project_wheel.read_bytes()).hexdigest(),
        wenmode_digest,
    )


def _build_project_wheel(repository: Path, temporary_path: Path, output: Path) -> Path:
    """Build and copy exactly one project wheel into the prepared wheelhouse."""
    project_output = temporary_path / "project-wheel"
    project_output.mkdir()
    _run(
        [_require_tool("uv"), "build", "--wheel", "--out-dir", str(project_output)],
        cwd=repository,
    )
    project_wheels = tuple(project_output.glob("*.whl"))
    assert len(project_wheels) == 1, (
        f"expected one project wheel, found {project_wheels!r}"
    )
    project_wheel = output / project_wheels[0].name
    project_wheel.write_bytes(project_wheels[0].read_bytes())
    return project_wheel


def _download_runtime_wheels(output: Path, temporary_path: Path) -> None:
    """Download runtime and editable build requirements into the wheelhouse."""
    _run(
        [
            _require_tool("uvx"),
            "--from",
            "pip",
            "pip",
            "download",
            "--only-binary=:all:",
            "--dest",
            str(output),
            *_WHEELHOUSE_REQUIREMENTS,
        ],
        cwd=temporary_path,
    )


def _assert_wenmode_wheel(wheel_path: Path) -> str:
    """Validate the reviewed Wenmode digest, licence and dependency metadata."""
    digest = hashlib.sha256(wheel_path.read_bytes()).hexdigest()
    assert digest == _EXPECTED_WENMODE_SHA256, f"Wenmode wheel digest changed: {digest}"
    release_metadata = _wheel_metadata(wheel_path)
    assert "License-Expression: BSD-3-Clause" in release_metadata, (
        "Wenmode wheel metadata must record the BSD-3-Clause licence"
    )
    dependencies = [
        line
        for line in release_metadata.splitlines()
        if line.startswith("Requires-Dist:")
    ]
    assert not dependencies, f"Wenmode gained runtime dependencies: {dependencies!r}"
    return digest


def _assert_project_wheel(wheel_path: Path) -> None:
    """Validate the built project wheel licence and exact dependency metadata."""
    project_metadata = _wheel_metadata(wheel_path)
    assert "License: ISC" in project_metadata, (
        "the built project wheel must retain its ISC licence"
    )
    requirements = {
        line.removeprefix("Requires-Dist: ")
        for line in project_metadata.splitlines()
        if line.startswith("Requires-Dist: ")
    }
    assert requirements == {"syrupy<7.0.0,>=5.0.0", "wenmode==0.15.2"}, (
        f"project wheel has unexpected runtime requirements: {requirements!r}"
    )


def _assert_python_only_wheels(wheels: tuple[Path, ...]) -> None:
    """Reject cross-runtime files from the project and Wenmode archives."""
    for wheel_path in wheels:
        with ZipFile(wheel_path) as archive:
            unexpected = find_javascript_assets(archive.namelist())
        assert not unexpected, (
            f"{wheel_path.name} contains JavaScript assets: {unexpected!r}"
        )


def install_and_probe(
    wheelhouse: Wheelhouse, mode: str, environment_path: Path
) -> tuple[str, str]:
    """Install one fresh mode offline and return probe output and stderr."""
    assert mode in {"wheel", "editable"}, f"unsupported installation mode: {mode}"
    uv = _require_tool("uv")
    _run(
        [uv, "venv", "--python", sys.executable, environment_path],
        cwd=environment_path.parent,
    )
    python = _environment_python(environment_path)
    uv_cache = environment_path / "uv-cache"
    uv_cache.mkdir()
    install_arguments = [
        uv,
        "pip",
        "install",
        "--offline",
        "--no-index",
        "--no-cache",
        "--find-links",
        str(wheelhouse.path),
        "--python",
        str(python),
    ]
    if mode == "editable":
        install_arguments.extend(("--editable", str(wheelhouse.repository)))
    else:
        install_arguments.append(str(wheelhouse.project_wheel))
    _run(
        install_arguments,
        cwd=environment_path,
        env={**_clean_dependency_environment(), "UV_CACHE_DIR": str(uv_cache)},
    )
    inventory = _run(
        [python, "-I", "-c", _runtime_inventory_probe()],
        cwd=environment_path,
        timeout=30,
    )
    installed_metadata = json.loads(inventory.stdout)
    _assert_installed_metadata(installed_metadata)
    for distribution_name, details in installed_metadata.items():
        unexpected_assets = find_javascript_assets(details["files"])
        assert not unexpected_assets, (
            f"installed {distribution_name} contains JavaScript assets: "
            f"{unexpected_assets!r}"
        )
    probe_env = {
        "PATH": str(python.parent),
        "WENMODE_INSTALL_MODE": mode,
        "WENMODE_CHECKOUT_PATH": str(wheelhouse.repository),
        "HOME": str(environment_path),
    }
    probe_path = Path(__file__).with_name("wenmode_runtime_probe.py").resolve()
    probe = _run(
        [python, "-I", "-W", "error", probe_path],
        cwd=environment_path.parent,
        env=probe_env,
        timeout=30,
    )
    return probe.stdout.strip(), probe.stderr


def _runtime_inventory_probe() -> str:
    """Return a child program checking installed Wenmode runtime contents."""
    return "\n".join((
        "import json",
        "from importlib.metadata import distribution",
        "names = ('wenmode', 'syrupy-mdast', 'syrupy')",
        "inventory = {}",
        "for name in names:",
        "    item = distribution(name)",
        "    inventory[name] = {",
        "        'version': item.version,",
        "        'requires': item.metadata.get_all('Requires-Dist') or [],",
        "        'license': (",
        "            item.metadata.get('License-Expression')",
        "            or item.metadata.get('License')",
        "        ),",
        "        'files': [str(path) for path in item.files or ()],",
        "    }",
        "print(json.dumps(inventory))",
    ))


def _environment_python(environment_path: Path) -> Path:
    """Return the Python executable in a new virtual environment."""
    return (
        environment_path / "Scripts" / "python.exe"
        if os.name == "nt"
        else environment_path / "bin" / "python"
    )


def _require_tool(executable: str) -> str:
    """Return one required local tool executable."""
    from shutil import which

    resolved = which(executable)
    assert resolved is not None, f"the Wenmode contract requires {executable} on PATH"
    return resolved


def _run(
    command: cabc.Sequence[str | Path],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    """Run one known local command with bounded output and failure evidence."""
    arguments = [str(argument) for argument in command]
    try:
        result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true] -- argv contains no shell text.
            arguments,
            cwd=cwd,
            env=_clean_dependency_environment() if env is None else env,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        pytest.fail(
            f"command timed out after {timeout}s: {arguments!r}\n"
            f"stdout:\n{error.stdout}\nstderr:\n{error.stderr}",
            pytrace=False,
        )
    except subprocess.CalledProcessError as error:
        pytest.fail(
            f"command failed ({error.returncode}): {arguments!r}\n"
            f"stdout:\n{error.stdout}\nstderr:\n{error.stderr}",
            pytrace=False,
        )
    return result


def _wheel_metadata(wheel_path: Path) -> str:
    """Read the sole METADATA payload from a built wheel."""
    with ZipFile(wheel_path) as archive:
        metadata_files = [
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        ]
        assert len(metadata_files) == 1, (
            f"expected one METADATA file in {wheel_path.name}"
        )
        return archive.read(metadata_files[0]).decode("utf-8")


def _assert_installed_metadata(installed: dict[str, dict[str, object]]) -> None:
    """Check the real wheel and editable installs expose the approved metadata."""
    project = installed["syrupy-mdast"]
    assert project["version"] == "0.1.0", (
        f"unexpected installed project metadata: {project!r}"
    )
    assert project["license"] == "ISC", (
        f"unexpected installed project metadata: {project!r}"
    )
    requirements = project["requires"]
    assert isinstance(requirements, list), (
        f"unexpected installed project requirements: {project!r}"
    )
    assert set(requirements) == {
        "syrupy<7.0.0,>=5.0.0",
        "wenmode==0.15.2",
    }, f"unexpected installed project requirements: {project!r}"
    wenmode = installed["wenmode"]
    assert wenmode["version"] == "0.15.2", (
        f"unexpected installed Wenmode metadata: {wenmode!r}"
    )
    assert wenmode["license"] == "BSD-3-Clause", (
        f"unexpected installed Wenmode metadata: {wenmode!r}"
    )
    assert not wenmode["requires"], (
        f"Wenmode has runtime dependencies: {wenmode['requires']!r}"
    )


def _clean_dependency_environment() -> dict[str, str]:
    """Remove credential routing before preparing remote dependency wheels."""
    environment = os.environ.copy()
    for key in list(environment):
        if key.startswith("GIT_CONFIG_") or key in {
            "GH_TOKEN",
            "GITHUB_TOKEN",
            "BASH_ENV",
            "GIT_SSH",
            "GIT_SSH_COMMAND",
        }:
            environment.pop(key, None)
    lody_path = str(Path.home() / ".lody")
    environment["PATH"] = os.pathsep.join(
        part
        for part in environment.get("PATH", "").split(os.pathsep)
        if part != lody_path and not part.startswith(lody_path + os.sep)
    )
    environment["GIT_SSH_COMMAND"] = "/usr/bin/ssh"
    return environment
