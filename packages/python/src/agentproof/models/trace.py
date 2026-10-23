"""The Trace data contract (architecture AD-3, AD-5, AD-9, AD-10; PRD FR-5).

A Trace is the integration surface for every stack: whatever an adapter, the Fixture
Agent, or a user's exported file produces is validated by these models, so the rules that
make a Trace trustworthy live here and on no loader. Every model is frozen and rejects
unknown fields; ``strict`` mode is not used (AD-3). The rules this module enforces:

* ``version`` is an exact integer listed in ``constants.SUPPORTED_VERSIONS["trace"]``;
  ``"1"``, ``1.0`` and ``true`` are rejected (AD-3).
* ``events[i].seq == i``: a 0-based contiguous sequence with no gap, duplicate, or
  disorder, checked on the Trace so every path into a ``Trace`` object enforces it
  (AD-5, ARCH-3). The error is located at ``events.<index>.seq``.
* Timestamps are strings matching ``constants.RFC3339_WITH_OFFSET`` (an explicit offset
  or ``Z``) and are stored exactly as given, never normalized (AD-3).
* ``capture`` defaults to ``Capture(tool_calls="unknown")`` and ``redaction`` to a state
  that was never applied; ``environment`` accepts only the four allowlisted keys (AD-9,
  AD-10; PRD AC-5.5, AC-5.6, AC-31.2).
* A ``null`` for a field that has a default means the same as leaving the key out
  (AD-19: absent optional fields are serialized as ``null``), so a file written with the
  full key set reads back identically. A ``null`` for a required field is still an error.
* NaN and infinity are rejected anywhere inside ``arguments``, ``result``, ``output`` and
  ``metadata`` (Consistency Conventions), so no artifact ever carries a non-finite number.

Validation failures are Pydantic ``ValidationError``s whose locations name the field path
and whose ``type`` codes are stable (``unsupported_version``, ``integer_required``,
``timestamp_type``, ``timestamp_format``, ``seq_not_contiguous``, ``finite_number`` plus
Pydantic's own); ``loading.parse_trace`` keys on them, preferring ``unsupported_version``
when it appears, and turns the rest into ``TraceFormatError`` violations.

Frozen is shallow, as Pydantic defines it: attributes cannot be reassigned, but a value a
field holds is only as immutable as its type. Sequence fields (``events``,
``redaction.paths``, ``redaction.env_names``) are therefore tuples, decided once for the
Trace and Suite models together: JSON arrays validate into them, ``model_dump(mode="json")``
and the JSON Schema still show arrays, and a Trace with no events is hashable. Mapping and
``JsonValue`` fields (``metadata``, ``arguments``, ``result``, ``output``) are not
deep-frozen; they keep whatever lists and dicts the input had, and because every event's
``metadata`` is a dict, a Trace with at least one event is not hashable.

The module performs no I/O and imports only the standard library, Pydantic, ``constants``
and ``models.common`` (AD-1, AD-2).
"""

import math
from typing import Annotated, Any, Final, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_core import InitErrorDetails, PydanticCustomError

from agentproof.constants import RFC3339_WITH_OFFSET, SUPPORTED_VERSIONS
from agentproof.models.common import JsonValue

__all__ = [
    "EVENT_TYPES",
    "AdapterInfo",
    "AgentInfo",
    "Capture",
    "CaptureLevel",
    "Environment",
    "EventError",
    "EventType",
    "ModelInfo",
    "RedactionState",
    "Timestamp",
    "ToolRef",
    "Trace",
    "TraceEvent",
    "TraceSchemaVersion",
]

EventType = Literal[
    "agent_started",
    "agent_finished",
    "tool_call",
    "tool_result",
    "llm_request",
    "llm_response",
    "exception",
    "approval_requested",
    "approval_granted",
    "approval_denied",
    "custom",
]
"""The eleven documented event types (spine Schemas seed; PRD AC-5.2); any other is rejected."""

EVENT_TYPES: Final[tuple[EventType, ...]] = (
    "agent_started",
    "agent_finished",
    "tool_call",
    "tool_result",
    "llm_request",
    "llm_response",
    "exception",
    "approval_requested",
    "approval_granted",
    "approval_denied",
    "custom",
)
"""The ``EventType`` values as a runtime tuple, in the order the literal declares them."""

