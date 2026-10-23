"""Assertion Result, Scenario Result, and Suite Outcome (architecture AD-6; PRD FR-17).

What the engine returns. ``engine.evaluate_scenario`` fans every Scenario out to one
``AssertionResult`` per Assertion and folds them into a ``ScenarioResult``;
``engine.fold`` folds those into a ``SuiteOutcome``, the in-memory shape the Report is
built from (AD-13). The rules this module enforces:

* ``status`` is one of the four ``Status`` values and nothing else is serializable
  (PRD AC-17.1); every result carries the id of the Assertion that produced it (AC-17.4).
* ``evidence`` is a tuple of event ``seq`` values, the only thing evidence points at
  (AD-5); each is an exact non-negative integer.
* ``ScenarioResult.counts`` equals the tally of its ``assertions`` by status; a
  mismatch is rejected at ``counts`` (PRD AC-22.3). ``count_statuses`` is the one tally,
  shared with the engine and the Report so the producer and the validator cannot differ.
* A Scenario has at least one Assertion (AD-6), so ``assertions`` has at least one item,
  and Assertion ids are unique within a Scenario (AD-8), as Scenario ids are unique
  within an outcome (AD-14).
* ``skip_reason`` and ``execution_error`` are the engine's two fan-out causes (AD-6): at
  most one is set, a ``skip_reason`` goes with status ``skipped``, an
  ``execution_error`` with status ``error``.
* ``SuiteOutcome.execution_failed`` is exactly "some Scenario carries an
  ``execution_error``" (AD-6); ``suite_status`` is not re-derived here because the fold
  belongs to ``engine.status.combine`` alone.
* A ``null`` for a field that has a default reads as the key being absent (AD-19).
* NaN and infinity are rejected (``MODEL_CONFIG``), so no artifact carries one.

Every model is frozen and rejects unknown fields; ``strict`` mode is not used (AD-3).
Frozen is shallow: sequence fields are tuples, ``detail`` is a plain ``JsonValue`` that
keeps whatever lists and dicts the engine put there and is not deep-frozen. The module
performs no I/O and imports only the standard library, Pydantic, and sibling ``models``
modules (AD-1, AD-2). It does not fold statuses: ``engine.status.combine`` is the only fold.
"""

from collections.abc import Iterable, Sequence
from typing import Annotated, Any, Self

from pydantic import BaseModel, Field, ValidationError, model_validator
from pydantic_core import InitErrorDetails, PydanticCustomError

from agentproof.models.assertions import Count
from agentproof.models.common import MODEL_CONFIG, JsonValue, Status, _null_means_absent
from agentproof.models.trace import Trace

__all__ = [
    "AssertionResult",
    "Cost",
    "Counts",
    "EventSeq",
    "Reason",
    "ScenarioResult",
    "SuiteOutcome",
    "count_statuses",
    "require_counts",
    "require_execution_failed",
    "require_non_empty",
    "require_unique_ids",
]

EventSeq = Annotated[int, Field(strict=True, ge=0)]
"""An event's ``seq`` as evidence points at it (AD-5): an exact non-negative integer, so
``"1"``, ``1.0`` and ``true`` are rejected like every other integer of a JSON contract."""

Cost = Annotated[float, Field(strict=True)]
"""A cost in the adapter's unit: a JSON number (an integer is accepted and stored as a
float), never a numeric string; NaN and infinity are rejected by ``MODEL_CONFIG``."""

Reason = Annotated[str, Field(min_length=1)]
"""A non-empty skip reason or execution error message; an empty string is a mistake, not
"unset" (``None`` is unset)."""


class Counts(BaseModel):
    """How many Assertion Results carry each ``Status`` (PRD AC-22.3).

    One key per status, every key always present, so two Counts compare field by field
    and a Report's summary never has a missing bucket.
    """

    model_config = MODEL_CONFIG

    passed: Count = Field(description="How many Assertion Results have status passed.")
    failed: Count = Field(description="How many Assertion Results have status failed.")
    error: Count = Field(description="How many Assertion Results have status error.")
    skipped: Count = Field(description="How many Assertion Results have status skipped.")


