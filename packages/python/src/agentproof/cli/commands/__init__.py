"""The CLI commands, one module each, and the test-only fault-injection hook.

A command module defines a plain function; ``cli/app.py`` wraps it in the error handler
and registers it, so no command module ends the process itself (AD-6: ``cli/app.py`` is
the only exit site, and an AST test over this package keeps it so). The commands import
nothing from ``cli/app.py`` (it imports them).

``inject_fault`` is the only fault-injection hook in the package (architecture AD-17;
PRD AC-27.1). It is how the test suite reaches exit 4 through the real CLI. It reads two
environment variables and does nothing unless both are set to the expected values, so
it is unreachable in normal use: ``AGENTPROOF_TESTING=1`` enables it at all, and
``AGENTPROOF_FAULT_INJECT`` names the one injection point to trip. The ``cli`` package is
part of the effectful shell (AD-1), so reading the environment here is allowed; no core
module may call this, and a test scans the source tree to keep it so.
"""

import os

__all__ = ["inject_fault"]

TESTING_VARIABLE = "AGENTPROOF_TESTING"
"""Set to ``1`` to enable fault injection at all; anything else leaves it off."""

FAULT_INJECT_VARIABLE = "AGENTPROOF_FAULT_INJECT"
"""The injection point to trip, such as ``cli.version``; ignored unless testing is on."""


def inject_fault(point: str) -> None:
    """Raise ``RuntimeError`` at ``point`` when the environment asks for it; else return.

    Both ``AGENTPROOF_TESTING`` (exactly ``1``) and ``AGENTPROOF_FAULT_INJECT`` (exactly
    ``point``) must be set. The error is a plain ``RuntimeError`` so it reaches the
    last-resort handler like any other bug would (exit 4); ``errors.py`` is the only
    module that defines exception classes (AD-7).
    """
    if os.environ.get(TESTING_VARIABLE) != "1":
        return
    if os.environ.get(FAULT_INJECT_VARIABLE) != point:
        return
    raise RuntimeError(f"injected fault at {point}")
