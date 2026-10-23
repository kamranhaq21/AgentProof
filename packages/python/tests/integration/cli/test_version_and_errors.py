"""The ``agentproof`` console script as a subprocess: version, help, usage errors, and the
fault-injection pair (story 3.1 criteria 4 and 5; PRD AC-27.1, AC-30.2; AD-17).

The script is the one installed next to the running interpreter (``uv sync`` installs
the project editable, console script included), so the exit codes asserted here are the
ones a shell or a CI job sees, not ``CliRunner``'s. Marked ``allow_subprocess``: this
module is one of the few allowed to spawn a process (AD-17).
"""

import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.allow_subprocess

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
SUBPROCESS_TIMEOUT_SECONDS = 120

TESTING = "AGENTPROOF_TESTING"
FAULT_INJECT = "AGENTPROOF_FAULT_INJECT"


def _strip_ansi(text: str) -> str:
    """CI sets GITHUB_ACTIONS, which makes Rich style even piped output."""
    return re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)


def _console_script() -> str:
    found = shutil.which("agentproof", path=str(Path(sys.executable).parent))
    if not found:
        pytest.fail(f"the agentproof console script is not installed next to {sys.executable}")
    return found


def _pyproject_version() -> str:
    with (PACKAGE_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def _run(*argv: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run the script with a deterministic environment: no color, no inherited fault flags."""
    base = {key: value for key, value in os.environ.items() if key not in (TESTING, FAULT_INJECT)}
    return subprocess.run(
        [_console_script(), *argv],
        env={
            **base,
            "NO_COLOR": "1",
            "TERM": "dumb",
            "COLUMNS": "200",
            "PYTHONIOENCODING": "utf-8",
            **(env or {}),
        },
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
        check=False,
    )


def test_version_prints_the_version_and_schema_versions_and_exits_0() -> None:
    result = _run("version")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        f"agentproof {_pyproject_version()}",
        "suite schema versions: 1",
        "trace schema versions: 1",
        "report schema versions: 1",
    ]
    assert result.stderr == ""


def test_help_lists_version_and_the_global_options_and_exits_0() -> None:
    result = _run("--help")
    assert result.returncode == 0, result.stderr
    help_text = _strip_ansi(result.stdout)
    assert "version" in help_text
    assert "--verbose" in help_text
    assert "--no-color" in help_text


def test_no_color_version_has_no_escape_sequence() -> None:
    result = _run("--no-color", "version", env={"FORCE_COLOR": "1"})
    assert result.returncode == 0, result.stderr
    assert "\x1b" not in result.stdout + result.stderr


def test_an_unknown_command_is_a_usage_error_with_exit_2_and_no_traceback() -> None:
    result = _run("validate", "x.yaml")
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "validate" in _strip_ansi(result.stderr)


@pytest.mark.parametrize("option", ["--verbose", "--no-color"])
def test_a_global_option_after_the_command_is_a_usage_error_with_exit_2(option: str) -> None:
    """The global options precede the command (documented in cli/app.py); pinned today."""
    result = _run("version", option)
    assert result.returncode == 2
    assert result.stdout == ""
    assert "Traceback" not in result.stderr


def test_fault_injection_makes_version_exit_4_with_one_line() -> None:
    result = _run("version", env={TESTING: "1", FAULT_INJECT: "cli.version"})
    assert result.returncode == 4
    assert result.stdout == ""
    assert result.stderr.splitlines() == [
        "internal error: RuntimeError: injected fault at cli.version "
        "(re-run with --verbose for the traceback)"
    ]


def test_fault_injection_with_verbose_adds_the_traceback() -> None:
    result = _run("--verbose", "version", env={TESTING: "1", FAULT_INJECT: "cli.version"})
    assert result.returncode == 4
    lines = result.stderr.splitlines()
    assert lines[0] == "internal error: RuntimeError: injected fault at cli.version"
    assert lines[1] == "Traceback (most recent call last):"
    assert lines[-1] == "RuntimeError: injected fault at cli.version"


def test_the_fault_variable_is_ignored_without_agentproof_testing() -> None:
    result = _run("version", env={FAULT_INJECT: "cli.version"})
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith(f"agentproof {_pyproject_version()}\n")
    assert result.stderr == ""


@pytest.mark.parametrize("testing", ["0", "true", "yes", ""])
def test_only_the_exact_value_1_enables_fault_injection(testing: str) -> None:
    result = _run("version", env={TESTING: testing, FAULT_INJECT: "cli.version"})
    assert result.returncode == 0, result.stderr


def test_another_fault_point_leaves_version_alone() -> None:
    result = _run("version", env={TESTING: "1", FAULT_INJECT: "cli.validate"})
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
