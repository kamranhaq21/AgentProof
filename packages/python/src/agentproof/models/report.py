"""The Report and Comparison data contracts (architecture AD-11, AD-13; PRD FR-22, FR-26).

A Report is what ``agentproof run`` and ``trace replay`` write and what reviewers,
``compare``, the HTML renderer, and the viewer read: a ``SuiteOutcome`` plus identity,
summary counts, the Suite defaults snapshot, and the redacted Trace of every Scenario,
so a Report alone shows the evidence and serves as a Baseline (PRD AC-22.4). It is built
only by ``reports.build_report`` (AD-13); this module validates the shape. The rules it
enforces:

* ``version`` is an exact integer listed in ``constants.SUPPORTED_VERSIONS["report"]``;
  ``"1"``, ``1.0`` and ``true`` are rejected (AD-3). The Report's version is independent
  of the package version and of the Suite and Trace versions it records in
  ``schema_versions``.
* ``counts`` equals the tally of every Assertion Result in every Scenario (PRD AC-22.3);
  a mismatch is rejected at ``counts``. Each ``ScenarioResult`` checks its own counts.
* Scenario ids are unique (AD-14) and ``execution_failed`` is exactly "some Scenario
  carries an ``execution_error``" (AD-6); ``suite_status`` is not re-derived because the
  fold belongs to ``engine.status.combine`` alone.
* ``created_at`` is an RFC 3339 string with an explicit offset, stored as given (AD-3).
* ``defaults`` is the ``SuiteDefaults`` model serialized with every field, which is where
  ``compare`` takes ``include_arguments`` from, so no Suite is needed at comparison time.
* A ``null`` for a field that has a default reads as the key being absent (AD-19).

A Comparison is the diff between a Baseline Report and a current Report (PRD FR-26). It
lists the two Suite statuses, per-scenario status changes, Assertion-id set differences,
failed-Assertion-id differences, tool-sequence differences, event-count differences,
selected-argument differences, added and removed Scenarios, duration and cost differences
present on both sides, ``regressed`` (PRD AC-26.4), and the fixed statement that it is an
exact comparison of saved data (``constants.STATEMENTS``, PRD AC-26.6), which no
Comparison may alter. It is built only by ``compare``; it is written and never read back,
so it carries no schema version.

Every model is frozen and rejects unknown fields; ``strict`` mode is not used (AD-3).
Frozen is shallow: sequence fields are tuples, embedded models are frozen themselves, and
``JsonValue`` fields are not deep-frozen. The module performs no I/O and imports only the
standard library, Pydantic, ``constants``, and sibling ``models`` modules (AD-1, AD-2).
"""

from typing import Annotated, Any, Self

from pydantic import AfterValidator, BaseModel, Field, model_validator
from pydantic_core import PydanticCustomError

from agentproof.constants import STATEMENTS, SUPPORTED_VERSIONS
from agentproof.models.assertions import Count
from agentproof.models.common import MODEL_CONFIG, JsonValue, Status, _null_means_absent
from agentproof.models.result import (
    Cost,
    Counts,
    ScenarioResult,
    require_counts,
    require_execution_failed,
    require_non_empty,
    require_unique_ids,
)
from agentproof.models.suite import CompareArgumentPath, SuiteDefaults
from agentproof.models.trace import Timestamp

__all__ = [
    "ArgumentChange",
    "AssertionIdChange",
    "Comparison",
    "CostChange",
    "DurationChange",
    "EventCountChange",
    "FailedAssertionChange",
    "Report",
    "ReportSchemaVersion",
    "SchemaVersions",
    "StatusChange",
    "ToolSequenceChange",
]


def _require_supported_report_version(value: int) -> int:
    """Accept only a version listed in ``SUPPORTED_VERSIONS["report"]`` (AD-3)."""
    supported = SUPPORTED_VERSIONS["report"]
    if value not in supported:
        raise PydanticCustomError(
            "unsupported_version",
            "Report schema version {given} is not supported; supported versions: {supported}",
            {"given": value, "supported": ", ".join(str(number) for number in supported)},
        )
    return value


def _require_fixed_statement(value: str) -> str:
    """Accept only ``STATEMENTS.compare_is_saved_data`` (PRD AC-26.6)."""
    if value != STATEMENTS.compare_is_saved_data:
        raise PydanticCustomError(
            "statement_fixed",
            "statement must be the fixed saved-data statement: {expected}",
            {"expected": STATEMENTS.compare_is_saved_data},
        )
    return value


ReportSchemaVersion = Annotated[
    int, Field(strict=True), AfterValidator(_require_supported_report_version)
]
"""An exact integer that ``SUPPORTED_VERSIONS["report"]`` lists (AD-3)."""

_SchemaVersionNumber = Annotated[int, Field(strict=True, ge=1)]