def count_statuses(statuses: Iterable[Status]) -> Counts:
    """Tally ``statuses`` into a ``Counts``.

    The one tally: the engine builds ``counts`` with it and the ``ScenarioResult`` and
    ``Report`` validators check against it, so a count can never disagree with the
    results it summarizes. Pure: an iterable in, a model out.
    """
    tally: dict[Status, int] = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
    for status in statuses:
        tally[status] += 1
    return Counts(
        passed=tally["passed"],
        failed=tally["failed"],
        error=tally["error"],
        skipped=tally["skipped"],
    )


def _error_at(
    title: str,
    loc: tuple[int | str, ...],
    error_type: str,
    message: str,
    context: dict[str, Any],
    value: object,
) -> ValidationError:
    """A one-line ``ValidationError`` titled ``title`` and located at ``loc``.

    Raised from an after model validator, Pydantic prefixes the model's own location when
    the model is nested (``scenarios.<index>.counts`` inside a Report) and the outer
    model's title replaces ``title``; at the top level ``title`` is the model's name.
    """
    return ValidationError.from_exception_data(
        title,
        [
            InitErrorDetails(
                type=PydanticCustomError(error_type, message, context),
                loc=loc,
                input=value,
            )
        ],
    )


def require_counts(counts: Counts, statuses: Iterable[Status], *, title: str) -> Counts:
    """Return ``counts`` when it equals the tally of ``statuses``, else raise at ``counts``.

    The one check behind ``ScenarioResult.counts`` and ``Report.counts`` (PRD AC-22.3).
    The error is a ``ValidationError`` titled ``title`` (the calling model's name) of
    type ``counts_mismatch`` located at ``counts``.
    """
    expected = count_statuses(statuses)
    if counts == expected:
        return counts
    raise _error_at(
        title,
        ("counts",),
        "counts_mismatch",
        "counts {given} do not match the assertion results, which tally to {expected}",
        {"given": counts.model_dump(), "expected": expected.model_dump()},
        counts.model_dump(),
    )


def require_non_empty(field: str, items: Sequence[object], *, title: str) -> None:
    """Raise Pydantic's ``too_short`` at ``field`` when ``items`` is empty.

    Checked from an after model validator rather than with ``Field(min_length=1)``:
    pydantic-core's tuple validator counts only the items that validated, so a
    ``min_length`` constraint adds a misleading "at least 1 item" line beside every
    element error. The after validator runs only when every element validated, so the
    error appears exactly when the sequence is empty. The field's JSON Schema still
    carries ``minItems: 1`` through ``json_schema_extra``. ``title`` is the calling
    model's name.
    """
    if items:
        return
    raise ValidationError.from_exception_data(
        title,
        [
            InitErrorDetails(
                type="too_short",
                loc=(field,),
                input=items,
                ctx={"field_type": "Tuple", "min_length": 1, "actual_length": 0},
            )
        ],
    )


def require_unique_ids(field: str, ids: Sequence[str], key: str, *, title: str) -> None:
    """Raise ``duplicate_id`` at ``<field>.<index>.<key>`` for the first repeated id.

    ``ids`` are the id values of the items of ``field`` in order and ``key`` is the name
    of the id field on each item (``scenario_id``, ``assertion_id``). The error points at
    the later duplicate and names the earlier position. ``title`` is the calling model's
    name.
    """
    seen: dict[str, int] = {}
    for index, ident in enumerate(ids):
        first = seen.get(ident)
        if first is None:
            seen[ident] = index
            continue
        raise _error_at(
            title,
            (field, index, key),
            "duplicate_id",
            "duplicate {key} {id} at {field}[{index}] and {field}[{first}]",
            {"key": key, "id": repr(ident), "field": field, "index": index, "first": first},
            ident,
        )


