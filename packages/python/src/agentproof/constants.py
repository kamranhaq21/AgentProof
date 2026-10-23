"""Package-wide constants (architecture Structural Seed; AD-3, AD-10, AD-14, AD-19, AD-20).

Every rule that more than one module needs lives here exactly once: the schema versions a
reader accepts, the scenario id charset and the Windows device names, the timestamp
grammar, the redaction marker, the input size limits, and the fixed user-facing
statements that the CLI, the Report, and the docs reuse so the product's claims cannot
drift apart. The module imports only the standard library (AD-1, AD-2).
"""

import re
from dataclasses import dataclass
from typing import Final

SUPPORTED_VERSIONS: Final[dict[str, tuple[int, ...]]] = {
    "suite": (1,),
    "trace": (1,),
    "report": (1,),
}
"""Schema versions each artifact kind accepts (AD-3); any other version is unsupported."""

SCENARIO_ID_RE: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
"""Scenario id charset (AD-14): 1 to 64 characters from letters, digits, ``.``, ``_`` and
``-``, not starting with punctuation. Match with ``fullmatch``. Device names are a
separate check that ``models.suite`` makes against ``WINDOWS_DEVICE_NAMES``."""

WINDOWS_DEVICE_NAMES: Final[frozenset[str]] = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "CONIN$",
        "CONOUT$",
        *(f"COM{digit}" for digit in range(10)),
        *(f"LPT{digit}" for digit in range(10)),
    }
)
"""Reserved Windows device names, upper case (AD-14); callers compare the upper-cased id."""

RFC3339_WITH_OFFSET: Final[re.Pattern[str]] = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,9})?(Z|[+-][0-9]{2}:[0-9]{2})"
)
"""RFC 3339 timestamp with an explicit offset or ``Z`` (AD-3); a naive timestamp does not
match. ``[0-9]`` rather than ``\\d``, which would also accept fullwidth and other Unicode
digits. Match with ``fullmatch``; the string is stored as given, never normalized."""

REDACTED: Final = "[REDACTED]"
"""The one redaction marker written in place of a scrubbed value (AD-10)."""

MAX_SUITE_BYTES: Final = 5 * 1024 * 1024
"""Largest Suite file the shell reads before parsing (AD-19; OQ-12: 5 MB)."""

MAX_TRACE_BYTES: Final = 5 * 1024 * 1024
"""Largest Trace file the shell reads before parsing (AD-19; OQ-12: 5 MB)."""

MAX_REPORT_BYTES: Final = 5 * 1024 * 1024
"""Largest Report file the shell reads before parsing (AD-19; OQ-12: 5 MB)."""

MAX_YAML_NODES: Final = 200_000
"""Most YAML nodes (every scalar, sequence and mapping) one Suite document may hold
(AD-19). A hand-written Suite of 100 Scenarios with 10 Assertions each is under 10,000
nodes; this is twenty times that, and it bounds the time and memory the pure-Python
loader can spend on a document that stays under ``MAX_SUITE_BYTES`` without aliases."""


@dataclass(frozen=True)
class Statements:
    """The fixed user-facing statements (AD-20), one plain sentence per field.

    They are string constants rather than prose repeated in the CLI, the Report, and the
    docs so that every surface states the same limit in the same words.
    """

    compare_is_saved_data: str
    """PRD AC-26.6: what a Comparison is and is not."""

    redaction_limits: str
    """PRD AC-31.4: what Redaction covers and what the user must still do."""

    capture_limited: str
    """PRD AC-12.4: the absence-proof caveat when a Trace's Capture is partial or unknown,
    for ``tool_not_called`` and for ``tool_call_count`` with ``less_than`` alike. Appended
    after ``capture_declaration``."""

    capture_declaration: str
    """PRD AC-12.4, AD-20: the Capture declaration label, a format string with one field,
    ``{tool_calls}``. The engine's result messages and the Report format it with the
    Trace's ``capture.tool_calls`` value so both show the same label."""

    limits_v01: str
    """PRD AC-33.3 and section 5: the v0.1 limits the README states."""

    artifacts_visible_to_readers: str
    """PRD AC-32.3: who can see artifacts uploaded from a CI run."""


STATEMENTS: Final[Statements] = Statements(
    compare_is_saved_data=(
        "This is an exact comparison of saved data; it says nothing about whether the "
        "agent would behave the same way if run again."
    ),
    redaction_limits=(
        "Redaction replaces only the configured keys and the declared environment values, "
        "assertions evaluate the redacted trace, and you must inspect artifacts before "
        "sharing them."
    ),
    capture_limited=(
        "The trace does not declare complete capture, so this absence proof is limited to "
        "what the adapter observed."
    ),
    capture_declaration="capture: {tool_calls}",
    limits_v01=(
        "AgentProof does not reproduce stochastic agent runs, does not enforce policy at "
        "runtime, and redacts only configured keys and declared environment values."
    ),
    artifacts_visible_to_readers=(
        "Artifacts uploaded from a CI run are visible to anyone with read access to the "
        "repository's Actions."
    ),
)
"""The single instance every CLI command, Report renderer, and documentation page quotes."""
