"""Contract tests for the Dependabot update configuration.

``.github/dependabot.yml`` decides which manifests Dependabot watches and how
it batches the resulting pull requests. Two properties matter and are
invisible to a YAML syntax check:

* every ecosystem runs daily, and its minor and patch bumps are grouped into a
  single pull request, because ungrouped bumps all edit the same files and the
  first to merge leaves its siblings out of date, while each major stays
  ungrouped so it can be reviewed on its own; and
* the configured directories cover both ``.github/workflows`` and every local
  composite action manifest, because ``/`` reaches only the workflows and the
  root action manifest.

The directory expectations are derived from the repository itself, so a new
composite action fails this contract until Dependabot is told to watch it.
"""

from __future__ import annotations

import re
import typing as typ

import pytest
import yaml

from tests.support.make_contract import REPO_ROOT, mapping, objects, text_sequence

DEPENDABOT_CONFIG_PATH: typ.Final = REPO_ROOT / ".github" / "dependabot.yml"
_COMPOSITE_ACTION_MANIFESTS: typ.Final = ("action.yml", "action.yaml")
# The workflows live at the repository root; the composite actions each need
# their own entry because Dependabot does not descend into `.github/actions`.
_WORKFLOW_DIRECTORY: typ.Final = "/"
_COMPOSITE_ACTION_PATTERN: typ.Final = "/.github/actions/*"
_GROUP_PATTERN_MATCH_ALL: typ.Final = "*"
# Estate Dependabot policy: every ecosystem is checked daily, and one
# catch-all group batches minor and patch bumps while majors stay ungrouped.
_ECOSYSTEMS: typ.Final = ("github-actions", "pip")
_INTERVAL: typ.Final = "daily"
_GROUPED_UPDATE_TYPES: typ.Final = frozenset(("minor", "patch"))
_VERSION_UPDATES: typ.Final = "version-updates"


def _dependabot_config() -> dict[str, object]:
    """Return the parsed Dependabot configuration."""
    return mapping(
        yaml.safe_load(DEPENDABOT_CONFIG_PATH.read_text(encoding="utf-8")),
        subject="Dependabot config",
    )


def _update_for(ecosystem: str) -> dict[str, object]:
    """Return the sole Dependabot update block for ``ecosystem``."""
    updates = objects(_dependabot_config().get("updates"), subject="updates")
    matches = [
        update for update in updates if update.get("package-ecosystem") == ecosystem
    ]
    assert len(matches) == 1, (
        f"expected one {ecosystem!r} update block, found {len(matches)}"
    )
    return matches[0]


def _configured_directories(update: dict[str, object]) -> frozenset[str]:
    """Return every directory the update block configures."""
    directories = update.get("directories")
    if directories is not None:
        return frozenset(
            text_sequence(directories, subject="github-actions directories")
        )
    directory = update.get("directory")
    assert isinstance(directory, str), (
        "the github-actions update block must configure directory or directories"
    )
    return frozenset((directory,))


def _directory_pattern_matches(pattern: str, directory: str) -> bool:
    """Return whether a Dependabot directory pattern covers ``directory``.

    ``*`` matches within one path segment and ``**`` spans segments, so
    ``/.github/actions/*`` covers ``/.github/actions/lint`` but not
    ``/.github/actions/release/sign``. ``**/`` also matches zero levels, as
    Dependabot's does, so ``/.github/actions/**/*`` covers both.

    Returns
    -------
    bool
        Whether ``pattern`` covers ``directory``.
    """
    tokens = {"**/": "(?:.*/)?", "**": ".*", "*": "[^/]*"}
    regex = "".join(
        tokens.get(part, re.escape(part))
        for part in re.split(r"(\*\*/|\*\*|\*)", pattern)
    )
    return re.fullmatch(regex, directory) is not None


def _composite_action_directories() -> frozenset[str]:
    """Return the repository's composite action directories in Dependabot form."""
    # Search every depth: an action nested below another directory still needs
    # a pattern that reaches its own directory.
    directories = {
        f"/{manifest.parent.relative_to(REPO_ROOT).as_posix()}"
        for manifest in (REPO_ROOT / ".github" / "actions").rglob("action.y*ml")
        if manifest.name in _COMPOSITE_ACTION_MANIFESTS
    }
    assert directories, "expected at least one composite action manifest"
    return frozenset(directories)


