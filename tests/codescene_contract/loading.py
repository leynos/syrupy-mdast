"""Load GitHub Actions workflows strictly enough for a contract to trust.

This is the one filesystem boundary in the package. A workflow that does
not parse, repeats a key, or is not a mapping is refused with its file
named, and an empty directory is the reader failing rather than the
repository complying.
"""

from __future__ import annotations

import collections.abc as cabc
import re
import typing as typ

import yaml
from yaml.constructor import ConstructorError

if typ.TYPE_CHECKING:
    from pathlib import Path

#: A parsed workflow. The key type is `object` because a key need not be a
#: string: `true:` parses to the boolean `True`, and a reader handed a
#: document from a YAML 1.1 loader sees an unquoted `on:` that way too.
type Document = dict[object, object]

#: The YAML tag PyYAML gives a resolved boolean.
_BOOL_TAG: typ.Final[str] = "tag:yaml.org,2002:bool"

#: The scalars GitHub reads as booleans. YAML 1.1 also resolves `yes`,
#: `no`, `on` and `off`, but GitHub passes those to an action as strings,
#: so an input such as `with-ratchet: yes` must stay the string it is.
_GITHUB_BOOL: typ.Final[re.Pattern[str]] = re.compile(
    r"^(?:true|True|TRUE|false|False|FALSE)$"
)

#: File suffixes GitHub runs as workflows, compared without case.
WORKFLOW_SUFFIXES: typ.Final[frozenset[str]] = frozenset({".yml", ".yaml"})


class WorkflowReadingError(Exception):
    """Raised when a workflow cannot be read into a shape the rules trust."""


