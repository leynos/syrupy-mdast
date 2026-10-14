"""Typed test support for the authored Markdown contract corpus."""

import collections.abc as cabc
import dataclasses
import typing as typ
from pathlib import Path, PurePosixPath, PureWindowsPath

type CaseKind = typ.Literal["markdown", "synthetic"]
type LineEndings = typ.Literal["lf", "crlf", "cr", "none"]
type RelationKind = typ.Literal["equal", "distinct"]

RULE_IDS = frozenset(f"NF-{number}" for number in range(1, 14)) | frozenset({
    "remove-position",
    "remove-empty-data",
    "merge-plain-text",
    "normalize-line-endings",
    "order-members",
    "preserve-values",
    "writer-format",
})
MIN_RELATION_CASES = 2


@dataclasses.dataclass(frozen=True, slots=True)
class CaseRecord:
    """One ordered source and its independently authored expected payload."""

    id: str
    rules: tuple[str, ...]
    reason: str
    kind: CaseKind
    input: Path
    expected: Path
    line_endings: LineEndings | None


@dataclasses.dataclass(frozen=True, slots=True)
class RelationRecord:
    """An equality group or a pairwise distinction between named cases."""

    id: str
    relation: RelationKind
    cases: tuple[str, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class ContractCorpus:
    """The ordered case and relation records loaded from one corpus root."""

    cases: tuple[CaseRecord, ...]
    relations: tuple[RelationRecord, ...]


def load_corpus(root: Path) -> ContractCorpus:
    """Load a corpus manifest into ordered, validated records.

    Returns
    -------
    ContractCorpus
        Validated case and relation records with resolved file paths.

    Examples
    --------
    ``load_corpus(root)`` loads the manifest rooted at ``root``.
    """
    from .markdown_contract_loading import load_corpus as load_manifest

    return load_manifest(root)


def read_source(path: Path) -> str:
    r"""Decode one Markdown source without changing its newline bytes.

    Returns
    -------
    str
        The strictly decoded source with all original newline characters.

    Examples
    --------
    For a file containing ``b"first\\r\\nsecond\\r"``, the result keeps both
    the CRLF pair and the final bare CR in the decoded string.
    """
    return path.read_bytes().decode("utf-8")


def _table(value: object, location: str) -> dict[str, object]:
    """Return a string-keyed TOML table or identify its location.

    Returns
    -------
    dict[str, object]
        A plain dictionary containing the table's original keys and values.

    Raises
    ------
    ValueError
        If the value is not a string-keyed table.

    Examples
    --------
    ``_table({"id": "case"}, "case")`` returns the same mapping.
    """
    if not isinstance(value, cabc.Mapping) or any(
        not isinstance(key, str) for key in value
    ):
        message = f"{location} must be a TOML table"
        raise ValueError(message)
    return dict(value.items())


def _string(value: object, location: str) -> str:
    """Return a non-empty string field and name it when the type is wrong.

    Returns
    -------
    str
        The validated string value.

    Raises
    ------
    ValueError
        If the value is not a non-empty string.

    Examples
    --------
    ``_string("NF-1", "case rules")`` returns ``"NF-1"``.
    """
    if not isinstance(value, str) or not value:
        message = f"{location} must be a non-empty string"
        raise ValueError(message)
    return value


def _string_tuple(value: object, location: str) -> tuple[str, ...]:
    """Return a TOML string array as an immutable tuple.

    Returns
    -------
    tuple[str, ...]
        The array items in their original order.

    Raises
    ------
    TypeError
        If the value is not a list or contains a non-string item.

    Examples
    --------
    ``_string_tuple(["NF-1"], "case rules")`` returns ``("NF-1",)``.
    """
    if not isinstance(value, list):
        message = f"{location} must be an array of strings"
        raise TypeError(message)
    strings: list[str] = []
    for item in value:
        if not isinstance(item, str):
            message = f"{location} must contain only strings"
            raise TypeError(message)
        strings.append(item)
    return tuple(strings)


def _resolve_corpus_file(root: Path, value: object, location: str) -> Path:
    """Resolve an existing corpus file without permitting path escapes.

    Returns
    -------
    Path
        The absolute path of the validated corpus file.

    Raises
    ------
    ValueError
        If the path is absolute, escapes the root, or does not exist.

    Examples
    --------
    A path such as ``"../outside.txt"`` raises ``ValueError`` instead of
    resolving outside the supplied corpus directory.
    """
    relative_name = _string(value, f"{location} path")
    relative_path = PurePosixPath(relative_name)
    windows_path = PureWindowsPath(relative_name)
    if any((
        relative_path.is_absolute(),
        windows_path.is_absolute(),
        bool(windows_path.drive),
        "\\" in relative_name,
        ".." in relative_path.parts,
        not relative_path.parts,
    )):
        message = f"{location} path must be relative to the corpus root"
        raise ValueError(message)

    resolved_root = root.resolve()
    resolved_path = resolved_root.joinpath(*relative_path.parts).resolve()
    if not resolved_path.is_relative_to(resolved_root):
        message = f"{location} path escapes the corpus root"
        raise ValueError(message)
    if not resolved_path.is_file():
        message = f"{location} file does not exist: {relative_name!r}"
        raise ValueError(message)
    return resolved_path