CaptureLevel = Literal["complete", "partial", "unknown"]
"""How much of the agent's tool activity the adapter declares it observed (AD-5, AC-12.4)."""


def _require_integer(value: object) -> object:
    """Accept only a real ``int``: no ``bool``, no numeric string, no whole float.

    Pydantic's lax mode would coerce ``"1"``, ``1.0`` and ``True`` to ``1``; a JSON data
    contract carries integers as integers, so those are rejected (AD-3).
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise PydanticCustomError(
            "integer_required",
            "Input should be an integer, not {kind}",
            {"kind": type(value).__name__},
        )
    return value


def _require_supported_trace_version(value: int) -> int:
    """Accept only a version listed in ``SUPPORTED_VERSIONS["trace"]`` (AD-3)."""
    supported = SUPPORTED_VERSIONS["trace"]
    if value not in supported:
        raise PydanticCustomError(
            "unsupported_version",
            "Trace schema version {given} is not supported; supported versions: {supported}",
            {"given": value, "supported": ", ".join(str(number) for number in supported)},
        )
    return value


def _require_timestamp(value: object) -> str:
    """Accept only a string that ``RFC3339_WITH_OFFSET`` matches in full; return it as given.

    A naive timestamp, a timestamp with a space instead of ``T``, and any non-string
    (including a ``datetime`` object or an epoch number) are rejected (AD-3; PRD AC-5.3).
    """
    if not isinstance(value, str):
        raise PydanticCustomError(
            "timestamp_type",
            "Input should be an RFC 3339 timestamp string with an explicit UTC offset, not {kind}",
            {"kind": type(value).__name__},
        )
    if RFC3339_WITH_OFFSET.fullmatch(value) is None:
        raise PydanticCustomError(
            "timestamp_format",
            "Input should be an RFC 3339 timestamp with an explicit UTC offset or Z, "
            "such as 2026-10-22T13:05:00+00:00",
        )
    return value


def _first_non_finite(value: JsonValue, path: str) -> tuple[str, float] | None:
    """Return the dotted path and value of the first NaN or infinity inside ``value``."""
    if isinstance(value, float):
        return None if math.isfinite(value) else (path, value)
    if isinstance(value, list):
        for index, item in enumerate(value):
            found = _first_non_finite(item, f"{path}.{index}" if path else str(index))
            if found is not None:
                return found
    elif isinstance(value, dict):
        for key, item in value.items():
            found = _first_non_finite(item, f"{path}.{key}" if path else key)
            if found is not None:
                return found
    return None


def _require_finite[T: JsonValue](value: T) -> T:
    """Reject NaN and infinity at any depth; the message names the path inside the value."""
    found = _first_non_finite(value, "")
    if found is not None:
        path, number = found
        raise PydanticCustomError(
            "finite_number",
            "Input should contain only finite numbers; found {number} at {path}",
            {"number": str(number), "path": path or "the value itself"},
        )
    return value


def _null_means_absent(model: type[BaseModel], data: Any) -> Any:
    """Drop ``None`` values for fields that have a default, so ``null`` reads as absent.

    AD-19 serializes absent optional fields as ``null``; without this a Trace written with
    the full key set (``"capture": null``, ``"metadata": null``) would not read back.
    Only dict input is touched, and only keys that name a field with a default are
    dropped, so a ``null`` for a required field and an unknown key keep their normal
    errors. Used as a ``model_validator(mode="before")`` by ``Trace`` and ``TraceEvent``;
    the Suite models may hoist it later.
    """
    if not isinstance(data, dict):
        return data
    fields = model.model_fields
    return {
        key: value
        for key, value in data.items()
        if not (value is None and key in fields and not fields[key].is_required())
    }


TraceSchemaVersion = Annotated[
    int, BeforeValidator(_require_integer), AfterValidator(_require_supported_trace_version)
]
"""An exact integer that ``SUPPORTED_VERSIONS["trace"]`` lists (AD-3)."""

Timestamp = Annotated[str, BeforeValidator(_require_timestamp)]
"""An RFC 3339 string with an explicit offset or ``Z``, stored exactly as given (AD-3)."""

# ``Field(ge=0)`` sits before the validator so the constraint lands on the integer schema
# and exports as JSON Schema ``minimum``; the validator still runs first on input.
_NonNegativeInt = Annotated[int, Field(ge=0), BeforeValidator(_require_integer)]
_FiniteJsonValue = Annotated[JsonValue, AfterValidator(_require_finite)]
_FiniteJsonObject = Annotated[dict[str, JsonValue], AfterValidator(_require_finite)]


class ToolRef(BaseModel):
    """The tool a ``tool_call`` or ``tool_result`` event refers to (AD-5).

    ``call_id`` links a result to its call when the adapter provides one; without it the
    engine links a result to the nearest preceding ``tool_call`` with the same name.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(description="The tool's name as the agent invoked it.")
    call_id: str | None = Field(
        default=None,
        description="The adapter's identifier linking a tool_result to its tool_call, if any.",
    )