class SchemaVersions(BaseModel):
    """The Suite and Trace schema versions the run used (spine Schemas seed).

    Recorded so a reader of an old Report knows which Suite and Trace rules applied; the
    embedded Traces carry their own ``version`` and are validated by it.
    """

    model_config = MODEL_CONFIG

    suite: _SchemaVersionNumber = Field(
        description="The Suite schema version of the Suite that was run."
    )
    trace: _SchemaVersionNumber = Field(
        description="The Trace schema version of the Traces that were evaluated."
    )


class Report(BaseModel):
    """The JSON Report (``version`` 1; spine Schemas seed; PRD FR-22).

    ``run_id``, ``created_at``, and ``package_version`` are volatile between runs and
    ``canonical.VOLATILE_PATHS`` names them, as it names each Scenario's Trace identity,
    timestamps, durations, and ``cost``. Everything else is a deterministic function of
    the Suite and the Traces.
    """

    model_config = MODEL_CONFIG

    version: ReportSchemaVersion = Field(
        description="The Report schema version, an integer independent of the package version.",
        json_schema_extra={"enum": list(SUPPORTED_VERSIONS["report"])},
    )
    suite_id: str = Field(min_length=1, description="The id of the Suite that was run.")
    run_id: str = Field(min_length=1, description="The run identifier the runner assigned.")
    created_at: Timestamp = Field(
        description="When the Report was created, as an RFC 3339 string with an explicit offset."
    )
    package_version: str = Field(
        min_length=1, description="The AgentProof package version that wrote the Report."
    )
    schema_versions: SchemaVersions = Field(
        description="The Suite and Trace schema versions the run used."
    )
    defaults: SuiteDefaults = Field(
        description="The Suite defaults snapshot, every field written; compare reads it."
    )
    suite_status: Status = Field(
        description="The Suite's folded status: passed, failed, error, or skipped."
    )
    execution_failed: bool = Field(
        description="Whether any Scenario carries an execution error (CLI exit 3)."
    )
    counts: Counts = Field(
        description="How many Assertion Results across every Scenario carry each status."
    )
    scenarios: tuple[ScenarioResult, ...] = Field(
        description="One result per Scenario, in Suite order, each with its redacted Trace.",
        json_schema_extra={"minItems": 1},
    )

    @model_validator(mode="after")
    def _scenarios_are_consistent(self) -> Self:
        """At least one Scenario, unique ids, ``execution_failed`` and ``counts`` derived right."""
        title = type(self).__name__
        require_non_empty("scenarios", self.scenarios, title=title)
        require_unique_ids(
            "scenarios",
            [scenario.scenario_id for scenario in self.scenarios],
            "scenario_id",
            title=title,
        )
        require_execution_failed(self.execution_failed, self.scenarios, title=title)
        require_counts(
            self.counts,
            (result.status for scenario in self.scenarios for result in scenario.assertions),
            title=title,
        )
        return self


class StatusChange(BaseModel):
    """A Scenario whose status differs between the Baseline and the current Report."""

    model_config = MODEL_CONFIG

    scenario_id: str = Field(min_length=1, description="The id of the Scenario that changed.")
    baseline: Status = Field(description="The Scenario's status in the Baseline Report.")
    current: Status = Field(description="The Scenario's status in the current Report.")


class AssertionIdChange(BaseModel):
    """A Scenario whose set of Assertion ids, of every status, differs between the Reports.

    The set difference of all Assertion ids whatever their status: it shows that the
    Suite's Assertions themselves changed between the two runs. ``FailedAssertionChange``
    is the status-aware view FR-26 names ("failed Assertion ids").
    """

    model_config = MODEL_CONFIG

    scenario_id: str = Field(min_length=1, description="The id of the Scenario that changed.")
    added: tuple[str, ...] = Field(
        description=(
            "Assertion ids, of any status, present in the current Report only, in current order."
        )
    )
    removed: tuple[str, ...] = Field(
        description=(
            "Assertion ids, of any status, present in the Baseline Report only, in Baseline order."
        )
    )


class FailedAssertionChange(BaseModel):
    """A Scenario whose set of failed Assertion ids differs (PRD FR-26, "failed Assertion ids")."""

    model_config = MODEL_CONFIG

    scenario_id: str = Field(min_length=1, description="The id of the Scenario that changed.")
    newly_failing: tuple[str, ...] = Field(
        description=(
            "Assertion ids failed in the current Report that were not failed in the Baseline, "
            "in current order."
        )
    )
    newly_passing: tuple[str, ...] = Field(
        description=(
            "Assertion ids failed in the Baseline that are no longer failed in the current "
            "Report, in Baseline order."
        )
    )


class ToolSequenceChange(BaseModel):
    """A Scenario whose tool-call sequence (tool names in event order) differs."""

    model_config = MODEL_CONFIG

    scenario_id: str = Field(min_length=1, description="The id of the Scenario that changed.")
    baseline: tuple[str, ...] = Field(
        description="The tool names of the Baseline's tool_call events, in seq order."
    )
    current: tuple[str, ...] = Field(
        description="The tool names of the current Report's tool_call events, in seq order."
    )


