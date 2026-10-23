"""``runner.suite_file.load_suite``: read with the size limit, then ``parse_suite`` (AD-15)."""

from pathlib import Path

import pytest

from agentproof import constants, load_suite, parse_suite
from agentproof.errors import PathError, SuiteError
from agentproof.runner import suite_file

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "yaml"
SEED_TEXT = (FIXTURES / "suite-seed.yaml").read_text(encoding="utf-8")

# No ``version`` and an unknown top-level field: two violations.
TWO_FAULTS = "suite: demo\nextra_field: 1\nscenarios: []\n"


def test_load_suite_reads_the_seed_file_and_sets_source_to_the_path(tmp_path: Path) -> None:
    target = tmp_path / "agentproof.yaml"
    target.write_text(SEED_TEXT, encoding="utf-8", newline="\n")
    assert load_suite(target) == parse_suite(SEED_TEXT, source=str(target))


def test_load_suite_violations_carry_the_path_as_source(tmp_path: Path) -> None:
    target = tmp_path / "agentproof.yaml"
    target.write_text(TWO_FAULTS, encoding="utf-8", newline="\n")
    with pytest.raises(SuiteError) as error:
        load_suite(target)
    assert len(error.value.violations) >= 2
    assert {violation.source for violation in error.value.violations} == {str(target)}


def test_load_suite_defaults_base_dir_to_the_files_directory(tmp_path: Path) -> None:
    outside = tmp_path / "outside.yaml"
    outside.write_text(SEED_TEXT, encoding="utf-8", newline="\n")
    inside = tmp_path / "suite"
    inside.mkdir()
    link = inside / "agentproof.yaml"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("this environment cannot create symlinks")
    with pytest.raises(PathError):
        load_suite(link)
    assert load_suite(link, base_dir=tmp_path) == parse_suite(SEED_TEXT, source=str(link))


def test_load_suite_uses_the_suite_size_limit_constant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[int] = []

    def fake(path: Path, max_bytes: int, *, base_dir: Path) -> str:
        seen.append(max_bytes)
        return SEED_TEXT

    monkeypatch.setattr(suite_file, "read_limited", fake)
    load_suite(tmp_path / "x.yaml")
    assert seen == [constants.MAX_SUITE_BYTES]
