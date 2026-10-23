"""``agentproof validate`` as a subprocess (story 3.4 criteria 1 to 4; PRD AC-2.4, AC-28.1/3).

The script is the one installed next to the running interpreter, so the exit codes asserted
here are the ones a shell or a CI job sees. Subprocess rather than ``CliRunner`` for every
case: the story names the subprocess, the cases are few, and the error handler's own unit
tests (``tests/unit/cli/test_error_handler.py``) already cover it in-process. Marked
``allow_subprocess`` (AD-17).

The malformed set is every Suite-shaped fixture of stories 2 and 3: the six
``suite__*.json`` files under ``fixtures/schema/v1/invalid`` (the Trace and Report fixtures
there are not Suites) and the eight rejection files under ``fixtures/yaml``; each yields
exactly one violation, so each must print exactly one line. Two inline Suites cover the
multi-violation case and an unknown Assertion type.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from testsupport import run_captured

pytestmark = pytest.mark.allow_subprocess

SUBPROCESS_TIMEOUT_SECONDS = 120
FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
YAML_FIXTURES = FIXTURES / "yaml"
SCHEMA_INVALID = FIXTURES / "schema" / "v1" / "invalid"

SEED_TEXT = (YAML_FIXTURES / "suite-seed.yaml").read_text(encoding="utf-8")

MALFORMED_FIXTURES = sorted(
    [*SCHEMA_INVALID.glob("suite__*.json"), *(YAML_FIXTURES.glob("*.yaml"))],
    key=lambda path: path.name,
)
MALFORMED_FIXTURES = [path for path in MALFORMED_FIXTURES if path.name != "suite-seed.yaml"]

THREE_FAULTS = """\
suite: demo
extra_field: 1
scenarios:
  - id: a
    input: {}
    trace: a.json
    assertions:
      - type: tool_not_called
        tool: x
  - id: A
    input: {}
    trace: b.json
    assertions:
      - type: tool_not_called
        tool: x
"""

UNKNOWN_ASSERTION_TYPE = """\
version: 1
suite: demo
scenarios:
  - id: a
    input: {}
    assertions:
      - type: no_such_assertion
"""

UNCLOSED_FLOW = "version: 1\nsuite: [demo\n"


def _strip_ansi(text: str) -> str:
    """CI sets GITHUB_ACTIONS, which makes Rich style even piped output."""
    return re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)


def _console_script() -> str:
    found = shutil.which("agentproof", path=str(Path(sys.executable).parent))
    if not found:
        pytest.fail(f"the agentproof console script is not installed next to {sys.executable}")
    return found


def _run(*argv: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run the script with a deterministic environment: no color, no fault injection."""
    base = {
        key: value
        for key, value in os.environ.items()
        if key not in ("AGENTPROOF_TESTING", "AGENTPROOF_FAULT_INJECT")
    }
    return run_captured(
        [_console_script(), *argv],
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
        env={
            **base,
            "NO_COLOR": "1",
            "TERM": "dumb",
            "COLUMNS": "200",
            "PYTHONIOENCODING": "utf-8",
            **(env or {}),
        },
    )


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def test_the_malformed_set_is_the_fourteen_known_fixtures() -> None:
    """Guards the parametrization: a renamed or deleted fixture must not shrink the set."""
    assert len(list(SCHEMA_INVALID.glob("suite__*.json"))) == 6
    assert len(MALFORMED_FIXTURES) == 14


# --- criterion 1: a valid Suite -------------------------------------------------------


def test_the_seed_suite_prints_its_id_and_counts_and_exits_0(tmp_path: Path) -> None:
    path = _write(tmp_path, "agentproof.yaml", SEED_TEXT)
    result = _run("validate", str(path))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["suite expense-agent: 1 scenarios, 3 assertions"]
    assert result.stderr == ""


def test_counts_are_totals_across_scenarios(tmp_path: Path) -> None:
    text = (
        "version: 1\nsuite: two\nscenarios:\n"
        "  - id: a\n    input: {}\n    skip: later\n    assertions:\n"
        "      - {type: tool_not_called, tool: x}\n"
        "  - id: b\n    input: {}\n    assertions:\n"
        "      - {type: tool_not_called, tool: x}\n"
        "      - {type: tool_not_called, tool: y}\n"
    )
    result = _run("validate", str(_write(tmp_path, "two.yaml", text)))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["suite two: 2 scenarios, 3 assertions"]