class EventCountChange(BaseModel):
    """A Scenario whose embedded Trace has missing or additional events (PRD FR-26)."""

    model_config = MODEL_CONFIG

    scenario_id: str = Field(min_length=1, description="The id of the Scenario that changed.")
    baseline_events: Count = Field(description="How many events the Baseline's embedded Trace has.")
    current_events: Count = Field(
        description="How many events the current Report's embedded Trace has."
    )


class ArgumentChange(BaseModel):
    """A selected argument (``defaults.compare.include_arguments``) whose value differs."""

    model_config = MODEL_CONFIG

    scenario_id: str = Field(min_length=1, description="The id of the Scenario that changed.")
    path: CompareArgumentPath = Field(
        description="The compared path as <tool>.<argument path>, such as approve_expense.amount."
    )
    baseline: JsonValue = Field(description="The value at that path in the Baseline Report.")
    current: JsonValue = Field(description="The value at that path in the current Report.")


class DurationChange(BaseModel):
    """A Scenario whose duration differs; listed only when both sides have one."""

    model_config = MODEL_CONFIG

    scenario_id: str = Field(min_length=1, description="The id of the Scenario that changed.")
    baseline_ms: Count = Field(description="The Baseline run's duration in whole milliseconds.")
    current_ms: Count = Field(description="The current run's duration in whole milliseconds.")


class CostChange(BaseModel):
    """A Scenario whose cost differs; listed only when both sides have one."""

    model_config = MODEL_CONFIG

    scenario_id: str = Field(min_length=1, description="The id of the Scenario that changed.")
    baseline: Cost = Field(description="The Baseline run's cost in the adapter's unit.")
    current: Cost = Field(description="The current run's cost in the adapter's unit.")


class Comparison(BaseModel):
    """The diff between a Baseline Report and a current Report (PRD FR-26).

    Every list is empty when a Report is compared against itself (PRD AC-26.2). A
    Scenario present on one side only appears in ``added_scenarios`` or
    ``removed_scenarios`` and nowhere else (AC-26.3). ``regressed`` is whether any
    Scenario went from ``passed`` to ``failed`` or ``error`` (AC-26.4); ``compare``
    decides it and the CLI maps it to the exit code. ``statement`` is the fixed
    saved-data sentence and cannot be anything else (AC-26.6).
    """

    model_config = MODEL_CONFIG

    baseline_suite_status: Status = Field(description="The Baseline Report's suite status.")
    current_suite_status: Status = Field(description="The current Report's suite status.")
    status_changes: tuple[StatusChange, ...] = Field(
        default_factory=tuple, description="Scenarios whose status differs."
    )
    assertion_id_changes: tuple[AssertionIdChange, ...] = Field(
        default_factory=tuple,
        description="Scenarios whose set of Assertion ids, of any status, differs.",
    )
    failed_assertion_changes: tuple[FailedAssertionChange, ...] = Field(
        default_factory=tuple,
        description="Scenarios whose set of failed Assertion ids differs.",
    )
    tool_sequence_changes: tuple[ToolSequenceChange, ...] = Field(
        default_factory=tuple, description="Scenarios whose tool-call sequence differs."
    )
    event_count_changes: tuple[EventCountChange, ...] = Field(
        default_factory=tuple,
        description="Scenarios whose embedded Trace has missing or additional events.",
    )
    argument_changes: tuple[ArgumentChange, ...] = Field(
        default_factory=tuple,
        description="Selected arguments whose values differ, per Scenario and path.",
    )
    added_scenarios: tuple[str, ...] = Field(
        default_factory=tuple, description="Scenario ids present in the current Report only."
    )
    removed_scenarios: tuple[str, ...] = Field(
        default_factory=tuple, description="Scenario ids present in the Baseline Report only."
    )
    duration_changes: tuple[DurationChange, ...] = Field(
        default_factory=tuple,
        description="Scenarios whose duration differs, when both sides have one.",
    )
    cost_changes: tuple[CostChange, ...] = Field(
        default_factory=tuple,
        description="Scenarios whose cost differs, when both sides have one.",
    )
    regressed: bool = Field(
        description="Whether any Scenario went from passed to failed or error (PRD AC-26.4)."
    )
    statement: Annotated[str, AfterValidator(_require_fixed_statement)] = Field(
        default=STATEMENTS.compare_is_saved_data,
        description=(
            "The fixed statement that this is an exact comparison of saved data, never a "
            "claim about agent reproducibility (PRD AC-26.6)."
        ),
    )

    @model_validator(mode="before")
    @classmethod
    def _null_is_absent(cls, data: Any) -> Any:
        """A ``null`` for a field with a default reads as the key being absent (AD-19)."""
        return _null_means_absent(cls, data)
