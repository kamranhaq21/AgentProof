"""The CI workflow (story 1.4) stays pinned, least-privilege, and shaped as the one gate.

``.github/workflows/ci.yml`` is read from the repository root, two levels above the
Python package, so these tests only run from a checkout, never from an installed wheel.
"""

import re
from pathlib import Path
from typing import Any

import yaml

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
WORKFLOWS_DIR = REPOSITORY_ROOT / ".github" / "workflows"
CI_WORKFLOW = WORKFLOWS_DIR / "ci.yml"

# `owner/repo@<40 hex>`: a full commit SHA, never a tag or branch, which can move.
PINNED_ACTION = re.compile(r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$")
# The raw line: the pinned reference followed by the tag it was resolved from.
PINNED_LINE = re.compile(r"^\s*-?\s*uses:\s*(?P<ref>\S+)\s+# v\d+\.\d+\.\d+\s*$")

EXPECTED_OS = ["ubuntu-latest", "windows-latest"]
EXPECTED_PYTHON = ["3.12", "3.13", "3.14", "3.15"]


def _raw() -> str:
    return CI_WORKFLOW.read_text(encoding="utf-8")


def _workflow() -> dict[str, Any]:
    loaded = yaml.safe_load(_raw())
    assert isinstance(loaded, dict)
    return loaded


def _check_job() -> dict[str, Any]:
    jobs = _workflow()["jobs"]
    assert "check" in jobs, "the workflow holds the `check` gate job (other jobs may exist)"
    job = jobs["check"]
    assert isinstance(job, dict)
    return job


def _steps() -> list[dict[str, Any]]:
    steps = _check_job()["steps"]
    assert isinstance(steps, list) and steps
    return steps


def _all_steps() -> list[dict[str, Any]]:
    """Every step of every job: pins and secrets are checked workflow-wide."""
    return [step for job in _workflow()["jobs"].values() for step in job.get("steps", [])]


def _triggers() -> dict[str, Any]:
    # PyYAML reads the bare key `on` as the YAML 1.1 boolean `True`.
    workflow = _workflow()
    triggers = workflow.get("on", workflow.get(True))
    assert isinstance(triggers, dict)
    return triggers


def test_ci_workflow_exists() -> None:
    assert CI_WORKFLOW.is_file()


def test_workflow_runs_on_pull_requests_and_pushes_to_main_and_backlog() -> None:
    triggers = _triggers()
    assert "pull_request" in triggers
    assert triggers["pull_request"] is None, "pull_request is unfiltered: every branch"
    assert triggers["push"] == {"branches": ["main", "backlog"]}


def test_every_action_is_pinned_to_a_full_commit_sha() -> None:
    uses = [step["uses"] for step in _all_steps() if "uses" in step]
    assert uses, "the job must use at least one action"
    unpinned = [ref for ref in uses if not PINNED_ACTION.match(ref)]
    assert unpinned == []


def test_every_pinned_action_line_carries_its_version_comment() -> None:
    # Key lines only: a `uses:` mentioned inside a comment is prose, not a pin.
    uses_lines = [line for line in _raw().splitlines() if re.match(r"^\s*-?\s*uses:", line)]
    assert uses_lines, "no `uses:` lines found in the raw workflow text"
    without_comment = [line for line in uses_lines if not PINNED_LINE.match(line)]
    assert without_comment == []
    # The commented lines are exactly the parsed `uses:` values: nothing hides elsewhere.
    commented_refs = sorted(PINNED_LINE.match(line)["ref"] for line in uses_lines)  # type: ignore[index]
    assert commented_refs == sorted(step["uses"] for step in _all_steps() if "uses" in step)


def test_check_job_uses_checkout_and_setup_uv() -> None:
    owners = [step["uses"].split("@")[0] for step in _steps() if "uses" in step]
    assert owners == ["actions/checkout", "astral-sh/setup-uv"]


def test_top_level_permissions_are_contents_read_only() -> None:
    workflow = _workflow()
    assert workflow["permissions"] == {"contents": "read"}
    assert "permissions" not in _check_job(), "the check job inherits the top-level grant"


def test_matrix_is_two_runners_by_four_python_versions() -> None:
    strategy = _check_job()["strategy"]
    assert strategy["fail-fast"] is False
    matrix = strategy["matrix"]
    assert matrix["os"] == EXPECTED_OS
    assert matrix["python"] == EXPECTED_PYTHON
    assert set(matrix) == {"os", "python"}, "no include/exclude: the full product runs"
    assert "runs-on" in _check_job()
    assert _check_job()["runs-on"] == "${{ matrix.os }}"


def test_job_name_yields_the_eight_protection_contexts() -> None:
    assert _check_job()["name"] == "check (${{ matrix.os }}, ${{ matrix.python }})"


def test_uv_installs_python_from_the_matrix_with_cache_enabled() -> None:
    setup_uv = [step for step in _steps() if step.get("uses", "").startswith("astral-sh/setup-uv@")]
    assert len(setup_uv) == 1
    assert setup_uv[0]["with"] == {"python-version": "${{ matrix.python }}", "enable-cache": True}


def test_check_stage_is_exactly_one_uv_run_check_step_in_the_package() -> None:
    run_steps = [step for step in _steps() if "run" in step]
    assert [step["run"] for step in run_steps] == ["uv sync --locked", "uv run check"]
    for step in run_steps:
        assert step["working-directory"] == "packages/python", step["run"]
        assert step["shell"] == "bash", step["run"]


def test_no_step_references_secrets_or_tolerates_failure() -> None:
    assert "secrets." not in _raw()
    assert "continue-on-error" not in _raw()
