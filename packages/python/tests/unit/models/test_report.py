"""``agentproof.models.report``: the spine's Report seed, counts, Comparison, Canonical form.

``SEED`` is the Report JSON seed from the architecture spine ("Schemas (seed)") completed
where the spine abbreviates: ``run_id`` and ``created_at`` replace the ``"…"``
placeholders and the embedded ``trace`` is the completed Trace seed from ``test_trace``.
The counts and the three Assertion Results are the spine's own (the seed was amended on
2026-10-23 so its ``passed: 2, failed: 1`` reconciles with the results it lists; the
earlier one-result form is kept below as the rejection case). Every test validates
through ``model_validate(dict)`` (AD-3).
"""

import copy
import json
import re
from typing import Any, get_args

import pytest
from pydantic import BaseModel, ValidationError

import agentproof.models.report as report_module
from agentproof.constants import STATEMENTS, SUPPORTED_VERSIONS
from agentproof.models.canonical import VOLATILE_PATHS, dumps
from agentproof.models.common import STATUSES, Status
from agentproof.models.report import (
    ArgumentChange,
    AssertionIdChange,
    Comparison,
    CostChange,
    DurationChange,
    EventCountChange,
    FailedAssertionChange,
    Report,
    SchemaVersions,
    StatusChange,
    ToolSequenceChange,
)
from agentproof.models.result import AssertionResult, Counts, ScenarioResult
from agentproof.models.suite import SuiteDefaults
from agentproof.models.trace import Trace, TraceEvent

from .test_trace import SEED as TRACE_SEED

CREATED_AT = "2026-10-22T13:05:02+00:00"

SEED: dict[str, Any] = {
    "version": 1,
    "suite_id": "expense-agent",
    "run_id": "fixture-reject-over-limit",
    "created_at": CREATED_AT,
    "package_version": "0.1.0",
    "schema_versions": {"suite": 1, "trace": 1},
    "defaults": {
        "adapter": "fixture",
        "fail_on_missing_trace": True,
        "fixture": {"deterministic": True},
        "compare": {"include_arguments": []},
        "redact": {"keys": [], "paths": [], "env": ["OPENAI_API_KEY"]},
    },
    "suite_status": "failed",
    "execution_failed": False,
    "counts": {"passed": 2, "failed": 1, "error": 0, "skipped": 0},
    "scenarios": [
        {
            "scenario_id": "reject-over-limit",
            "status": "failed",
            "skip_reason": None,
            "execution_error": None,
            "counts": {"passed": 2, "failed": 1, "error": 0, "skipped": 0},
            "assertions": [
                {
                    "assertion_id": "tool_not_called-0",
                    "type": "tool_not_called",
                    "status": "failed",
                    "message": "approve_expense was called (capture: complete)",
                    "evidence": [1],
                    "detail": {},
                },
                {
                    "assertion_id": "tool_call_count-1",
                    "type": "tool_call_count",
                    "status": "passed",
                    "message": "reject_expense was called 1 time (equals 1)",
                    "evidence": [1],
                    "detail": {},
                },
                {
                    "assertion_id": "says-rejected",
                    "type": "final_output_contains",
                    "status": "passed",
                    "message": 'final output contains "rejected"',
                    "evidence": [3],
                    "detail": {},
                },
            ],
            "trace": TRACE_SEED,
            "cost": None,
        }
    ],
}


def _report(**overrides: Any) -> dict[str, Any]:
    """A deep copy of ``SEED`` with top-level keys replaced; a ``...`` value removes the key."""
    data = copy.deepcopy(SEED)
    for key, value in overrides.items():
        if value is ...:
            data.pop(key, None)
        else:
            data[key] = value
    return data


def _assertion(assertion_id: str, status: Status) -> dict[str, Any]:
    return {
        "assertion_id": assertion_id,
        "type": "tool_called",
        "status": status,
        "message": f"{assertion_id} {status}",
        "evidence": [],
        "detail": None,
    }


def _scenario(scenario_id: str, *statuses: Status) -> dict[str, Any]:
    """A Scenario Result with one result per status and consistent counts, no Trace."""
    tally = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
    for status in statuses:
        tally[status] += 1
    return {
        "scenario_id": scenario_id,
        "status": "failed" if "failed" in statuses else statuses[0],
        "skip_reason": None,
        "execution_error": None,
        "counts": tally,
        "assertions": [
            _assertion(f"tool_called-{index}", status) for index, status in enumerate(statuses)
        ],
        "trace": None,
        "cost": None,
    }


def _comparison(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "baseline_suite_status": "passed",
        "current_suite_status": "passed",
        "regressed": False,
    }
    data.update(overrides)
    return data


