"""Contract tests for how CI workflows provision the Makefile parser.

Every job that runs the full pytest suite needs Makeutil, so the workflows are
parsed with PyYAML and the installation and verification steps are asserted
structurally rather than as source text.
"""

from __future__ import annotations

import typing as typ

from tests.support import makeutil_contract
from tests.support.make_contract import (
    mapping,
    objects,
    sole_workflow_step,
    workflow_job,
)

_FULL_SUITE_WORKFLOW_JOBS: typ.Final = (
    (".github/workflows/ci.yml", "lint-test"),
    (".github/workflows/act-validation.yml", "act-validation"),
    (".github/workflows/coverage-main.yml", "coverage-upload"),
)


def test_full_suite_workflows_provision_the_makefile_parser_identically() -> None:
    """Every job running the full pytest suite must install Makeutil alike.

    Each full-suite job installs the pinned prebuilt release through the shared
    action, takes its default version, carries no from-source pin, and smoke-tests
    the binary straight after installing it.
    """
    for workflow_path, job_name in _FULL_SUITE_WORKFLOW_JOBS:
        job = workflow_job(workflow_path, job_name)
        environment = mapping(
            job.get("env", {}), subject=f"{workflow_path} {job_name} environment"
        )
        for key in ("MAKEUTIL_REVISION", "MAKEUTIL_TOOLCHAIN"):
            assert key not in environment, (
                f"{workflow_path} {job_name} must not carry the from-source {key}"
            )
        contract = f"{workflow_path} {job_name} Makeutil"
        install_step = sole_workflow_step(workflow_path, job_name, "Install makeutil")
        makeutil_contract.assert_installation(install_step, contract=contract)
        makeutil_contract.assert_verification(
            install_step,
            sole_workflow_step(workflow_path, job_name, "Verify makeutil"),
            contract=contract,
        )
        makeutil_contract.assert_verification_follows_install(
            objects(job.get("steps"), subject=f"{contract} steps"),
            contract=contract,
        )