class EventError(BaseModel):
    """The error an event records: its type name, message, and whether it was unhandled."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: str = Field(description="The error's type name, such as the exception class.")
    message: str = Field(description="The error's message text.")
    unhandled: bool = Field(
        description="Whether the error escaped the agent unhandled and ended the run."
    )


class AgentInfo(BaseModel):
    """The agent under test as the adapter identifies it; the version may be unknown."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(description="The name of the agent under test.")
    version: str | None = Field(
        default=None, description="The agent's version string, when the adapter knows it."
    )


class AdapterInfo(BaseModel):
    """The adapter that produced the Trace; every adapter declares a name and a version (AD-9)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(description="The adapter's registered name, such as fixture.")
    version: str = Field(description="The adapter's version string.")


class ModelInfo(BaseModel):
    """The language model behind the run; both the provider and the name are optional (AC-5.1)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: str | None = Field(default=None, description="The model provider's name, when known.")
    name: str | None = Field(default=None, description="The model's name, when known.")


class Capture(BaseModel):
    """The adapter's Capture declaration (AD-5; PRD AC-5.6).

    ``complete`` means every tool call the agent made is in the Trace, so absence proofs
    such as ``tool_not_called`` are conclusive; ``partial`` and ``unknown`` make them
    limited to what the adapter observed (``constants.STATEMENTS.capture_limited``). An
    adapter that omits the declaration gets ``unknown``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tool_calls: CaptureLevel = Field(
        default="unknown",
        description=(
            "How completely the adapter observed the agent's tool calls: complete, partial, "
            "or unknown; unknown when the adapter made no declaration."
        ),
    )


class RedactionState(BaseModel):
    """What redaction has done to this Trace (AD-10; PRD AC-31.2).

    ``paths`` are the configured rule strings that matched; ``env_names`` are the names
    (never the values) of the environment variables whose values were scrubbed. A Trace
    nobody redacted carries ``applied=False`` with empty lists.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    applied: bool = Field(
        default=False, description="Whether redaction has been applied to this Trace."
    )
    paths: tuple[str, ...] = Field(
        default_factory=tuple,
        description="The configured redaction keys and paths that matched a value.",
    )
    env_names: tuple[str, ...] = Field(
        default_factory=tuple,
        description=(
            "The names, never the values, of the environment variables whose values were scrubbed."
        ),
    )


