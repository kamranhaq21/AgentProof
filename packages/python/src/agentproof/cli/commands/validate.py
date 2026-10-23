"""``agentproof validate SUITE_PATH`` (architecture AD-20; PRD FR-2, AC-2.4, AC-28.1, AC-28.3).

Reads one Suite file with ``runner.load_suite`` (size limit, symlink policy, safe YAML,
every violation at once) and, when it is valid, prints one fixed line on stdout:

.. code-block:: text

    suite <id>: <n> scenarios, <m> assertions

``<n>`` is the number of Scenarios and ``<m>`` the number of Assertions across all of
them, skipped Scenarios included (``validate`` evaluates nothing). The nouns are always
plural so a script can match the line with one pattern. The format is part of the CLI
contract. Nothing is printed on stdout when the Suite is invalid.

A malformed Suite or an unreadable path raises ``SuiteError`` or ``PathError``; both are
``InputError`` and the shared handler in ``cli/app.py`` prints one line per violation on
stderr and exits 2. This module neither catches nor prints errors.
"""

from pathlib import Path
from typing import Annotated

import typer

from agentproof.models.suite import Suite
from agentproof.runner.suite_file import load_suite

__all__ = ["format_summary", "validate"]


def format_summary(suite: Suite) -> str:
    """The exact text ``validate`` prints for a valid Suite, without a trailing newline. Pure."""
    scenarios = len(suite.scenarios)
    assertions = sum(len(scenario.assertions) for scenario in suite.scenarios)
    return f"suite {suite.suite}: {scenarios} scenarios, {assertions} assertions"


def validate(
    suite_path: Annotated[
        Path,
        typer.Argument(metavar="SUITE_PATH", help="Path to the Suite YAML file to check."),
    ],
) -> None:
    """Check that a Suite file is valid, without running anything.

    Reads SUITE_PATH and reports every problem in one pass.
    On success prints "suite <id>: <n> scenarios, <m> assertions".

    Exit codes:
    0 the Suite is valid.
    2 the file is missing, unreadable, or not a valid Suite
    (one line per problem on stderr, no traceback).
    4 internal error.
    """
    typer.echo(format_summary(load_suite(suite_path)))