class _UniqueKeyLoader(yaml.SafeLoader):
    """A `yaml.SafeLoader` refusing a mapping that declares a key twice.

    PyYAML keeps the last of two equal keys and says nothing, so a job
    declaring `runs-on` twice parses into a document holding only the
    second value while the rules read the half GitHub may not run. Only
    `true` and `false` resolve to booleans, as GitHub reads them.
    """

    def construct_mapping(
        self,
        node: yaml.MappingNode,
        deep: bool = False,  # ruff: ignore[boolean-type-hint-positional-argument, boolean-default-value-positional-argument] -- PyYAML's own signature, overridden.
    ) -> dict[typ.Hashable, typ.Any]:
        """Construct one mapping, refusing a key already seen in it.

        Returns
        -------
        dict[typ.Hashable, typ.Any]
            The mapping PyYAML constructs once every key is unique.

        Raises
        ------
        ConstructorError
            If a key appears twice or cannot be hashed, naming it and where
            it appears.

        """
        seen: set[object] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, cabc.Hashable):
                context = "while constructing a mapping"
                problem = f"found unhashable key {key!r}"
                raise ConstructorError(
                    context, node.start_mark, problem, key_node.start_mark
                )
            if key in seen:
                context = "while constructing a mapping"
                problem = f"found duplicate key {key!r}"
                raise ConstructorError(
                    context, node.start_mark, problem, key_node.start_mark
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


# PyYAML reads the resolver table from the class, so the YAML 1.1 boolean
# resolvers are dropped there, and only GitHub's spellings are added back.
_UniqueKeyLoader.yaml_implicit_resolvers = {
    first: [pair for pair in resolvers if pair[0] != _BOOL_TAG]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_UniqueKeyLoader.add_implicit_resolver(_BOOL_TAG, _GITHUB_BOOL, list("tTfF"))


def load_workflow(text: str) -> Document:
    r"""Parse one workflow, refusing duplicate keys and non-mapping documents.

    Parameters
    ----------
    text : str
        The workflow's YAML text.

    Returns
    -------
    Document
        The parsed workflow.

    Raises
    ------
    WorkflowReadingError
        If the text is not YAML, repeats a key, uses a key that cannot be
        hashed, or is not a mapping.

    Examples
    --------
    >>> load_workflow("on: push\njobs: {}\n")
    {'on': 'push', 'jobs': {}}

    """
    # What `yaml.load` does, spelt out so no linter mistakes the strict
    # SafeLoader subclass for an unsafe loader.
    loader = _UniqueKeyLoader(text)
    try:
        parsed = loader.get_single_data()
    except yaml.YAMLError as error:
        message = f"not a workflow document: {error}"
        raise WorkflowReadingError(message) from error
    finally:
        loader.dispose()
    if not isinstance(parsed, dict):
        message = "a workflow must parse to a top-level mapping"
        raise WorkflowReadingError(message)
    return typ.cast("Document", parsed)


def read_workflows(directory: Path) -> dict[str, Document]:
    """Return every workflow under one directory, by file name.

    Both suffixes are read, whatever their case, because GitHub runs a
    workflow named either way.

    Parameters
    ----------
    directory : Path
        The directory to read workflows from.

    Returns
    -------
    dict[str, Document]
        Every workflow under `directory`, by file name.

    Raises
    ------
    WorkflowReadingError
        If the directory cannot be listed or holds no workflow, or a
        workflow cannot be read or does not parse. The message names the
        directory or the file, and the I/O error, if any, is the cause.

    """
    paths = [
        path
        for path in _entries(directory)
        if path.suffix.casefold() in WORKFLOW_SUFFIXES
    ]
    if not paths:
        message = f"no workflow was read from {directory}; the reader is broken"
        raise WorkflowReadingError(message)
    return {path.name: _load_file(path) for path in paths}


#: File names GitHub reads a local action's metadata from.
ACTION_FILES: typ.Final[tuple[str, ...]] = ("action.yml", "action.yaml")


def load_action(text: str) -> Document:
    r"""Parse one local action into the shape of a workflow the rules read.

    A composite action's steps run in its caller's job, so the closure
    rules must read them as they read a called workflow's. The steps become
    one job of a workflow triggered only by `workflow_call`, which no seed
    reading counts, and the rest of the metadata is kept under `action`, so
    a whole-document reading still sees its inputs and any `runs` field.
    Text that `load_workflow` refuses is refused the same way.

    Parameters
    ----------
    text : str
        The action metadata's YAML text.

    Returns
    -------
    Document
        A workflow-shaped document holding the action's steps.

    Raises
    ------
    WorkflowReadingError
        If the action's `runs` field is not a mapping.

    Examples
    --------
    >>> load_action("runs:\n  using: composite\n  steps: [{run: echo}]\n")["jobs"]
    {'action': {'steps': [{'run': 'echo'}]}}

    """
    parsed = load_workflow(text)
    runs = parsed.get("runs")
    if not isinstance(runs, dict):
        message = f"an action's `runs` must be a mapping, not {runs!r}"
        raise WorkflowReadingError(message)
    metadata = {key: value for key, value in parsed.items() if key != "runs"}
    metadata["runs"] = {key: value for key, value in runs.items() if key != "steps"}
    document: Document = {
        "on": "workflow_call",
        "jobs": {"action": {"steps": runs.get("steps", [])}},
        "action": metadata,
    }
    return document


def read_actions(root: Path) -> dict[str, Document]:
    """Return every local action under `.github/actions`, by its `uses:` path.

    The key is the path a step names after `./`, such as
    `.github/actions/build`, so the closure can look an action up by the
    reference that runs it. An action this reads nothing for is refused
    where it is called, not here, since a repository need hold none. Metadata
    that cannot be read or parsed raises `WorkflowReadingError` naming the
    file.

    Parameters
    ----------
    root : Path
        The repository root.

    Returns
    -------
    dict[str, Document]
        Every local action, workflow-shaped, by its path from `root`.

    """
    directory = root / ".github" / "actions"
    paths = sorted(path for name in ACTION_FILES for path in directory.rglob(name))
    return {
        path.parent.relative_to(root).as_posix(): _load_file(path, load_action)
        for path in paths
    }


def _entries(directory: Path) -> list[Path]:
    """List one directory in name order, naming it in any I/O failure."""
    try:
        return sorted(directory.iterdir())
    except OSError as error:
        message = f"{directory} could not be listed: {error}"
        raise WorkflowReadingError(message) from error


def _load_file(
    path: Path, parse: cabc.Callable[[str], Document] = load_workflow
) -> Document:
    """Read and parse one workflow or action file, naming it in any failure."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        message = f"{path.name} could not be read: {error}"
        raise WorkflowReadingError(message) from error
    try:
        return parse(text)
    except WorkflowReadingError as error:
        message = f"{path.name}: {error}"
        raise WorkflowReadingError(message) from error
