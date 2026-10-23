"""Assertion configuration models and the static union (architecture AD-8).

One frozen model per built-in assertion type, each with ``type: Literal["<name>"]``, the
fields PRD FR-11 to FR-16 give it, and an optional ``id``. ``AssertionConfig`` is the
discriminated union on ``type`` that ``models.suite.Scenario.assertions`` holds, so an
unknown type fails at parse time with the field path. Configuration lives here, below
the layer boundary; the evaluators live in ``assertions/builtin`` and never leak into
``models`` (AD-2). The only YAML form is the flat mapping with a ``type`` key.

Models are shallow-frozen: sequence fields are tuples, so a validated configuration is
hashable and nothing can be appended to it; mapping fields (``arguments``) stay plain
dicts and are not deep-frozen. JSON input lists validate into the tuples and
``model_dump(mode="json")`` writes them back as arrays.

The ``id`` default ``<type>-<0-based index in the scenario list>`` is assigned by
``models.suite``, not here, because the index is a property of the Scenario. Nothing
here touches a file, the clock, or the environment (AD-1).
"""

from typing import Annotated, Final, Literal, Self, get_args

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agentproof.models.common import JsonValue

MODEL_CONFIG: Final[ConfigDict] = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)
"""The one model configuration every serialized model uses (AD-3): frozen after
construction, unknown fields rejected naming the field path, NaN and infinity rejected,
and no model-level ``strict`` so Python-mode validation of a dict is the only mode."""

ToolName = Annotated[str, Field(min_length=1)]
"""A tool name as a Trace records it: any non-empty string."""

Count = Annotated[int, Field(strict=True, ge=0)]
"""A non-negative call count. Field-level strict so ``"1"``, ``1.0``, and ``true`` are
rejected in Python and JSON mode alike (PRD AC-3.3: "without an integer")."""

ARGUMENT_PATH_PATTERN: Final = r"^[^.\s]+(\.[^.\s]+)*$"
"""The v0.1 argument path grammar (conventions; OQ-7): dotted segments, each non-empty and
free of whitespace, with integer list indexes written as segments, ``items.0.amount``.
No wildcards. A ``pattern`` constraint so Python validation and the exported JSON Schema
state the same rule."""

ArgumentPath = Annotated[str, Field(pattern=ARGUMENT_PATH_PATTERN)]
"""A dotted path into a tool call's arguments, ``items.0.amount`` (OQ-7)."""

Operator = Literal["equals", "greater_than", "less_than"]
"""The ``tool_call_count`` comparison field names."""

OPERATORS: Final[tuple[Operator, ...]] = ("equals", "greater_than", "less_than")
"""The ``Operator`` values as a runtime tuple, in declaration order."""


class AssertionConfigBase(BaseModel):
    """What every assertion configuration shares: the frozen config and an optional ``id``.

    ``id`` is ``None`` until the Scenario assigns the default ``<type>-<index>``; a Suite
    that has been validated never carries a ``None`` id (PRD AC-17.4). A user-given id
    is any non-empty string, unique within its Scenario (AC-3.1).
    """

    model_config = MODEL_CONFIG

    id: str | None = Field(default=None, min_length=1)
    """The Assertion id every Assertion Result carries; defaults to ``<type>-<index>``."""


class ToolCalled(AssertionConfigBase):
    """PRD FR-11: at least one ``tool_call`` Event with this tool name exists."""

    type: Literal["tool_called"]
    tool: ToolName


class ToolNotCalled(AssertionConfigBase):
    """PRD FR-12: no ``tool_call`` Event with this tool name exists."""

    type: Literal["tool_not_called"]
    tool: ToolName


class ToolCallCount(AssertionConfigBase):
    """PRD FR-13: the number of ``tool_call`` Events for the tool satisfies one comparison.

    Exactly one of ``equals``, ``greater_than``, ``less_than`` is given (AC-13.2); each is
    a non-negative integer.
    """

    type: Literal["tool_call_count"]
    tool: ToolName
    equals: Count | None = None
    greater_than: Count | None = None
    less_than: Count | None = None

    @model_validator(mode="after")
    def _exactly_one_operator(self) -> Self:
        given = [name for name in OPERATORS if getattr(self, name) is not None]
        if len(given) != 1:
            got = ", ".join(given) if given else "none"
            raise ValueError(
                f"tool_call_count takes exactly one of equals, greater_than, less_than; got {got}"
            )
        return self

    @property
    def operator(self) -> tuple[Operator, int]:
        """The one configured comparison as ``(field name, bound)``."""
        for name in OPERATORS:
            bound: int | None = getattr(self, name)
            if bound is not None:
                return name, bound
        raise AssertionError("validated ToolCallCount has exactly one operator")


class ToolArgumentsMatch(AssertionConfigBase):
    """PRD FR-14: some ``tool_call`` for the tool matches every configured path exactly.

    ``arguments`` maps a dotted argument path (``items.0.amount``; OQ-7) to the expected
    JSON value. At least one path is required; an empty mapping could never fail. The
    mapping is a plain dict and is not deep-frozen.
    """

    type: Literal["tool_arguments_match"]
    tool: ToolName
    arguments: dict[ArgumentPath, JsonValue] = Field(min_length=1)


class ToolOrder(AssertionConfigBase):
    """PRD FR-15: the listed tools occur as ``tool_call`` Events in this relative order.

    Intervening Events are allowed and the first occurrence of each tool is the one
    ordered (AC-15.1, AC-15.4). At least one tool is required; an empty list could never
    fail.
    """

    type: Literal["tool_order"]
    tools: tuple[ToolName, ...] = Field(min_length=1)


class FinalOutputContains(AssertionConfigBase):
    """PRD FR-16: the Final Output exists and contains ``value`` as a literal substring.

    Structured Final Output is matched against its compact Canonical form (AD-11).
    ``value`` is non-empty; the empty string is a substring of everything.
    """

    type: Literal["final_output_contains"]
    value: str = Field(min_length=1)
    case_sensitive: bool = True


ASSERTION_MODELS: Final[tuple[type[AssertionConfigBase], ...]] = (
    ToolCalled,
    ToolNotCalled,
    ToolCallCount,
    ToolArgumentsMatch,
    ToolOrder,
    FinalOutputContains,
)
"""The six configuration models in declaration order, the members of ``AssertionConfig``."""

AssertionConfig = Annotated[
    ToolCalled
    | ToolNotCalled
    | ToolCallCount
    | ToolArgumentsMatch
    | ToolOrder
    | FinalOutputContains,
    Field(discriminator="type"),
]
"""The static union of the six configurations, discriminated on ``type`` (AD-8)."""

ASSERTION_TYPES: Final[tuple[str, ...]] = tuple(
    get_args(model.model_fields["type"].annotation)[0] for model in ASSERTION_MODELS
)
"""The ``type`` literals of ``AssertionConfig`` in declaration order, read from the models
so the two cannot drift; the evaluator registry's keys must equal this tuple (AD-8)."""
