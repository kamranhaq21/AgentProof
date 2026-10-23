"""``agentproof version`` (architecture AD-20; PRD AC-30.2).

Prints the installed package version and the Schema Versions this build accepts for
each artifact kind, as fixed plain text:

.. code-block:: text

    agentproof <package version>
    suite schema versions: <n>[, <n>...]
    trace schema versions: <n>[, <n>...]
    report schema versions: <n>[, <n>...]

The first line is the package version; the next three are the supported versions of
``constants.SUPPORTED_VERSIONS`` for ``suite``, ``trace``, and ``report`` in that order,
ascending and comma-separated when there are several. The format is part of the CLI
contract; scripts may rely on it. There is no JSON form (AD-20 names none).
"""

from collections.abc import Mapping

import typer

from agentproof import __version__
from agentproof.cli.commands import inject_fault
from agentproof.constants import SUPPORTED_VERSIONS

__all__ = ["format_version", "version"]

ARTIFACT_KINDS: tuple[str, ...] = ("suite", "trace", "report")
"""The artifact kinds listed, in output order."""

FAULT_POINT = "cli.version"
"""The fault-injection point of this command (``AGENTPROOF_FAULT_INJECT=cli.version``)."""


def format_version(package_version: str, supported_versions: Mapping[str, tuple[int, ...]]) -> str:
    """The exact text ``version`` prints, without a trailing newline. Pure."""
    lines = [f"agentproof {package_version}"]
    for kind in ARTIFACT_KINDS:
        numbers = ", ".join(str(number) for number in sorted(supported_versions[kind]))
        lines.append(f"{kind} schema versions: {numbers}")
    return "\n".join(lines)


def version() -> None:
    """Print the package version and the supported Suite, Trace, and Report schema versions.

    Output, one item per line: "agentproof <version>", then "suite schema versions: ...",
    "trace schema versions: ...", "report schema versions: ...". Exit code: 0.
    """
    inject_fault(FAULT_POINT)
    typer.echo(format_version(__version__, SUPPORTED_VERSIONS))
