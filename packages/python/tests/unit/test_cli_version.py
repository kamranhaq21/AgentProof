"""The ``version`` command in-process, covering the dev-environment matrix row."""

from typer.main import get_command
from typer.testing import CliRunner

import agentproof
from agentproof.cli.app import app

runner = CliRunner()


def test_version_command_prints_package_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.output.strip() == agentproof.__version__


def test_help_lists_only_version_command() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    # CommandInfo.name is None until Typer derives it from the function name while
    # building the Click group, so assert on the built group's command set.
    assert list(get_command(app).commands) == ["version"]
