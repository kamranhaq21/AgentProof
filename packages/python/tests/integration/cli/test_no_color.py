"""``--no-color`` and ``--verbose`` end to end through the installed script (story 3.5
criterion 4; AD-20). Marked ``allow_subprocess`` (AD-17)."""

import os
import shutil
import sys
from pathlib import Path

import pytest

from testsupport import run_captured

pytestmark = pytest.mark.allow_subprocess

TESTING = "AGENTPROOF_TESTING"
FAULT_INJECT = "AGENTPROOF_FAULT_INJECT"


def _script() -> str:
    found = shutil.which("agentproof", path=str(Path(sys.executable).parent))
    if not found:
        pytest.fail(f"the agentproof console script is not installed next to {sys.executable}")
    return found


def _run(*argv: str, fault: bool = False) -> tuple[int, str]:
    base = {k: v for k, v in os.environ.items() if k not in (TESTING, FAULT_INJECT)}
    # Ask for color three ways; --no-color must still win.
    env = {**base, "FORCE_COLOR": "1", "CLICOLOR_FORCE": "1", "TERM": "xterm-256color"}
    env.pop("NO_COLOR", None)
    if fault:
        env.update({TESTING: "1", FAULT_INJECT: "cli.version"})
    result = run_captured([_script(), *argv], timeout=120, env=env)
    return result.returncode, result.stdout + result.stderr


def test_no_color_exit_4_with_traceback_has_no_escape_sequences() -> None:
    code, output = _run("--no-color", "--verbose", "version", fault=True)
    assert code == 4
    assert "Traceback (most recent call last):" in output
    assert "\x1b" not in output


def test_no_color_usage_error_and_version_have_no_escape_sequences() -> None:
    code, output = _run("--no-color", "version", "--verbose")
    assert code == 2
    assert "\x1b" not in output
    code, output = _run("--no-color", "version")
    assert code == 0
    assert "\x1b" not in output


def test_verbose_diagnostics_appear_only_for_exit_3_and_4() -> None:
    # exit 4: hint without --verbose, traceback with it.
    code, output = _run("version", fault=True)
    assert code == 4
    assert "Traceback" not in output
    assert "--verbose" in output
    code, output = _run("--verbose", "version", fault=True)
    assert code == 4
    assert "Traceback (most recent call last):" in output
    # exit 0 and exit 2: nothing extra under --verbose.
    code, output = _run("--verbose", "version")
    assert code == 0
    assert "Traceback" not in output
    code, output = _run("--verbose", "version", "--bogus")
    assert code == 2
    assert "Traceback" not in output
