"""Repository hygiene (story 1.5): line endings, ignore rules, policy files, decision records.

These tests read files at the repository root, two levels above the Python package, so
they only run from a checkout, never from an installed wheel.
"""

import re
import tomllib
from pathlib import Path

import yaml

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
GOLDEN_DIR = PACKAGE_ROOT / "tests" / "golden"
DECISIONS_DIR = REPOSITORY_ROOT / "docs" / "decisions"

REQUIRED_IGNORES = (
    ".claude/skills/",
    ".venv/",
    "dist/",
    "build/",
    "*.egg-info/",
    "__pycache__/",
    "*.pyc",
    ".pytest_cache/",
    ".ruff_cache/",
    ".mypy_cache/",
    ".import_linter_cache/",
    ".hypothesis/",
    "agentproof-output/",
    ".agentproof-*",
    "_bmad/custom/*.user.toml",
)

ADR_TITLE = re.compile(r"^# ADR-(\d{3}) \(AD-(\d+)\): .+$")


def _rules(path: Path) -> list[str]:
    """Non-empty, non-comment lines of a git-style rule file, stripped."""
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def test_gitattributes_forces_lf_for_golden_files_and_schemas() -> None:
    rules = _rules(REPOSITORY_ROOT / ".gitattributes")
    assert "* text=auto" in rules
    assert "**/tests/golden/** text eol=lf" in rules
    assert "schemas/*.json text eol=lf" in rules


def test_gitignore_lists_every_local_artifact() -> None:
    rules = _rules(REPOSITORY_ROOT / ".gitignore")
    missing = [entry for entry in REQUIRED_IGNORES if entry not in rules]
    assert missing == []


def test_gitignore_keeps_example_traces_trackable() -> None:
    rules = _rules(REPOSITORY_ROOT / ".gitignore")
    assert [rule for rule in rules if "examples" in rule] == []


def test_golden_files_contain_no_carriage_return() -> None:
    files = [path for path in GOLDEN_DIR.rglob("*") if path.is_file()]
    assert files, "tests/golden/ must hold at least the README"
    with_cr = [path.name for path in files if b"\r" in path.read_bytes()]
    assert with_cr == []


def test_decision_records_are_complete() -> None:
    names = sorted(path.name for path in DECISIONS_DIR.iterdir() if path.is_file())
    assert "README.md" in names
    numbered = {name[:4] for name in names if re.match(r"^\d{4}-.+\.md$", name)}
    assert numbered >= {f"{n:04d}" for n in range(22)}  # containment: later ADRs may be added
    assert "0000-distribution-name.md" in names
    assert "0021-license.md" in names


def test_each_adr_file_names_its_adr_id() -> None:
    adr_files = sorted(DECISIONS_DIR.glob("00[0-2][0-9]-*.md"))
    checked = 0
    for path in adr_files:
        number = int(path.name[:4])
        if number < 1 or number > 20:
            continue
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        match = ADR_TITLE.match(first_line)
        assert match is not None, f"{path.name}: {first_line!r}"
        assert int(match.group(1)) == number, path.name
        assert int(match.group(2)) == number, path.name
        checked += 1
    assert checked == 20


def test_decision_index_lists_every_record() -> None:
    index = (DECISIONS_DIR / "README.md").read_text(encoding="utf-8")
    for path in DECISIONS_DIR.glob("[0-9][0-9][0-9][0-9]-*.md"):
        assert path.name in index, path.name


def test_architecture_page_links_the_spine_and_the_decisions() -> None:
    page = (REPOSITORY_ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    assert "architecture-agentproof/architecture-agentproof.md" in page
    assert "decisions/" in page


def test_contributing_states_the_check_command_and_policies() -> None:
    text = (REPOSITORY_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "uv run check" in text
    assert "short-lived" in text
    assert "pull request" in text.lower()
    assert "AD-15" in text
    assert "AD-16" in text
    assert "SECURITY.md" in text


def test_security_policy_names_a_reporting_channel_placeholder() -> None:
    text = (REPOSITORY_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "<security contact to be filled by the maintainer>" in text


def _locked_ruff_version() -> str:
    with (PACKAGE_ROOT / "uv.lock").open("rb") as handle:
        lock = tomllib.load(handle)
    versions = [pkg["version"] for pkg in lock["package"] if pkg["name"] == "ruff"]
    assert len(versions) == 1, versions
    return str(versions[0])


def test_pre_commit_ruff_revision_matches_the_locked_ruff() -> None:
    with (REPOSITORY_ROOT / ".pre-commit-config.yaml").open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    repos = [repo for repo in config["repos"] if repo["repo"].endswith("/ruff-pre-commit")]
    assert len(repos) == 1
    assert repos[0]["rev"] == f"v{_locked_ruff_version()}"
    hook_ids = sorted(hook["id"] for hook in repos[0]["hooks"])
    assert hook_ids == ["ruff-check", "ruff-format"]
    assert all("--fix" not in hook.get("args", []) for hook in repos[0]["hooks"])
