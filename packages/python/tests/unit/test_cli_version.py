"""The ``version`` command and the root help in-process (story 3.1 criterion 4)."""

import re

from typer.main import get_command
from typer.testing import CliRunner

import agentproof
from agentproof.cli.app import app
from agentproof.cli.commands.version import format_version
from agentproof.constants import SUPPORTED_VERSIONS

runner = CliRunner()

_ANSI = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def _strip_ansi(text: str) -> str:
    """CI sets GITHUB_ACTIONS, which makes Rich emit styling even into captured output, so
    help-text assertions look at the text with the escape sequences removed."""
    return _ANSI.sub("", text)


EXPECTED_LINES = [
    f"agentproof {agentproof.__version__}",
    "suite schema versions: 1",
    "trace schema versions: 1",
    "report schema versions: 1",
]


def test_version_command_prints_package_version_and_supported_schema_versions() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.splitlines() == EXPECTED_LINES
    assert result.stderr == ""


def test_version_text_follows_the_documented_four_line_format() -> None:
    """The format is a contract: first the package version, then one line per kind."""
    assert format_version(agentproof.__version__, SUPPORTED_VERSIONS) == "\n".join(EXPECTED_LINES)
    several = format_version("9.9.9", {"suite": (2, 1), "trace": (1,), "report": (1, 3)})
    assert several.splitlines() == [
        "agentproof 9.9.9",
        "suite schema versions: 1, 2",
        "trace schema versions: 1",
        "report schema versions: 1, 3",
    ]


def test_help_lists_only_version_command() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    # CommandInfo.name is None until Typer derives it from the function name while
    # building the Click group, so assert on the built group's command set.
    assert list(get_command(app).commands) == ["version"]
    assert "version" in _strip_ansi(result.stdout)


def test_help_lists_the_two_global_options() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    help_text = _strip_ansi(result.stdout)
    assert "--verbose" in help_text
    assert "--no-color" in help_text
    assert runner.invoke(app, ["--verbose", "--no-color", "version"]).exit_code == 0


def test_global_options_after_the_command_are_a_usage_error_today() -> None:
    """They belong to the root command, so they must precede the command name (standard
    Typer/Click behavior, documented in ``cli/app.py``); pinned so a change is deliberate."""
    for option in ("--verbose", "--no-color"):
        result = runner.invoke(app, ["version", option])
        assert result.exit_code == 2, option
        assert "No such option" in _strip_ansi(result.output)
        assert "Traceback" not in result.output


def test_version_help_documents_the_output_and_exit_code() -> None:
    result = runner.invoke(app, ["version", "--help"])
    assert result.exit_code == 0
    help_text = _strip_ansi(result.stdout)
    assert "schema versions" in help_text
    assert "Exit code: 0" in help_text


def test_version_short_help_is_short_enough_never_to_wrap_in_the_command_list() -> None:
    """The first docstring line is the command-list description; keep it under 60 chars."""
    summary = get_command(app).commands["version"].get_short_help_str(limit=1000)
    assert len(summary) < 60, summary
