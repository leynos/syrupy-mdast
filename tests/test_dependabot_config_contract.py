"""Contract tests for the Dependabot update configuration.

``.github/dependabot.yml`` decides which manifests Dependabot watches and how
it batches the resulting pull requests. Two properties matter for the GitHub
Actions ecosystem and are invisible to a YAML syntax check:

* every action bump is grouped into a single pull request, because ungrouped
  bumps all edit the same workflow files and the first to merge leaves its
  siblings out of date; and
* the configured directories cover both ``.github/workflows`` and every local
  composite action manifest, because ``/`` reaches only the workflows and the
  root action manifest.

The directory expectations are derived from the repository itself, so a new
composite action fails this contract until Dependabot is told to watch it.
"""

from __future__ import annotations

import typing as typ

import yaml

from tests.support.make_contract import REPO_ROOT, mapping, objects, text_sequence

DEPENDABOT_CONFIG_PATH: typ.Final = REPO_ROOT / ".github" / "dependabot.yml"
_COMPOSITE_ACTION_MANIFESTS: typ.Final = ("action.yml", "action.yaml")
# The workflows live at the repository root; the composite actions each need
# their own entry because Dependabot does not descend into `.github/actions`.
_WORKFLOW_DIRECTORY: typ.Final = "/"
_COMPOSITE_ACTION_PATTERN: typ.Final = "/.github/actions/*"
_GROUP_PATTERN_MATCH_ALL: typ.Final = "*"


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
    """Return whether a Dependabot directory pattern covers ``directory``."""
    prefix, separator, suffix = pattern.partition("/*")
    if not separator:
        return pattern == directory
    return directory.startswith(f"{prefix}/") and "/" not in suffix


def _composite_action_directories() -> frozenset[str]:
    """Return the repository's composite action directories in Dependabot form."""
    actions_root = REPO_ROOT / ".github" / "actions"
    directories = {
        f"/.github/actions/{manifest.parent.name}"
        for manifest in actions_root.glob("*/*")
        if manifest.name in _COMPOSITE_ACTION_MANIFESTS
    }
    assert directories, "expected at least one composite action manifest"
    return frozenset(directories)


def test_github_actions_updates_are_grouped_into_one_pull_request() -> None:
    """GitHub Actions bumps are batched so sibling pull requests cannot stall."""
    update = _update_for("github-actions")
    groups = mapping(update.get("groups"), subject="github-actions groups")
    assert list(groups) == ["github-actions"], (
        "github-actions updates should define exactly one group"
    )
    group = mapping(groups["github-actions"], subject="github-actions group")
    patterns = text_sequence(group.get("patterns"), subject="group patterns")
    assert _GROUP_PATTERN_MATCH_ALL in patterns, (
        "the github-actions group should match every action with the '*' pattern"
    )
    assert group.get("exclude-patterns") is None, (
        "no action should be excluded from the group, or it reappears as a lone "
        "pull request that collides with the group"
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