def _errors(
    excinfo: pytest.ExceptionInfo[ValidationError],
) -> list[tuple[tuple[int | str, ...], str]]:
    return [(error["loc"], error["msg"]) for error in excinfo.value.errors()]


def _locs(excinfo: pytest.ExceptionInfo[ValidationError]) -> list[tuple[int | str, ...]]:
    return [loc for loc, _ in _errors(excinfo)]


def _types(excinfo: pytest.ExceptionInfo[ValidationError]) -> list[str]:
    """The stable error type codes ``loading.parse_report`` keys on."""
    return [error["type"] for error in excinfo.value.errors()]


def _schema_properties(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Every property of the root and of every ``$defs`` entry, keyed ``Model.field``."""
    found: dict[str, dict[str, Any]] = {}
    for name, definition in [(schema["title"], schema), *schema.get("$defs", {}).items()]:
        for field, prop in definition.get("properties", {}).items():
            found[f"{name}.{field}"] = prop
    return found


# --- criterion 2: the spine's Report seed -----------------------------------------------


def test_spine_report_seed_validates_with_every_field_of_criterion_2() -> None:
    report = Report.model_validate(SEED)
    assert report.version == 1
    assert report.suite_id == "expense-agent"
    assert report.run_id == "fixture-reject-over-limit"
    assert report.created_at == CREATED_AT
    assert report.package_version == "0.1.0"
    assert report.schema_versions == SchemaVersions(suite=1, trace=1)
    assert isinstance(report.defaults, SuiteDefaults)
    assert report.defaults.adapter == "fixture"
    assert report.defaults.fixture.deterministic is True
    assert report.defaults.redact.env == ("OPENAI_API_KEY",)
    assert report.suite_status == "failed"
    assert report.execution_failed is False
    assert report.counts == Counts(passed=2, failed=1, error=0, skipped=0)
    assert len(report.scenarios) == 1
    scenario = report.scenarios[0]
    assert isinstance(scenario, ScenarioResult)
    assert scenario.scenario_id == "reject-over-limit"
    assert scenario.counts == report.counts
    assert [result.assertion_id for result in scenario.assertions] == [
        "tool_not_called-0",
        "tool_call_count-1",
        "says-rejected",
    ]
    assert isinstance(scenario.assertions[0], AssertionResult)
    assert scenario.assertions[0].evidence == (1,)
    assert scenario.assertions[2].evidence == (3,)
    assert isinstance(scenario.trace, Trace)
    assert scenario.trace.events[1].tool is not None
    assert scenario.trace.events[1].tool.name == "reject_expense"
    assert scenario.duration_ms is None
    assert scenario.cost is None


def test_embedded_trace_may_be_null_or_absent() -> None:
    for trace in (None, ...):
        data = _report()
        if trace is ...:
            del data["scenarios"][0]["trace"]
        else:
            data["scenarios"][0]["trace"] = trace
        assert Report.model_validate(data).scenarios[0].trace is None


def test_every_top_level_report_field_is_required() -> None:
    for field in SEED:
        with pytest.raises(ValidationError) as excinfo:
            Report.model_validate(_report(**{field: ...}))
        assert _locs(excinfo) == [(field,)], field
        assert _types(excinfo) == ["missing"], field


def test_report_round_trips_through_json_mode_dump() -> None:
    report = Report.model_validate(SEED)
    dumped = report.model_dump(mode="json")
    assert dumped["scenarios"][0]["trace"]["events"][0]["seq"] == 0
    assert dumped["defaults"]["redact"]["env"] == ["OPENAI_API_KEY"]
    assert Report.model_validate(dumped) == report


# --- criterion 2: counts ----------------------------------------------------------------


def test_report_counts_equal_to_the_tally_over_every_scenario_validate() -> None:
    data = _report(
        counts={"passed": 2, "failed": 1, "error": 1, "skipped": 0},
        scenarios=[
            _scenario("a", "passed", "failed"),
            _scenario("b", "passed", "error"),
        ],
    )
    report = Report.model_validate(data)
    assert report.counts == Counts(passed=2, failed=1, error=1, skipped=0)


def test_report_counts_mismatch_is_rejected_at_counts_naming_both_tallies() -> None:
    data = _report(
        counts={"passed": 2, "failed": 0, "error": 0, "skipped": 0},
        scenarios=[_scenario("a", "passed"), _scenario("b", "failed")],
    )
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(data)
    assert _locs(excinfo) == [("counts",)]
    assert _types(excinfo) == ["counts_mismatch"]
    message = _errors(excinfo)[0][1]
    assert "'passed': 2, 'failed': 0" in message
    assert "'passed': 1, 'failed': 1" in message


def test_the_spines_former_abbreviated_seed_is_rejected_at_the_scenario_counts() -> None:
    # Before 2026-10-23 the spine wrote ``passed: 2, failed: 1`` beside a single failed
    # result; that abbreviation is exactly what AC-22.3 forbids.
    data = _report()
    del data["scenarios"][0]["assertions"][1:]
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(data)
    assert _locs(excinfo) == [("scenarios", 0, "counts")]
    assert _types(excinfo) == ["counts_mismatch"]


def test_duplicate_scenario_ids_are_rejected_at_the_later_scenario() -> None:
    data = _report(
        counts={"passed": 2, "failed": 1, "error": 0, "skipped": 0},
        scenarios=[_scenario("a", "passed"), _scenario("b", "failed"), _scenario("a", "passed")],
    )
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(data)
    assert excinfo.value.title == "Report"
    assert _locs(excinfo) == [("scenarios", 2, "scenario_id")]
    assert _types(excinfo) == ["duplicate_id"]
    assert "scenarios[2] and scenarios[0]" in _errors(excinfo)[0][1]
    data["scenarios"][2]["scenario_id"] = "c"
    assert [s.scenario_id for s in Report.model_validate(data).scenarios] == ["a", "b", "c"]


def _errored_scenario(scenario_id: str) -> dict[str, Any]:
    scenario = _scenario(scenario_id, "error")
    scenario["execution_error"] = "trace missing"
    return scenario


def test_execution_failed_true_with_an_execution_error_validates() -> None:
    data = _report(
        execution_failed=True,
        counts={"passed": 1, "failed": 0, "error": 1, "skipped": 0},
        scenarios=[_scenario("a", "passed"), _errored_scenario("b")],
    )
    report = Report.model_validate(data)
    assert report.execution_failed is True
    assert report.scenarios[1].execution_error == "trace missing"


def test_execution_failed_false_with_an_execution_error_is_rejected_naming_the_scenario() -> None:
    data = _report(
        execution_failed=False,
        counts={"passed": 1, "failed": 0, "error": 1, "skipped": 0},
        scenarios=[_scenario("a", "passed"), _errored_scenario("b")],
    )
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(data)
    assert _locs(excinfo) == [("execution_failed",)]
    assert _types(excinfo) == ["execution_failed_mismatch"]
    assert "scenarios[1] ('b')" in _errors(excinfo)[0][1]


def test_execution_failed_true_without_an_execution_error_is_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(_report(execution_failed=True))
    assert _locs(excinfo) == [("execution_failed",)]
    assert _types(excinfo) == ["execution_failed_mismatch"]
    assert "no scenario sets execution_error" in _errors(excinfo)[0][1]


def test_a_scenario_counts_mismatch_is_rejected_naming_the_scenario() -> None:
    bad = _scenario("b", "failed")
    bad["counts"] = {"passed": 1, "failed": 0, "error": 0, "skipped": 0}
    data = _report(
        counts={"passed": 1, "failed": 1, "error": 0, "skipped": 0},
        scenarios=[_scenario("a", "passed"), bad],
    )
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(data)
    assert _locs(excinfo) == [("scenarios", 1, "counts")]
    assert _types(excinfo) == ["counts_mismatch"]


def test_report_with_no_scenarios_is_rejected_at_scenarios() -> None:
    data = _report(counts={"passed": 0, "failed": 0, "error": 0, "skipped": 0}, scenarios=[])
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(data)
    assert _locs(excinfo) == [("scenarios",)]
    assert _types(excinfo) == ["too_short"]


# --- criterion 2: version, identity, created_at, schema_versions, defaults ------------


def test_version_accepts_only_the_supported_report_versions() -> None:
    assert SUPPORTED_VERSIONS["report"] == (1,)
    for version in SUPPORTED_VERSIONS["report"]:
        assert Report.model_validate(_report(version=version)).version == version
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(_report(version=2))
    assert _locs(excinfo) == [("version",)]
    assert _types(excinfo) == ["unsupported_version"]
    assert "2" in _errors(excinfo)[0][1]
    assert "supported versions: 1" in _errors(excinfo)[0][1]


@pytest.mark.parametrize("version", ["1", 1.0, True, None])
def test_non_integer_version_is_rejected(version: object) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(_report(version=version))
    assert _locs(excinfo) == [("version",)]
    assert _types(excinfo) == ["int_type"]


def test_unsupported_version_with_an_unknown_field_reports_both_codes() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(_report(version=2, summary="..."))
    assert set(_types(excinfo)) == {"unsupported_version", "extra_forbidden"}


@pytest.mark.parametrize("field", ["suite_id", "run_id", "package_version"])
def test_identity_strings_must_be_non_empty(field: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(_report(**{field: ""}))
    assert _locs(excinfo) == [(field,)]
    assert _types(excinfo) == ["string_too_short"]


@pytest.mark.parametrize(
    "created_at",
    ["2026-10-22T13:05:02+00:00", "2026-10-22T13:05:02Z", "2026-10-22T13:05:02.123456-05:00"],
)
def test_created_at_accepts_rfc3339_with_an_offset_and_stores_it_as_given(
    created_at: str,
) -> None:
    assert Report.model_validate(_report(created_at=created_at)).created_at == created_at


@pytest.mark.parametrize(
    ("created_at", "code"),
    [("2026-10-22T13:05:02", "timestamp_format"), (1761138302, "timestamp_type")],
)
def test_naive_or_non_string_created_at_is_rejected(created_at: object, code: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(_report(created_at=created_at))
    assert _locs(excinfo) == [("created_at",)]
    assert _types(excinfo) == [code]


def test_schema_versions_has_exactly_suite_and_trace_as_positive_integers() -> None:
    assert tuple(SchemaVersions.model_fields) == ("suite", "trace")
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(_report(schema_versions={"suite": 1}))
    assert _locs(excinfo) == [("schema_versions", "trace")]
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(_report(schema_versions={"suite": "1", "trace": 0}))
    assert _locs(excinfo) == [("schema_versions", "suite"), ("schema_versions", "trace")]
    assert _types(excinfo) == ["int_type", "greater_than_equal"]
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(_report(schema_versions={"suite": 1, "trace": 1, "report": 1}))
    assert _locs(excinfo) == [("schema_versions", "report")]
    assert _types(excinfo) == ["extra_forbidden"]


def test_defaults_is_a_suite_defaults_and_its_rules_apply() -> None:
    report = Report.model_validate(_report(defaults={}))
    assert report.defaults == SuiteDefaults()
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(_report(defaults={"adapter": "fixture", "timeout": 3}))
    assert _locs(excinfo) == [("defaults", "timeout")]
    assert _types(excinfo) == ["extra_forbidden"]
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(_report(defaults={"compare": {"include_arguments": ["amount"]}}))
    assert _locs(excinfo) == [("defaults", "compare", "include_arguments", 0)]


@pytest.mark.parametrize("status", ["ok", "PASSED", 1])
def test_suite_status_accepts_only_the_four_values(status: object) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(_report(suite_status=status))
    assert _locs(excinfo) == [("suite_status",)]
    assert _types(excinfo) == ["literal_error"]
    assert get_args(Report.model_fields["suite_status"].annotation) == STATUSES


# --- AD-3: unknown fields and frozen at every level -------------------------------------


def test_unknown_top_level_key_is_rejected_naming_it() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(_report(summary="all good"))
    assert _locs(excinfo) == [("summary",)]
    assert _types(excinfo) == ["extra_forbidden"]


def test_unknown_keys_nested_anywhere_are_rejected_at_their_path() -> None:
    data = _report()
    data["counts"]["total"] = 1
    data["scenarios"][0]["elapsed_ms"] = 5
    data["scenarios"][0]["assertions"][0]["traceback"] = "..."
    data["scenarios"][0]["trace"]["hostname"] = "ci-1"
    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(data)
    assert set(_locs(excinfo)) == {
        ("counts", "total"),
        ("scenarios", 0, "elapsed_ms"),
        ("scenarios", 0, "assertions", 0, "traceback"),
        ("scenarios", 0, "trace", "hostname"),
    }
    assert set(_types(excinfo)) == {"extra_forbidden"}


@pytest.mark.parametrize(
    ("model", "data"),
    [
        (Report, SEED),
        (SchemaVersions, {"suite": 1, "trace": 1}),
        (Comparison, _comparison()),
        (StatusChange, {"scenario_id": "a", "baseline": "passed", "current": "failed"}),
        (AssertionIdChange, {"scenario_id": "a", "added": ["x"], "removed": []}),
        (FailedAssertionChange, {"scenario_id": "a", "newly_failing": ["x"], "newly_passing": []}),
        (ToolSequenceChange, {"scenario_id": "a", "baseline": ["t"], "current": []}),
        (EventCountChange, {"scenario_id": "a", "baseline_events": 4, "current_events": 5}),
        (ArgumentChange, {"scenario_id": "a", "path": "t.amount", "baseline": 1, "current": 2}),
        (DurationChange, {"scenario_id": "a", "baseline_ms": 1, "current_ms": 2}),
        (CostChange, {"scenario_id": "a", "baseline": 0.1, "current": 0.2}),
    ],
)
def test_every_model_is_frozen_and_forbids_unknown_fields(
    model: type[BaseModel], data: dict[str, Any]
) -> None:
    assert model.model_config.get("frozen") is True
    assert model.model_config.get("extra") == "forbid"
    assert "strict" not in model.model_config
    with pytest.raises(ValidationError) as excinfo:
        model.model_validate({**copy.deepcopy(data), "surprise": 1})
    assert _locs(excinfo) == [("surprise",)]
    assert _types(excinfo) == ["extra_forbidden"]
    instance = model.model_validate(copy.deepcopy(data))
    first = next(iter(model.model_fields))
    with pytest.raises(ValidationError) as excinfo:
        setattr(instance, first, getattr(instance, first))
    assert _types(excinfo) == ["frozen_instance"]
    assert getattr(instance, first) == model.model_validate(copy.deepcopy(data)).__dict__[first]


def test_report_sequence_fields_are_tuples() -> None:
    report = Report.model_validate(SEED)
    assert isinstance(report.scenarios, tuple)
    with pytest.raises(AttributeError):
        report.scenarios.append(None)  # type: ignore[attr-defined]
    comparison = Comparison.model_validate(_comparison(added_scenarios=["a"]))
    assert comparison.added_scenarios == ("a",)
    assert isinstance(comparison.status_changes, tuple)


# --- criterion 3: Comparison ------------------------------------------------------------


def test_comparison_exists_with_the_fields_of_criterion_3() -> None:
    assert tuple(Comparison.model_fields) == (
        "baseline_suite_status",
        "current_suite_status",
        "status_changes",
        "assertion_id_changes",
        "failed_assertion_changes",
        "tool_sequence_changes",
        "event_count_changes",
        "argument_changes",
        "added_scenarios",
        "removed_scenarios",
        "duration_changes",
        "cost_changes",
        "regressed",
        "statement",
    )
    assert Comparison.model_fields["regressed"].annotation is bool
    assert sorted(report_module.__all__) == report_module.__all__
    for name in report_module.__all__:
        assert hasattr(report_module, name)


def test_comparison_of_a_report_against_itself_has_empty_lists_and_the_statement() -> None:
    comparison = Comparison.model_validate(_comparison())
    assert comparison.baseline_suite_status == "passed"
    assert comparison.current_suite_status == "passed"
    assert comparison.status_changes == ()
    assert comparison.assertion_id_changes == ()
    assert comparison.failed_assertion_changes == ()
    assert comparison.tool_sequence_changes == ()
    assert comparison.event_count_changes == ()
    assert comparison.argument_changes == ()
    assert comparison.added_scenarios == ()
    assert comparison.removed_scenarios == ()
    assert comparison.duration_changes == ()
    assert comparison.cost_changes == ()
    assert comparison.regressed is False
    assert comparison.statement == STATEMENTS.compare_is_saved_data
    assert "exact comparison of saved data" in comparison.statement


def test_comparison_with_every_kind_of_change_validates() -> None:
    comparison = Comparison.model_validate(
        _comparison(
            baseline_suite_status="passed",
            current_suite_status="failed",
            status_changes=[{"scenario_id": "a", "baseline": "passed", "current": "failed"}],
            assertion_id_changes=[
                {"scenario_id": "a", "added": ["tool_called-2"], "removed": ["says-rejected"]}
            ],
            failed_assertion_changes=[
                {
                    "scenario_id": "a",
                    "newly_failing": ["tool_not_called-0"],
                    "newly_passing": ["tool_call_count-1"],
                }
            ],
            tool_sequence_changes=[
                {
                    "scenario_id": "b",
                    "baseline": ["lookup", "reject_expense"],
                    "current": ["lookup", "approve_expense"],
                }
            ],
            event_count_changes=[{"scenario_id": "b", "baseline_events": 4, "current_events": 6}],
            argument_changes=[
                {
                    "scenario_id": "b",
                    "path": "approve_expense.amount",
                    "baseline": 4000,
                    "current": [5000, 6000],
                }
            ],
            added_scenarios=["c"],
            removed_scenarios=["d"],
            duration_changes=[{"scenario_id": "a", "baseline_ms": 2000, "current_ms": 2500}],
            cost_changes=[{"scenario_id": "a", "baseline": 0.01, "current": 0.02}],
            regressed=True,
            statement=STATEMENTS.compare_is_saved_data,
        )
    )
    assert comparison.regressed is True
    assert comparison.status_changes == (
        StatusChange(scenario_id="a", baseline="passed", current="failed"),
    )
    assert comparison.assertion_id_changes[0].added == ("tool_called-2",)
    assert comparison.assertion_id_changes[0].removed == ("says-rejected",)
    assert comparison.failed_assertion_changes[0] == FailedAssertionChange(
        scenario_id="a", newly_failing=("tool_not_called-0",), newly_passing=("tool_call_count-1",)
    )
    assert comparison.tool_sequence_changes[0].current == ("lookup", "approve_expense")
    assert comparison.event_count_changes[0] == EventCountChange(
        scenario_id="b", baseline_events=4, current_events=6
    )
    assert comparison.argument_changes[0].path == "approve_expense.amount"
    assert comparison.argument_changes[0].baseline == 4000
    assert comparison.argument_changes[0].current == [5000, 6000]
    assert comparison.added_scenarios == ("c",)
    assert comparison.removed_scenarios == ("d",)
    assert comparison.duration_changes[0] == DurationChange(
        scenario_id="a", baseline_ms=2000, current_ms=2500
    )
    assert comparison.cost_changes[0] == CostChange(scenario_id="a", baseline=0.01, current=0.02)


@pytest.mark.parametrize("field", ["baseline_suite_status", "current_suite_status", "regressed"])
def test_comparison_required_fields_are_required(field: str) -> None:
    data = _comparison()
    del data[field]
    with pytest.raises(ValidationError) as excinfo:
        Comparison.model_validate(data)
    assert _locs(excinfo) == [(field,)]
    assert _types(excinfo) == ["missing"]


def test_regressed_must_be_a_boolean() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Comparison.model_validate(_comparison(regressed="maybe"))
    assert _locs(excinfo) == [("regressed",)]
    assert _types(excinfo) == ["bool_parsing"]


def test_statement_cannot_be_anything_but_the_fixed_saved_data_statement() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Comparison.model_validate(_comparison(statement="The agent is reproducible."))
    assert _locs(excinfo) == [("statement",)]
    assert _types(excinfo) == ["statement_fixed"]
    assert STATEMENTS.compare_is_saved_data in _errors(excinfo)[0][1]
    with pytest.raises(ValidationError) as excinfo:
        Comparison.model_validate(_comparison(statement=""))
    assert _types(excinfo) == ["statement_fixed"]


def test_change_records_reject_a_bad_status_or_path_naming_the_path() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Comparison.model_validate(
            _comparison(
                status_changes=[{"scenario_id": "a", "baseline": "passed", "current": "worse"}]
            )
        )
    assert _locs(excinfo) == [("status_changes", 0, "current")]
    assert _types(excinfo) == ["literal_error"]
    with pytest.raises(ValidationError) as excinfo:
        Comparison.model_validate(
            _comparison(
                argument_changes=[
                    {"scenario_id": "a", "path": "amount", "baseline": 1, "current": 2}
                ]
            )
        )
    assert _locs(excinfo) == [("argument_changes", 0, "path")]
    with pytest.raises(ValidationError) as excinfo:
        Comparison.model_validate(
            _comparison(
                duration_changes=[{"scenario_id": "a", "baseline_ms": -1, "current_ms": 1.5}]
            )
        )
    assert _locs(excinfo) == [
        ("duration_changes", 0, "baseline_ms"),
        ("duration_changes", 0, "current_ms"),
    ]
    assert _types(excinfo) == ["greater_than_equal", "int_type"]
    with pytest.raises(ValidationError) as excinfo:
        Comparison.model_validate(
            _comparison(
                event_count_changes=[
                    {"scenario_id": "a", "baseline_events": "4", "current_events": -1}
                ]
            )
        )
    assert _locs(excinfo) == [
        ("event_count_changes", 0, "baseline_events"),
        ("event_count_changes", 0, "current_events"),
    ]
    assert _types(excinfo) == ["int_type", "greater_than_equal"]
    with pytest.raises(ValidationError) as excinfo:
        Comparison.model_validate(
            _comparison(failed_assertion_changes=[{"scenario_id": "a", "newly_failing": ["x"]}])
        )
    assert _locs(excinfo) == [("failed_assertion_changes", 0, "newly_passing")]
    assert _types(excinfo) == ["missing"]


def test_cost_change_values_are_numbers_not_strings() -> None:
    change = CostChange.model_validate({"scenario_id": "a", "baseline": 1, "current": 0.5})
    assert (change.baseline, change.current) == (1.0, 0.5)
    with pytest.raises(ValidationError) as excinfo:
        CostChange.model_validate({"scenario_id": "a", "baseline": "1", "current": 0.5})
    assert _locs(excinfo) == [("baseline",)]
    assert _types(excinfo) == ["float_type"]


def test_change_record_scenario_ids_must_be_non_empty() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Comparison.model_validate(
            _comparison(
                added_scenarios=["a"],
                status_changes=[{"scenario_id": "", "baseline": "passed", "current": "failed"}],
            )
        )
    assert _locs(excinfo) == [("status_changes", 0, "scenario_id")]
    assert _types(excinfo) == ["string_too_short"]


def test_null_comparison_lists_read_as_empty_and_null_regressed_keeps_its_error() -> None:
    comparison = Comparison.model_validate(
        _comparison(
            status_changes=None,
            assertion_id_changes=None,
            failed_assertion_changes=None,
            tool_sequence_changes=None,
            event_count_changes=None,
            argument_changes=None,
            added_scenarios=None,
            removed_scenarios=None,
            duration_changes=None,
            cost_changes=None,
            statement=None,
        )
    )
    assert comparison == Comparison.model_validate(_comparison())
    with pytest.raises(ValidationError) as excinfo:
        Comparison.model_validate(_comparison(regressed=None))
    assert _locs(excinfo) == [("regressed",)]
    assert _types(excinfo) == ["bool_type"]


def test_non_finite_argument_values_are_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Comparison.model_validate(
            _comparison(
                argument_changes=[
                    {"scenario_id": "a", "path": "t.x", "baseline": 1.0, "current": float("inf")}
                ]
            )
        )
    assert all(loc[:3] == ("argument_changes", 0, "current") for loc in _locs(excinfo))
    assert "finite_number" in _types(excinfo)
    with pytest.raises(ValidationError) as excinfo:
        Comparison.model_validate(
            _comparison(
                cost_changes=[{"scenario_id": "a", "baseline": 0.1, "current": float("nan")}]
            )
        )
    assert _locs(excinfo) == [("cost_changes", 0, "current")]
    assert _types(excinfo) == ["finite_number"]


# --- criterion 4: Canonical serialization (AD-11) ---------------------------------------


def _top_level_keys(text: str) -> list[str]:
    """The keys at two-space indent, in the order the text writes them."""
    return re.findall(r'^  "([^"]+)":', text, flags=re.MULTILINE)


def _keys_at_indent(text: str, indent: int) -> list[str]:
    return re.findall(rf'^ {{{indent}}}"([^"]+)":', text, flags=re.MULTILINE)


def test_canonical_dumps_writes_defaults_scenarios_and_trace_keys_in_sorted_order() -> None:
    report = Report.model_validate(SEED)
    text = dumps(report.model_dump(mode="json"))
    top = _top_level_keys(text)
    assert top == sorted(top)
    assert top == [
        "counts",
        "created_at",
        "defaults",
        "execution_failed",
        "package_version",
        "run_id",
        "scenarios",
        "schema_versions",
        "suite_id",
        "suite_status",
        "version",
    ]
    defaults_keys = _keys_at_indent(text.split('  "defaults": {', 1)[1].split("\n  }", 1)[0], 4)
    assert defaults_keys == ["adapter", "compare", "fail_on_missing_trace", "fixture", "redact"]
    scenario_text = text.split('  "scenarios": [', 1)[1]
    scenario_keys = _keys_at_indent(scenario_text, 6)
    assert scenario_keys == [
        "assertions",
        "cost",
        "counts",
        "duration_ms",
        "execution_error",
        "scenario_id",
        "skip_reason",
        "status",
        "trace",
    ]
    trace_text = scenario_text.split('      "trace": {', 1)[1]
    trace_keys = _keys_at_indent(trace_text, 8)
    assert trace_keys == sorted(trace_keys)
    assert trace_keys[:3] == ["adapter", "agent", "capture"]
    assert trace_keys[-1] == "version"
    assert text.endswith("}\n")
    assert "\r" not in text


def test_canonical_dumps_writes_every_optional_field_as_null() -> None:
    data = _report()
    data["scenarios"][0]["trace"] = None
    data["scenarios"][0]["assertions"][0]["detail"] = None
    del data["scenarios"][0]["skip_reason"]
    del data["scenarios"][0]["execution_error"]
    del data["scenarios"][0]["cost"]
    text = dumps(Report.model_validate(data).model_dump(mode="json"))
    assert '      "cost": null,\n' in text
    assert '      "duration_ms": null,\n' in text
    assert '      "execution_error": null,\n' in text
    assert '      "skip_reason": null,\n' in text
    assert '      "trace": null\n' in text
    assert '          "detail": null,\n' in text
    assert '    "adapter": "fixture",\n' in text
    assert "None" not in text
    assert Report.model_validate(json.loads(text)) == Report.model_validate(data)


def test_canonical_dumps_of_an_embedded_trace_writes_every_event_key() -> None:
    text = dumps(Report.model_validate(SEED).model_dump(mode="json"))
    assert '            "duration_ms": null,\n' in text
    assert '            "error": null,\n' in text
    assert '            "metadata": {},\n' in text
    assert '            "redacted": false,\n' in text


def test_canonical_dumps_is_stable_across_key_insertion_order() -> None:
    shuffled = {key: SEED[key] for key in reversed(list(SEED))}
    assert dumps(Report.model_validate(shuffled).model_dump(mode="json")) == dumps(
        Report.model_validate(SEED).model_dump(mode="json")
    )


# --- AD-11: the volatile paths name real Report fields ---------------------------------


def test_volatile_paths_resolve_to_real_report_fields() -> None:
    for path in VOLATILE_PATHS:
        head, _, tail = path.partition(".")
        if head == "scenarios[*]":
            field, _, rest = tail.partition(".")
            assert field in ScenarioResult.model_fields, path
            if field == "trace":
                assert rest, path
                trace_field, _, event_field = rest.partition(".")
                if trace_field == "events[*]":
                    assert event_field in TraceEvent.model_fields, path
                else:
                    assert trace_field in Trace.model_fields, path
                    assert event_field == "", path
            else:
                assert rest == "", path
        else:
            assert tail == "", path
            assert head in Report.model_fields, path
    assert {"run_id", "created_at", "package_version"} <= set(VOLATILE_PATHS)
    # Scenario-level timing and cost are volatile (AC-22.2), like the trace's own.
    assert "scenarios[*].cost" in VOLATILE_PATHS
    assert "scenarios[*].duration_ms" in VOLATILE_PATHS


# --- AD-4: the generated JSON Schema ----------------------------------------------------


def test_version_exports_an_enum_of_the_supported_report_versions() -> None:
    prop = Report.model_json_schema()["properties"]["version"]
    assert prop["type"] == "integer"
    assert prop["enum"] == list(SUPPORTED_VERSIONS["report"]) == [1]


def test_json_schema_exports_status_enums_arrays_and_min_items() -> None:
    props = _schema_properties(Report.model_json_schema())
    assert props["Report.suite_status"]["enum"] == list(STATUSES)
    assert props["Report.scenarios"]["type"] == "array"
    assert props["Report.scenarios"]["minItems"] == 1
    assert props["Report.scenarios"]["items"] == {"$ref": "#/$defs/ScenarioResult"}
    assert props["Report.defaults"] == {
        "$ref": "#/$defs/SuiteDefaults",
        "description": "The Suite defaults snapshot, every field written; compare reads it.",
    }
    assert props["SchemaVersions.suite"]["minimum"] == 1
    comparison = _schema_properties(Comparison.model_json_schema())
    assert comparison["Comparison.baseline_suite_status"]["enum"] == list(STATUSES)
    assert comparison["Comparison.status_changes"]["type"] == "array"
    assert comparison["Comparison.regressed"]["type"] == "boolean"
    assert comparison["Comparison.statement"]["default"] == STATEMENTS.compare_is_saved_data
    assert comparison["StatusChange.current"]["enum"] == list(STATUSES)
    assert comparison["ArgumentChange.path"]["pattern"]


def test_every_field_of_the_report_and_comparison_models_has_a_description() -> None:
    own = {
        "Report",
        "SchemaVersions",
        "Comparison",
        "StatusChange",
        "AssertionIdChange",
        "FailedAssertionChange",
        "ToolSequenceChange",
        "EventCountChange",
        "ArgumentChange",
        "DurationChange",
        "CostChange",
    }
    props = {
        **_schema_properties(Report.model_json_schema()),
        **_schema_properties(Comparison.model_json_schema()),
    }
    assert own <= {name.split(".")[0] for name in props}
    missing = [
        name
        for name, prop in props.items()
        if name.split(".")[0] in own and not prop.get("description", "").strip()
    ]
    assert missing == []
    for model in (
        Report,
        SchemaVersions,
        Comparison,
        StatusChange,
        AssertionIdChange,
        FailedAssertionChange,
        ToolSequenceChange,
        EventCountChange,
        ArgumentChange,
        DurationChange,
        CostChange,
    ):
        for field, info in model.model_fields.items():
            assert info.description, f"{model.__name__}.{field}"
