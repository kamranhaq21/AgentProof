"""Canonical form, compact form, and the volatile paths (architecture AD-11).

``dumps`` is the one serialization every written JSON artifact and every determinism
test uses. ``dumps_compact`` is the one-line form that assertions match structured Final
Output against. ``VOLATILE_PATHS`` is the one list of fields that ``compare`` excludes
and golden tests strip. Nothing here touches a file: the caller writes the returned text
as UTF-8 without BOM with ``newline="\\n"`` (the ``io`` package owns that).
"""

import json
from typing import Final

from agentproof.models.common import JsonValue


def dumps(obj: JsonValue) -> str:
    """Return ``obj`` in Canonical form.

    Keys sorted, two-space indent, non-ASCII preserved, a single trailing newline, and
    floats written by their shortest round-trip ``repr``. The text uses ``\\n`` only; two
    calls on equal values return equal text whatever the dict insertion order was.

    Raises ``ValueError`` for NaN or infinity anywhere in ``obj``, so a non-finite number
    is never written to an artifact.
    """
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def dumps_compact(obj: JsonValue) -> str:
    """Return ``obj`` in compact Canonical form: one line, sorted keys, no spaces.

    Non-ASCII is preserved and there is no trailing newline. This is the text
    ``final_output_contains`` matches a structured Final Output against (AD-11, OQ-9).

    Raises ``ValueError`` for NaN or infinity anywhere in ``obj``.
    """
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


VOLATILE_PATHS: Final[tuple[str, ...]] = (
    "run_id",
    "created_at",
    "package_version",
    "scenarios[*].trace.run_id",
    "scenarios[*].trace.started_at",
    "scenarios[*].trace.ended_at",
    "scenarios[*].trace.environment",
    "scenarios[*].trace.events[*].timestamp",
    "scenarios[*].trace.events[*].duration_ms",
    "scenarios[*].duration_ms",
    "scenarios[*].cost",
)
"""Report fields that differ between runs of the same Suite, as path patterns rooted at
the Report (``[*]`` is every list element). ``compare`` excludes exactly these and golden
tests strip exactly these; nothing matches by bare key name."""