class Environment(BaseModel):
    """The allowlisted environment metadata (AD-9; PRD AC-5.5).

    Only the runner fills these four fields, from the package version, the interpreter
    version, the operating system name, and an optional source revision. Process
    environment variables, hostnames, and user names have no field here and are rejected
    as unknown keys.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    package_version: str | None = Field(
        default=None, description="The AgentProof package version that produced the Trace."
    )
    python_version: str | None = Field(
        default=None, description="The Python interpreter version of the run."
    )
    os: str | None = Field(default=None, description="The operating system name of the run.")
    source_revision: str | None = Field(
        default=None, description="The source revision of the agent under test, when known."
    )


class TraceEvent(BaseModel):
    """One recorded event (spine Schemas seed; AD-5).

    ``seq`` is the event's 0-based position and the only thing evidence points at. Which
    optional fields an event carries depends on its ``type``: ``tool_call`` carries
    ``tool`` and ``arguments``, ``tool_result`` carries ``tool``, ``result`` and
    ``status``, ``agent_finished`` carries the Final Output in ``output``, ``exception``
    carries ``error``. ``redacted`` marks an event the scrubber changed; ``metadata`` is
    free-form adapter data.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    seq: _NonNegativeInt = Field(
        description="The event's 0-based position in events; evidence points at this value."
    )
    type: EventType = Field(description="The event type, one of the eleven documented values.")
    timestamp: Timestamp | None = Field(
        default=None,
        description="When the event occurred, as an RFC 3339 string with an explicit offset.",
    )
    duration_ms: _NonNegativeInt | None = Field(
        default=None, description="How long the event took, in whole milliseconds."
    )
    tool: ToolRef | None = Field(
        default=None, description="The tool a tool_call or tool_result refers to."
    )
    arguments: _FiniteJsonValue = Field(
        default=None, description="The arguments passed to the tool on a tool_call."
    )
    result: _FiniteJsonValue = Field(
        default=None, description="The value the tool returned on a tool_result."
    )
    status: str | None = Field(
        default=None, description="The adapter's status word for the event, such as ok."
    )
    error: EventError | None = Field(
        default=None, description="The error an exception or failed event records."
    )
    output: _FiniteJsonValue = Field(
        default=None, description="The Final Output of the run on an agent_finished event."
    )
    redacted: bool = Field(
        default=False, description="Whether redaction changed a value in this event."
    )
    metadata: _FiniteJsonObject = Field(
        default_factory=dict, description="Free-form adapter metadata about the event."
    )

    @model_validator(mode="before")
    @classmethod
    def _null_is_absent(cls, data: Any) -> Any:
        """A ``null`` for a field with a default reads as the key being absent (AD-19)."""
        return _null_means_absent(cls, data)


class Trace(BaseModel):
    """One recorded run of an agent against a Scenario (``version`` 1; spine Schemas seed).

    ``run_id``, ``started_at``, ``ended_at`` and ``environment`` are owned by the runner,
    which overwrites whatever an adapter put there (AD-9). ``events`` must carry
    contiguous ``seq`` values starting at 0; the validator reports the first event whose
    ``seq`` differs from its index, located at ``events.<index>.seq``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: TraceSchemaVersion = Field(
        description="The Trace schema version, an integer independent of the package version.",
        json_schema_extra={"enum": list(SUPPORTED_VERSIONS["trace"])},
    )
    run_id: str = Field(description="The run identifier the runner assigned.")
    scenario_id: str = Field(description="The id of the Scenario this run executed.")
    started_at: Timestamp = Field(
        description="When the run started, as an RFC 3339 string with an explicit offset."
    )
    ended_at: Timestamp = Field(
        description="When the run ended, as an RFC 3339 string with an explicit offset."
    )
    agent: AgentInfo = Field(description="The agent under test.")
    adapter: AdapterInfo = Field(description="The adapter that produced this Trace.")
    model: ModelInfo | None = Field(
        default=None, description="The language model behind the run, when known."
    )
    capture: Capture = Field(
        default_factory=Capture,
        description="The adapter's declaration of how completely it captured tool calls.",
    )
    environment: Environment = Field(
        default_factory=Environment,
        description="Allowlisted environment metadata filled by the runner.",
    )
    redaction: RedactionState = Field(
        default_factory=RedactionState,
        description="What redaction has been applied to this Trace.",
    )
    events: tuple[TraceEvent, ...] = Field(
        description="The recorded events in order; seq runs 0, 1, 2, ... without gaps."
    )

    @model_validator(mode="before")
    @classmethod
    def _null_is_absent(cls, data: Any) -> Any:
        """A ``null`` for a field with a default reads as the key being absent (AD-19)."""
        return _null_means_absent(cls, data)

    @field_validator("events", mode="after")
    @classmethod
    def _seq_is_contiguous(cls, events: tuple[TraceEvent, ...]) -> tuple[TraceEvent, ...]:
        """Reject the first event whose ``seq`` is not its index (AD-5; PRD AC-7.2)."""
        for index, event in enumerate(events):
            if event.seq != index:
                raise ValidationError.from_exception_data(
                    cls.__name__,
                    [
                        InitErrorDetails(
                            type=PydanticCustomError(
                                "seq_not_contiguous",
                                "events[{index}].seq is {seq}; expected {index}: seq must run "
                                "0, 1, 2, ... with no gap, duplicate, or disorder",
                                {"index": index, "seq": event.seq},
                            ),
                            loc=(index, "seq"),
                            input=event.seq,
                        )
                    ],
                )
        return events
