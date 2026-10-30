"""Shared fixtures for packaging evidence used by contract and behavioural tests."""

from __future__ import annotations

import pytest

from tests.support.wenmode_installation import Wheelhouse, prepare_wheelhouse


@pytest.fixture(scope="session")
def wheelhouse(tmp_path_factory: pytest.TempPathFactory) -> Wheelhouse:
    """Prepare one immutable local wheelhouse per test worker session.

    Contract and behavioural modules share this fixture so the project wheel,
    runtime wheels, and build backend are fetched and inspected once.

    Returns
    -------
    Wheelhouse
        Paths and inspected release evidence for the prepared wheelhouse.
    """
    return prepare_wheelhouse(tmp_path_factory.mktemp("wenmode-wheelhouse"))