class AssertionResult(BaseModel):
    """What one Assertion produced against one Trace (PRD FR-17; spine Schemas seed).

    ``evidence`` lists the ``seq`` of every event the verdict rests on, so a reader can
    open the embedded Trace at those events. ``detail`` is free-form structured data the
    assertion adds, such as the expected and actual values; ``message`` is the one plain
    sentence a reviewer reads.
    """

    model_config = MODEL_CONFIG

    assertion_id: str = Field(
        min_length=1,
        description="The id of the Assertion that produced this result (PRD AC-17.4).",
    )
    type: str = Field(
        min_length=1, description="The assertion type that ran, such as tool_not_called."
    )
    status: Status = Field(description="The verdict: passed, failed, error, or skipped.")
    message: str = Field(
        description="One plain sentence explaining the verdict, including any capture caveat."
    )
    evidence: tuple[EventSeq, ...] = Field(
        description="The seq values of the Trace events the verdict rests on, in order."
    )
    detail: JsonValue = Field(
        default=None,
        description="Structured detail the assertion adds, such as expected and actual values.",
    )

    @model_validator(mode="before")
    @classmethod
    def _null_is_absent(cls, data: Any) -> Any:
        """A ``null`` for a field with a default reads as the key being absent (AD-19)."""
        return _null_means_absent(cls, data)


class ScenarioResult(BaseModel):
    """One Scenario's evaluation: its status, one result per Assertion, and the Trace (AD-6).

    ``skip_reason`` is set when the Scenario was skipped (status ``skipped``) and
    ``execution_error`` when the adapter failed or the Trace was missing under
    ``fail_on_missing_trace`` (status ``error``); the engine sets at most one of them.
    ``trace`` is the redacted Trace the results were evaluated against, or ``None`` when
    there was none (PRD AC-22.4). ``duration_ms`` and ``cost`` are the run's optional
    timing and cost (PRD FR-22), present when the runner or the adapter supplied them.
    """

    model_config = MODEL_CONFIG

    scenario_id: str = Field(min_length=1, description="The id of the Scenario evaluated.")
    status: Status = Field(
        description="The Scenario's folded status: passed, failed, error, or skipped."
    )
    skip_reason: Reason | None = Field(
        default=None,
        description="The Scenario's skip reason when it was skipped (status skipped), else null.",
    )
    execution_error: Reason | None = Field(
        default=None,
        description=(
            "Why the run could not produce evidence (adapter failure or missing Trace; "
            "status error), else null."
        ),
    )
    counts: Counts = Field(
        description="How many of this Scenario's Assertion Results carry each status."
    )
    assertions: tuple[AssertionResult, ...] = Field(
        description="One result per Assertion of the Scenario, in Suite order; at least one.",
        json_schema_extra={"minItems": 1},
    )
    trace: Trace | None = Field(
        default=None,
        description="The redacted Trace the results were evaluated against, or null when absent.",
    )
    duration_ms: Count | None = Field(
        default=None,
        description="How long the run took, in whole milliseconds, when the runner measured it.",
    )
    cost: Cost | None = Field(
        default=None,
        description="The run's cost in the adapter's unit when the adapter supplied one.",
    )

    @model_validator(mode="before")
    @classmethod
    def _null_is_absent(cls, data: Any) -> Any:
        """A ``null`` for a field with a default reads as the key being absent (AD-19)."""
        return _null_means_absent(cls, data)

    @model_validator(mode="after")
    def _results_are_consistent(self) -> Self:
        """At least one Assertion Result, unique ids, and a tally equal to ``counts``."""
        title = type(self).__name__
        require_non_empty("assertions", self.assertions, title=title)
        require_unique_ids(
            "assertions",
            [result.assertion_id for result in self.assertions],
            "assertion_id",
            title=title,
        )
        require_counts(self.counts, (result.status for result in self.assertions), title=title)
        return self

    @model_validator(mode="after")
    def _cause_matches_status(self) -> Self:
        """``skip_reason`` goes with ``skipped``, ``execution_error`` with ``error``, never both."""
        title = type(self).__name__
        if self.skip_reason is not None and self.execution_error is not None:
            raise _error_at(
                title,
                ("execution_error",),
                "skip_reason_and_execution_error",
                "execution_error cannot be set together with skip_reason; the engine "
                "interprets a skip before anything else and sets at most one cause",
                {},
                self.execution_error,
            )
        if self.skip_reason is not None and self.status != "skipped":
            raise _error_at(
                title,
                ("skip_reason",),
                "skip_reason_requires_skipped",
                "skip_reason is set but status is {status}; a skipped Scenario has status skipped",
                {"status": self.status},
                self.skip_reason,
            )
        if self.execution_error is not None and self.status != "error":
            raise _error_at(
                title,
                ("execution_error",),
                "execution_error_requires_error",
                "execution_error is set but status is {status}; a Scenario whose run "
                "failed has status error",
                {"status": self.status},
                self.execution_error,
            )
        return self


