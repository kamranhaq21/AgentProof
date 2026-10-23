"""Every workflow stays pinned and least-privilege; CI keeps the one gate (story 1.4).

Story 1.6 adds the `wheel`, `smoke`, and `audit` jobs around the gate and the
``release-draft.yml`` workflow, and nothing anywhere publishes to a package index.

``.github/workflows/*.yml`` are read from the repository root, two levels above the
Python package, so these tests only run from a checkout, never from an installed wheel.
"""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
WORKFLOWS_DIR = REPOSITORY_ROOT / ".github" / "workflows"
CI_WORKFLOW = WORKFLOWS_DIR / "ci.yml"
RELEASE_WORKFLOW = WORKFLOWS_DIR / "release-draft.yml"
WORKFLOW_FILES = sorted(WORKFLOWS_DIR.glob("*.yml"))

# `owner/repo@<40 hex>`: a full commit SHA, never a tag or branch, which can move.
PINNED_ACTION = re.compile(r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$")
# The raw line: the pinned reference followed by the tag it was resolved from.
PINNED_LINE = re.compile(r"^\s*-?\s*uses:\s*(?P<ref>\S+)\s+# v\d+\.\d+\.\d+\s*$")

# The maintainer's decision (story 1.6): these four, and no third-party release action.
ALLOWED_ACTIONS = {
    "actions/checkout",
    "astral-sh/setup-uv",
    "actions/upload-artifact",
    "actions/download-artifact",
}

# No publishing from any workflow until epic 9 story 5. Case-sensitive on purpose: the
# prose name "PyPI" in a comment is fine, a `PYPI_*` secret or a publish tool is not.
# Whole words, so prose such as "intertwined" never trips the scan; `PYPI` is matched
# as a prefix too, so a `PYPI_TOKEN` secret name trips it (retrospective epic 1, finding 2).
FORBIDDEN_PUBLISH_TEXT = ("uv publish", "twine", "pypi-token", "PYPI", "gh-action-pypi-publish")
FORBIDDEN_PUBLISH_PATTERNS = [
    re.compile(r"(?<!\w)PYPI") if text == "PYPI" else re.compile(rf"\b{re.escape(text)}\b")
    for text in FORBIDDEN_PUBLISH_TEXT
]

EXPECTED_OS = ["ubuntu-latest", "windows-latest"]
EXPECTED_PYTHON = ["3.12", "3.13", "3.14", "3.15"]

workflow_files = pytest.mark.parametrize("path", WORKFLOW_FILES, ids=lambda p: p.name)


def _raw(path: Path = CI_WORKFLOW) -> str:
    return path.read_text(encoding="utf-8")


def _load(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(_raw(path))
    assert isinstance(loaded, dict), path.name
    return loaded


def _workflow() -> dict[str, Any]:
    return _load(CI_WORKFLOW)


def _release() -> dict[str, Any]:
    return _load(RELEASE_WORKFLOW)


def _job(workflow: dict[str, Any], name: str) -> dict[str, Any]:
    jobs = workflow["jobs"]
    assert name in jobs, f"the workflow holds the `{name}` job (other jobs may exist)"
    job = jobs[name]
    assert isinstance(job, dict)
    return job


def _check_job() -> dict[str, Any]:
    return _job(_workflow(), "check")


def _steps() -> list[dict[str, Any]]:
    steps = _check_job()["steps"]
    assert isinstance(steps, list) and steps
    return steps


def _all_steps(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    """Every step of every job: pins and secrets are checked workflow-wide."""
    return [step for job in workflow["jobs"].values() for step in job.get("steps", [])]


def _uses(steps: list[dict[str, Any]]) -> list[str]:
    return [step["uses"] for step in steps if "uses" in step]


def _run_steps(job: dict[str, Any]) -> list[dict[str, Any]]:
    return [step for step in job["steps"] if "run" in step]


def _triggers(workflow: dict[str, Any]) -> dict[str, Any]:
    # PyYAML reads the bare key `on` as the YAML 1.1 boolean `True`.
    triggers = workflow.get("on", workflow.get(True))
    assert isinstance(triggers, dict)
    return triggers


def test_ci_workflow_exists() -> None:
    assert CI_WORKFLOW.is_file()


def test_release_workflow_exists() -> None:
    assert RELEASE_WORKFLOW.is_file()
    assert RELEASE_WORKFLOW in WORKFLOW_FILES and CI_WORKFLOW in WORKFLOW_FILES


def test_workflow_runs_on_pull_requests_and_pushes_to_main_and_backlog() -> None:
    triggers = _triggers(_workflow())
    assert "pull_request" in triggers
    assert triggers["pull_request"] is None, "pull_request is unfiltered: every branch"
    assert triggers["push"] == {"branches": ["main", "backlog"]}


@workflow_files
def test_every_action_is_pinned_to_a_full_commit_sha(path: Path) -> None:
    uses = _uses(_all_steps(_load(path)))
    assert uses, "the workflow must use at least one action"
    unpinned = [ref for ref in uses if not PINNED_ACTION.match(ref)]
    assert unpinned == []


@workflow_files
def test_every_pinned_action_line_carries_its_version_comment(path: Path) -> None:
    # Key lines only: a `uses:` mentioned inside a comment is prose, not a pin.
    uses_lines = [line for line in _raw(path).splitlines() if re.match(r"^\s*-?\s*uses:", line)]
    assert uses_lines, "no `uses:` lines found in the raw workflow text"
    without_comment = [line for line in uses_lines if not PINNED_LINE.match(line)]
    assert without_comment == []
    # The commented lines are exactly the parsed `uses:` values: nothing hides elsewhere.
    commented_refs = sorted(PINNED_LINE.match(line)["ref"] for line in uses_lines)  # type: ignore[index]
    assert commented_refs == sorted(_uses(_all_steps(_load(path))))


@workflow_files
def test_only_the_four_agreed_actions_are_used(path: Path) -> None:
    owners = {ref.split("@")[0] for ref in _uses(_all_steps(_load(path)))}
    assert owners <= ALLOWED_ACTIONS, owners - ALLOWED_ACTIONS


@workflow_files
def test_no_step_references_secrets_or_tolerates_failure(path: Path) -> None:
    raw = _raw(path)
    assert "secrets." not in raw
    assert "continue-on-error" not in raw


@workflow_files
def test_no_workflow_publishes_to_a_package_index(path: Path) -> None:
    raw = _raw(path)
    found = [p.pattern for p in FORBIDDEN_PUBLISH_PATTERNS if p.search(raw)]
    assert found == [], f"{path.name} mentions publishing machinery: {found}"


def test_check_job_uses_checkout_and_setup_uv() -> None:
    owners = [ref.split("@")[0] for ref in _uses(_steps())]
    assert owners == ["actions/checkout", "astral-sh/setup-uv"]


def test_top_level_permissions_are_contents_read_only() -> None:
    workflow = _workflow()
    assert workflow["permissions"] == {"contents": "read"}
    for name, job in workflow["jobs"].items():
        assert "permissions" not in job, f"the `{name}` job inherits the top-level grant"


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
    run_steps = _run_steps(_check_job())
    assert [step["run"] for step in run_steps] == ["uv sync --locked", "uv run check"]
    for step in run_steps:
        assert step["working-directory"] == "packages/python", step["run"]
        assert step["shell"] == "bash", step["run"]


def test_wheel_job_builds_the_wheel_and_uploads_it_as_the_wheel_artifact() -> None:
    job = _job(_workflow(), "wheel")
    assert job["runs-on"] == "ubuntu-latest"
    assert "needs" not in job, "the wheel builds alongside the gate, not after it"
    builds = [step for step in _run_steps(job) if step["run"].startswith("uv build")]
    assert len(builds) == 1
    assert builds[0]["run"] == "uv build --wheel --out-dir dist"
    assert builds[0]["working-directory"] == "packages/python"
    uploads = [s for s in job["steps"] if s.get("uses", "").startswith("actions/upload-artifact@")]
    assert len(uploads) == 1
    assert uploads[0]["with"] == {
        "name": "wheel",
        "path": "packages/python/dist/*.whl",
        "if-no-files-found": "error",
    }
    assert job["steps"][-1] is uploads[0], "the upload is the last step: nothing runs after it"


def test_smoke_job_installs_the_uploaded_wheel_by_path_on_both_runners() -> None:
    job = _job(_workflow(), "smoke")
    assert job["needs"] == "wheel"
    assert job["name"] == "smoke (${{ matrix.os }})"
    assert job["runs-on"] == "${{ matrix.os }}"
    assert job["strategy"] == {"fail-fast": False, "matrix": {"os": EXPECTED_OS}}
    downloads = [
        s for s in job["steps"] if s.get("uses", "").startswith("actions/download-artifact@")
    ]
    assert len(downloads) == 1
    assert downloads[0]["with"] == {"name": "wheel", "path": "dist"}
    run_steps = _run_steps(job)
    assert [step["run"] for step in run_steps[:2]] == [
        "uv venv .smoke",
        "uv pip install --python .smoke dist/*.whl",
    ]
    for step in run_steps:
        assert step["shell"] == "bash", step["run"]
        assert "working-directory" not in step, "the smoke venv lives at the checkout root"
    # Never by name from an index: every install step is the downloaded file, and nothing
    # names the distribution or an index.
    installs = [step["run"] for step in run_steps if "pip install" in step["run"]]
    assert installs == ["uv pip install --python .smoke dist/*.whl"]
    assert not any(re.search(r"--index|--extra-index|-i ", step["run"]) for step in run_steps)
    # The installed console script runs, on either venv layout, and its output is
    # compared with pyproject.toml; an empty expectation fails rather than matching empty.
    verify = run_steps[-1]["run"]
    assert "exe=.smoke/bin/agentproof\n" in verify
    assert '[ -x "$exe" ] || exe=.smoke/Scripts/agentproof.exe' in verify
    assert """actual="$("$exe" version | tr -d '\\r')\"""" in verify
    assert "tr -d '\\r' < packages/python/pyproject.toml" in verify
    assert 'test -n "$expected" && test "$actual" = "$expected"' in verify


def test_audit_job_runs_pip_audit_strictly_against_the_exported_lock() -> None:
    job = _job(_workflow(), "audit")
    assert job["runs-on"] == "ubuntu-latest"
    run_steps = _run_steps(job)
    assert [step["run"] for step in run_steps] == [
        "uv export --locked --all-groups --no-emit-project --no-emit-workspace -o requirements.txt",
        "uvx pip-audit==2.10.1 --strict -r requirements.txt",
    ]
    for step in run_steps:
        assert step["working-directory"] == "packages/python", step["run"]
        assert step["shell"] == "bash", step["run"]


def test_release_workflow_triggers_only_on_version_tags() -> None:
    assert _triggers(_release()) == {"push": {"tags": ["v*"]}}


def test_release_workflow_permissions_are_exactly_contents_write() -> None:
    release = _release()
    assert release["permissions"] == {"contents": "write"}
    assert list(release["jobs"]) == ["draft-release"]
    assert "permissions" not in release["jobs"]["draft-release"]


def test_release_workflow_drafts_a_release_with_gh_and_the_job_token() -> None:
    job = _job(_release(), "draft-release")
    assert job["runs-on"] == "ubuntu-latest"
    owners = [ref.split("@")[0] for ref in _uses(job["steps"])]
    assert owners == ["actions/checkout", "astral-sh/setup-uv"]
    run_steps = _run_steps(job)
    assert len(run_steps) == 3
    guard, build, create = run_steps
    # The tag names the declared version, or the job fails before building anything.
    assert 'test -n "$expected" && test "${GITHUB_REF_NAME#v}" = "$expected"' in guard["run"]
    assert "working-directory" not in guard
    assert build["run"] == "uv build"
    assert build["working-directory"] == "packages/python"
    assert "env" not in guard and "env" not in build
    assert create["env"] == {"GH_TOKEN": "${{ github.token }}"}
    for step in run_steps:
        assert step["shell"] == "bash", step["run"]
    assert (
        'gh release create "$GITHUB_REF_NAME" --draft --title "$GITHUB_REF_NAME"'
        " --generate-notes packages/python/dist/*"
    ) in create["run"]
    assert 'gh release upload "$GITHUB_REF_NAME" --clobber packages/python/dist/*' in create["run"]
    assert "gh release edit" not in create["run"], "an existing release keeps its draft state"
    assert job["steps"][-1] is create, "creating the draft is the last step: nothing publishes"


def test_publish_scan_catches_secret_names_and_spares_prose() -> None:
    hits = [p.pattern for p in FORBIDDEN_PUBLISH_PATTERNS if p.search("env: PYPI_TOKEN")]
    assert hits == ["(?<!\\w)PYPI"]
    assert not any(p.search("intertwined PyPI prose MYPYPI") for p in FORBIDDEN_PUBLISH_PATTERNS)
