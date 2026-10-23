"""Types every model shares (architecture Consistency Conventions): JSON values and status.

No Pydantic here. These are plain typing names that the models, the assertions, the
serializer, and the engine all import so that the same value means the same thing in
every module. The module imports only the standard library (AD-1, AD-2).
"""

from typing import Final, Literal

type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
"""Any value ``json.loads`` can produce. Numbers compare numerically, a number and a string
never match, and NaN and infinity are rejected by the models and the serializer."""

Status = Literal["passed", "failed", "error", "skipped"]
"""The status of an Assertion, a Scenario, or a Suite; folded only by ``engine.status``."""

STATUSES: Final[tuple[Status, ...]] = ("passed", "failed", "error", "skipped")
"""The ``Status`` values as a runtime tuple, in the order the literal declares them."""
