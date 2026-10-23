"""The one exit-code module (architecture AD-6; PRD FR-27).

This module defines the five exit codes exactly once, as named constants, and two pure
functions that turn what the core produced into one of them, so the public API and the
CLI cannot disagree about a result. ``cli/app.py`` applies the codes (it is the only
module that exits) and imports the constants from here; no literal code is repeated
there. The codes, in precedence order (PRD AC-27.4): 4 internal error, 2 invalid input,
3 execution failure, 1 assertion failure or nothing evaluated, 0 success.

``__all__`` is the two functions the architecture names (``from_outcome`` and
``from_comparison``); the ``EXIT_*`` constants are module attributes for ``cli/app.py``.
"""

from typing import Final

from agentproof.models.report import Comparison
from agentproof.models.result import SuiteOutcome

__all__ = ["from_comparison", "from_outcome"]

EXIT_OK: Final = 0
"""Every non-skipped Assertion passed and at least one was evaluated."""

EXIT_FAILED: Final = 1
"""An Assertion failed or errored, nothing was evaluated, or a Comparison regressed."""

EXIT_INPUT_ERROR: Final = 2
"""The user's input is wrong: an ``InputError`` (and click's own usage errors)."""

EXIT_EXECUTION_ERROR: Final = 3
"""The run could not produce or persist evidence: an ``ExecutionError`` or ``execution_failed``."""

EXIT_INTERNAL_ERROR: Final = 4
"""Any other exception: a bug."""


def from_outcome(outcome: SuiteOutcome) -> int:
    """The exit code for a ``SuiteOutcome`` (AD-6; PRD AC-18.5, AC-27.2, AC-27.3).

    3 when any Scenario carries an execution error (``execution_failed``), whatever the
    Assertion Results say; else 1 when the Suite Status is ``failed`` or ``error`` or no
    Assertion was evaluated (every Scenario skipped); else 0. The outcome is trusted as
    ``engine.fold`` produced it; nothing is re-derived here.
    """
    if outcome.execution_failed:
        return EXIT_EXECUTION_ERROR
    if outcome.suite_status in ("failed", "error") or outcome.evaluated_assertions == 0:
        return EXIT_FAILED
    return EXIT_OK


def from_comparison(comparison: Comparison) -> int:
    """The exit code for a ``Comparison`` (PRD AC-26.4): 1 when it regressed, else 0.

    ``compare`` decides ``regressed`` (a Scenario went from ``passed`` to ``failed`` or
    ``error``); improvements and sequence-only changes are reported but do not fail.
    """
    return EXIT_FAILED if comparison.regressed else EXIT_OK
