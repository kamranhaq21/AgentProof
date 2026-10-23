"""The ``version`` command and the root help in-process (story 3.1 criterion 4)."""

from typer.main import get_command
from typer.testing import CliRunner

import agentproof
from agentproof.cli.app import app
from agentproof.cli.commands.version import format_version
from agentproof.constants import SUPPORTED_VERSIONS

runner = CliRunner()

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
    assert "version" in result.stdout


def test_help_lists_the_two_global_options() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--verbose" in result.stdout
    assert "--no-color" in result.stdout
    assert runner.invoke(app, ["--verbose", "--no-color", "version"]).exit_code == 0


def test_global_options_after_the_command_are_a_usage_error_today() -> None:
    """They belong to the root command, so they must precede the command name (standard
    Typer/Click behavior, documented in ``cli/app.py``); pinned so a change is deliberate."""
    for option in ("--verbose", "--no-color"):
        result = runner.invoke(app, ["version", option])
        assert result.exit_code == 2, option
        assert "No such option" in result.output
        assert "Traceback" not in result.output


def test_version_help_documents_the_output_and_exit_code() -> None:
    result = runner.invoke(app, ["version", "--help"])
    assert result.exit_code == 0
    assert "schema versions" in result.stdout
    assert "Exit code: 0" in result.stdout