# --- criterion 2: malformed Suites ----------------------------------------------------


def _assert_input_error(result: subprocess.CompletedProcess[str], lines: int) -> None:
    assert result.returncode == 2, result.stderr
    assert result.stdout == ""
    assert "Traceback" not in result.stderr
    error_lines = result.stderr.splitlines()
    assert len(error_lines) == lines, result.stderr
    for line in error_lines:
        assert re.fullmatch(r"(SuiteError|PathError): .+ \(.+\)", line), line


@pytest.mark.parametrize("fixture", MALFORMED_FIXTURES, ids=lambda path: path.name)
def test_each_malformed_fixture_exits_2_with_one_line_and_no_traceback(fixture: Path) -> None:
    _assert_input_error(_run("validate", str(fixture)), lines=1)


def test_three_violations_print_three_lines(tmp_path: Path) -> None:
    result = _run("validate", str(_write(tmp_path, "three.yaml", THREE_FAULTS)))
    _assert_input_error(result, lines=3)
    fields = [line.rsplit(":", 1)[-1].rstrip(")") for line in result.stderr.splitlines()]
    assert fields == ["extra_field", "scenarios.1.id", "version"]


@pytest.mark.parametrize(
    ("name", "text"),
    [
        ("unknown-assertion.yaml", UNKNOWN_ASSERTION_TYPE),
        ("unclosed-flow.yaml", UNCLOSED_FLOW),
        ("empty.yaml", ""),
    ],
)
def test_other_unusable_suites_exit_2_without_a_traceback(
    tmp_path: Path, name: str, text: str
) -> None:
    result = _run("validate", str(_write(tmp_path, name, text)))
    assert result.returncode == 2, result.stderr
    assert result.stdout == ""
    assert "Traceback" not in result.stderr
    assert result.stderr.splitlines()
    assert all(line.startswith("SuiteError: ") for line in result.stderr.splitlines())


# --- criterion 3: a missing file ------------------------------------------------------


def test_a_missing_file_exits_2_with_one_line_naming_the_path(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.yaml"
    result = _run("validate", str(missing))
    _assert_input_error(result, lines=1)
    assert result.stderr.startswith("PathError: ")
    assert str(missing) in result.stderr


def test_a_directory_is_an_input_error_not_a_crash(tmp_path: Path) -> None:
    result = _run("validate", str(tmp_path))
    assert result.returncode == 2, result.stderr
    assert "Traceback" not in result.stderr
    assert result.stderr.startswith("PathError: ")


# --- criterion 4: help ----------------------------------------------------------------


def _assert_exit_codes_paired(help_text: str) -> None:
    """Each code sits directly before its own meaning, whatever the wrapping."""
    flat = " ".join(help_text.split())
    assert "Exit codes:" in flat, help_text
    codes = flat.split("Exit codes:", 1)[1]
    assert re.search(r"\b0 the Suite is valid\.", codes), help_text
    assert re.search(r"\b2 the file is missing, unreadable, or not a valid Suite", codes), help_text
    assert re.search(r"\b4 internal error\.", codes), help_text
    # In the documented order, and no other digit-led meaning in between.
    assert codes.index("0 the Suite") < codes.index("2 the file") < codes.index("4 internal")


def test_help_lists_the_argument_and_the_exit_codes_0_2_and_4() -> None:
    result = _run("validate", "--help")
    assert result.returncode == 0, result.stderr
    help_text = _strip_ansi(result.stdout)
    assert "SUITE_PATH" in help_text
    _assert_exit_codes_paired(help_text)


def test_help_at_a_narrow_width_still_pairs_each_exit_code_with_its_meaning() -> None:
    """Story 3.1's CI-only bug was a layout that held at 200 columns and broke narrow."""
    result = _run("validate", "--help", env={"COLUMNS": "60"})
    assert result.returncode == 0, result.stderr
    help_text = _strip_ansi(result.stdout)
    assert "SUITE_PATH" in help_text
    _assert_exit_codes_paired(help_text)


def test_the_root_help_lists_validate() -> None:
    result = _run("--help")
    assert result.returncode == 0, result.stderr
    assert "validate" in _strip_ansi(result.stdout)


def test_validate_without_its_argument_is_a_usage_error_with_exit_2() -> None:
    result = _run("validate")
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