def require_execution_failed(
    execution_failed: bool, scenarios: Sequence[ScenarioResult], *, title: str
) -> None:
    """Raise ``execution_failed_mismatch`` at ``execution_failed`` unless it is derived right.

    AD-6: ``execution_failed`` is whether any Scenario carries an ``execution_error``.
    The message names the first Scenario that sets one, or states that none does.
    ``title`` is the calling model's name.
    """
    first = next(
        (
            (index, scenario.scenario_id)
            for index, scenario in enumerate(scenarios)
            if scenario.execution_error is not None
        ),
        None,
    )
    if execution_failed == (first is not None):
        return
    if first is None:
        message = "execution_failed is true but no scenario sets execution_error"
        context: dict[str, Any] = {}
    else:
        message = "execution_failed is false but scenarios[{index}] ({id}) sets execution_error"
        context = {"index": first[0], "id": repr(first[1])}
    raise _error_at(
        title,
        ("execution_failed",),
        "execution_failed_mismatch",
        message,
        context,
        execution_failed,
    )


class SuiteOutcome(BaseModel):
    """What ``engine.fold`` returns: every Scenario Result and the Suite-level verdict (AD-6).

    In-memory only; the Report adds identity, counts, the Suite defaults snapshot, and
    its own schema version. ``execution_failed`` is whether any Scenario carries an
    ``execution_error`` (exit 3) and is checked here; ``evaluated_assertions`` counts the
    results whose status is not ``skipped`` (a Suite that evaluated nothing exits 1) and
    ``suite_status`` is the fold, both produced by ``engine.fold`` alone.
    """

    model_config = MODEL_CONFIG

    scenarios: tuple[ScenarioResult, ...] = Field(
        description="One result per Scenario of the Suite, in Suite order; at least one.",
        json_schema_extra={"minItems": 1},
    )
    suite_status: Status = Field(
        description="The Suite's folded status: passed, failed, error, or skipped."
    )
    execution_failed: bool = Field(
        description="Whether any Scenario carries an execution error (CLI exit 3)."
    )
    evaluated_assertions: Count = Field(
        description="How many Assertion Results have a status other than skipped."
    )

    @model_validator(mode="after")
    def _scenarios_are_consistent(self) -> Self:
        """At least one Scenario, unique Scenario ids, and ``execution_failed`` derived right."""
        title = type(self).__name__
        require_non_empty("scenarios", self.scenarios, title=title)
        require_unique_ids(
            "scenarios",
            [scenario.scenario_id for scenario in self.scenarios],
            "scenario_id",
            title=title,
        )
        require_execution_failed(self.execution_failed, self.scenarios, title=title)
        return self
