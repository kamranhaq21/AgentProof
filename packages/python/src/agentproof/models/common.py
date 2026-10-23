"""What every model shares (architecture Consistency Conventions): JSON values, status, and
the one Pydantic configuration and null-handling helper the serialized models use.

The typing names (``JsonValue``, ``Status``) are plain; the models, the assertions, the
serializer, and the engine all import them so that the same value means the same thing in
every module. ``MODEL_CONFIG`` and ``null_means_absent`` live here so that no model module
imports a sibling model module just to reach them. The module imports only the standard
library and Pydantic (AD-1, AD-2).
"""

from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict

type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
"""Any value ``json.loads`` can produce. Numbers compare numerically, a number and a string
never match, and NaN and infinity are rejected by the models and the serializer."""

Status = Literal["passed", "failed", "error", "skipped"]
"""The status of an Assertion, a Scenario, or a Suite; folded only by ``engine.status``."""

STATUSES: Final[tuple[Status, ...]] = ("passed", "failed", "error", "skipped")
"""The ``Status`` values as a runtime tuple, in the order the literal declares them."""

MODEL_CONFIG: Final[ConfigDict] = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)
"""The one model configuration every serialized model uses (AD-3): frozen after
construction, unknown fields rejected naming the field path, NaN and infinity rejected,
and no model-level ``strict`` so Python-mode validation of a dict is the only mode."""


def null_means_absent(model: type[BaseModel], data: Any) -> Any:
    """Drop ``None`` values for fields that have a default, so ``null`` reads as absent.

    AD-19 serializes absent optional fields as ``null``; without this a Trace written with
    the full key set (``"capture": null``, ``"metadata": null``) would not read back.
    Only dict input is touched, and only keys that name a field with a default are
    dropped, so a ``null`` for a required field and an unknown key keep their normal
    errors. Used as a ``model_validator(mode="before")`` by the models that call it.
    """
    if not isinstance(data, dict):
        return data
    fields = model.model_fields
    return {
        key: value
        for key, value in data.items()
        if not (value is None and key in fields and not fields[key].is_required())
    }