def test_the_policy_covers_every_declared_ecosystem() -> None:
    """A new ecosystem must join the policy deliberately, not bypass it."""
    updates = objects(_dependabot_config().get("updates"), subject="updates")
    declared = sorted(str(update.get("package-ecosystem")) for update in updates)
    assert declared == sorted(_ECOSYSTEMS), (
        f"the Dependabot policy covers {sorted(_ECOSYSTEMS)}; "
        f"the configuration declares {declared}"
    )


@pytest.mark.parametrize("ecosystem", _ECOSYSTEMS)
def test_every_update_block_checks_daily(ecosystem: str) -> None:
    """Each ecosystem is checked for updates every day."""
    schedule = mapping(
        _update_for(ecosystem).get("schedule"), subject=f"{ecosystem} schedule"
    )
    assert schedule.get("interval") == _INTERVAL, (
        f"the {ecosystem} update block should run {_INTERVAL!r}; "
        f"got {schedule.get('interval')!r}"
    )


@pytest.mark.parametrize("ecosystem", _ECOSYSTEMS)
def test_every_update_block_batches_minor_and_patch_updates_only(
    ecosystem: str,
) -> None:
    """Routine bumps share one pull request; each major arrives on its own."""
    groups = mapping(
        _update_for(ecosystem).get("groups"), subject=f"{ecosystem} groups"
    )
    assert len(groups) == 1, (
        f"{ecosystem} updates should define exactly one group; got {sorted(groups)}"
    )
    [(name, raw_group)] = groups.items()
    group = mapping(raw_group, subject=f"{ecosystem} group {name}")
    patterns = text_sequence(group.get("patterns"), subject="group patterns")
    assert tuple(patterns) == (_GROUP_PATTERN_MATCH_ALL,), (
        f"the {ecosystem} group should match every dependency with '*' alone; "
        f"got {patterns}"
    )
    # Without `update-types` the group also takes majors, which would then
    # hide a breaking bump inside the routine batch.
    update_types = text_sequence(group.get("update-types"), subject="update-types")
    assert frozenset(update_types) == _GROUPED_UPDATE_TYPES, (
        f"the {ecosystem} group should batch exactly minor and patch; "
        f"got {update_types}"
    )
    assert group.get("exclude-patterns") is None, (
        "no dependency should be excluded from the group, or it reappears as a "
        "lone pull request that collides with the group"
    )
    applies_to = group.get("applies-to", _VERSION_UPDATES)
    assert applies_to == _VERSION_UPDATES, (
        f"the {ecosystem} group should apply to {_VERSION_UPDATES!r}; "
        f"got {applies_to!r}"
    )


@pytest.mark.parametrize(
    ("pattern", "directory", "expected"),
    [
        ("/", "/", True),
        ("/.github/actions/*", "/.github/actions/lint", True),
        ("/.github/actions/*", "/.github/actions/release/sign", False),
        ("/.github/actions/**", "/.github/actions/release/sign", True),
        ("/.github/actions/**/*", "/.github/actions/lint", True),
        ("/.github/actions/**/*", "/.github/actions/release/sign", True),
        ("/.github/actions/lint", "/.github/actions/lint", True),
        ("/.github/actions/lint", "/.github/actions/lints", False),
    ],
)
def test_directory_patterns_match_like_dependabot(
    pattern: str, directory: str, *, expected: bool
) -> None:
    """``*`` stays within one path segment; ``**`` spans segments."""
    assert _directory_pattern_matches(pattern, directory) is expected, (
        f"{pattern!r} should {'cover' if expected else 'not cover'} {directory!r}"
    )


def test_github_actions_directories_cover_workflows_and_composite_actions() -> None:
    """Every action manifest the repository owns is reachable by Dependabot."""
    configured = _configured_directories(_update_for("github-actions"))
    assert _WORKFLOW_DIRECTORY in configured, (
        "the github-actions update block should watch / for .github/workflows"
    )
    assert (REPO_ROOT / ".github" / "workflows").is_dir(), (
        "expected a .github/workflows directory covered by /"
    )
    for action_directory in sorted(_composite_action_directories()):
        assert any(
            _directory_pattern_matches(pattern, action_directory)
            for pattern in configured
        ), (
            f"composite action directory {action_directory} is not covered by "
            f"the configured directories {sorted(configured)}"
        )
    assert _COMPOSITE_ACTION_PATTERN in configured, (
        "the github-actions update block should cover .github/actions/* so "
        "composite action pins stay current"
    )


def test_dependabot_config_targets_the_supported_schema_version() -> None:
    """The configuration declares the schema version Dependabot expects."""
    assert _dependabot_config().get("version") == 2, (
        "the Dependabot configuration should declare version 2"
    )
