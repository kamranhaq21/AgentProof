"""Typer application behind the ``agentproof`` console script (architecture AD-20).

Only ``version`` exists at this point. The error handler, the exit-code module, and
the remaining commands arrive in later stories; nothing here may grow a second
exit site.
"""

import typer

from agentproof import __version__

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.callback()
def _root() -> None:
    """Test and regression-check tool-using AI agents from saved traces."""
    # An empty callback keeps ``app`` a command group. Without it Typer collapses a
    # single-command app into that command, and ``agentproof version`` would fail
    # with an unexpected extra argument.


@app.command()
def version() -> None:
    """Print the installed AgentProof version."""
    typer.echo(__version__)


def main() -> None:
    """Console-script entry point declared in ``pyproject.toml``."""
    app()
