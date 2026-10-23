"""Error taxonomy (architecture AD-7).

This is the only module in the package that defines exception classes; a test scans the
source tree to keep it that way. Everything derives from ``AgentProofError``.
``InputError`` and its subclasses mean the user's input is wrong: the CLI maps them to
exit 2, prints one line per ``Violation``, and shows no traceback. ``ExecutionError`` and
its subclasses mean the run could not produce or persist evidence: exit 3. Anything else
is a bug and reaches the last-resort handler (exit 4). The exit codes themselves live in
``cli.exit_codes`` and are applied by ``cli/app.py`` (AD-6), not here. The module imports
only the standard library.
"""

from dataclasses import dataclass

__all__ = [
    "AdapterLoadError",
    "AdapterRunError",
    "AgentProofError",
    "ArtifactWriteError",
    "ExecutionError",
    "InputError",
    "PathError",
    "SuiteError",
    "TraceFormatError",
    "TraceMissingError",
    "UnsupportedVersionError",
    "Violation",
]


@dataclass(frozen=True)
class Violation:
    """One thing wrong with an input: where it came from, which field, and why.

    ``source`` is the label the shell attached to the text (a file path or ``<stdin>``),
    ``field`` where inside it, and ``message`` one plain sentence. ``field`` is one of
    three things: a 1-based ``line:column`` position in the text (it fully matches
    ``\\d+:\\d+``; set by the YAML loader for faults found before the document is a
    model), the dotted model path (``scenarios.2.id``, list indexes 0-based; set by
    model validation), or empty for the whole document. A text-level fault never has a
    path and a validation fault never has a position. The CLI prints each violation as
    ``<kind>: <message> (<source>:<field>)``.
    """

    source: str
    field: str
    message: str


def _summarize(violations: list[Violation]) -> str:
    """The exception message for a list of violations: the sole text, or a count plus the first."""
    if not violations:
        return "invalid input"
    if len(violations) == 1:
        return violations[0].message
    return f"{len(violations)} violations; first: {violations[0].message}"


class AgentProofError(Exception):
    """Root of every exception AgentProof raises on purpose."""


class InputError(AgentProofError):
    """The user's input is wrong (exit 2): a Suite, Trace, path, or version problem.

    Carries every violation found so the CLI can print them all at once. The exception
    message is the sole violation's text, ``"<n> violations; first: <text>"`` when there
    are several, or ``"invalid input"`` when the list is empty.
    """

    violations: list[Violation]
    """Every violation found, in the order they were detected."""

    def __init__(self, violations: list[Violation]) -> None:
        self.violations = list(violations)
        # ``args`` holds the list itself so ``copy``, ``deepcopy`` and ``pickle`` can rebuild
        # the exception through this constructor; the summary is computed in ``__str__``.
        super().__init__(self.violations)

    def __str__(self) -> str:
        return _summarize(self.violations)


class SuiteError(InputError):
    """A Suite document is malformed or breaks a Suite rule (ids, versions, assertions)."""


class TraceFormatError(InputError):
    """A Trace document named by the user is malformed or breaks a Trace rule."""


class PathError(InputError):
    """A path given on the command line is missing, unreadable, unsafe, or escapes its root."""


class UnsupportedVersionError(InputError):
    """An artifact declares a schema version that ``constants.SUPPORTED_VERSIONS`` lacks."""


class ExecutionError(AgentProofError):
    """The run could not produce or persist evidence (exit 3); the input itself was fine."""


class AdapterLoadError(ExecutionError):
    """The named Adapter could not be found, imported, or instantiated."""


class AdapterRunError(ExecutionError):
    """The Adapter failed while running, or produced a Trace that does not parse."""


class TraceMissingError(ExecutionError):
    """A Trace the Suite or the Adapter was expected to provide does not exist."""


class ArtifactWriteError(ExecutionError):
    """An artifact could not be written atomically to its target path."""
