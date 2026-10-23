"""``agentproof.models.result``: Assertion Result, Counts, Scenario Result, Suite Outcome.

Every test validates through ``model_validate(dict)``, the only path the engine's
consumers and ``loading.parse_report`` will use (AD-3). The embedded Trace is the spine's
Trace seed from ``test_trace``.
"""

import copy
import math
from typing import Any, get_args

import pytest
from pydantic import BaseModel, ValidationError

import agentproof.models.result as result_module
from agentproof.models.common import STATUSES, Status
from agentproof.models.result import (
    AssertionResult,
    Counts,
    ScenarioResult,
    SuiteOutcome,
    count_statuses,
    require_counts,
    require_execution_failed,
    require_non_empty,
    require_unique_ids,
)
from agentproof.models.trace import Trace

from .test_trace import SEED as TRACE_SEED

ZERO = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}


def _assertion(**overrides: Any) -> dict[str, Any]:
    """The spine seed's single Assertion Result with keys replaced; ``...`` removes a key."""
    data: dict[str, Any] = {
        "assertion_id": "tool_not_called-0",
        "type": "tool_not_called",
        "status": "failed",
        "message": "approve_expense was called (capture: complete)",
        "evidence": [1],
        "detail": {},
    }
    for key, value in overrides.items():
        if value is ...:
            data.pop(key, None)
        else:
            data[key] = value
    return data


def _scenario(*assertions: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    """A Scenario Result whose ``counts`` match ``assertions`` unless overridden."""
    results = list(assertions) or [_assertion()]
    tally = dict(ZERO)
    for result in results:
        tally[result["status"]] += 1
    data: dict[str, Any] = {
        "scenario_id": "reject-over-limit",
        "status": "failed",
        "skip_reason": None,
        "execution_error": None,
        "counts": tally,
        "assertions": results,
        "trace": copy.deepcopy(TRACE_SEED),
        "cost": None,
    }
    for key, value in overrides.items():
        if value is ...:
            data.pop(key, None)
        else:
            data[key] = value
    return data


def _outcome(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "scenarios": [_scenario()],
        "suite_status": "failed",
        "execution_failed": False,
        "evaluated_assertions": 1,
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
    """The stable error type codes the loader keys on."""
    return [error["type"] for error in excinfo.value.errors()]


def _schema_properties(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Every property of the root and of every ``$defs`` entry, keyed ``Model.field``."""
    found: dict[str, dict[str, Any]] = {}
    for name, definition in [(schema["title"], schema), *schema.get("$defs", {}).items()]:
        for field, prop in definition.get("properties", {}).items():
            found[f"{name}.{field}"] = prop
    return found


# --- criterion 1: the models exist with the named fields ---------------------------------


def test_result_models_exist_with_the_fields_of_criterion_1() -> None:
    assert tuple(AssertionResult.model_fields) == (
        "assertion_id",
        "type",
        "status",
        "message",
        "evidence",
        "detail",
    )
    assert tuple(ScenarioResult.model_fields) == (
        "scenario_id",
        "status",
        "skip_reason",
        "execution_error",
        "counts",
        "assertions",
        "trace",
        "duration_ms",
        "cost",
    )
    assert tuple(SuiteOutcome.model_fields) == (
        "scenarios",
        "suite_status",
        "execution_failed",
        "evaluated_assertions",
    )
    assert tuple(Counts.model_fields) == STATUSES


def test_public_names_are_exported() -> None:
    assert sorted(result_module.__all__) == result_module.__all__
    for name in result_module.__all__:
        assert hasattr(result_module, name)
    assert set(result_module.__all__) >= {
        "AssertionResult",
        "Counts",
        "ScenarioResult",
        "SuiteOutcome",
        "count_statuses",
    }


def test_spine_seed_assertion_result_validates_with_evidence_as_a_tuple_of_seqs() -> None:
    result = AssertionResult.model_validate(_assertion())
    assert result.assertion_id == "tool_not_called-0"
    assert result.type == "tool_not_called"
    assert result.status == "failed"
    assert result.message == "approve_expense was called (capture: complete)"
    assert result.evidence == (1,)
    assert isinstance(result.evidence, tuple)
    assert result.detail == {}


# --- criterion 1: status accepts only the four values (AC-17.1) -------------------------


@pytest.mark.parametrize("status", STATUSES)
def test_each_of_the_four_statuses_is_accepted(status: Status) -> None:
    assert AssertionResult.model_validate(_assertion(status=status)).status == status
    scenario = ScenarioResult.model_validate(_scenario(_assertion(status=status), status=status))
    assert scenario.status == status
    outcome = SuiteOutcome.model_validate(_outcome(suite_status=status))
    assert outcome.suite_status == status


@pytest.mark.parametrize("status", ["ok", "PASSED", "pass", 1, None, True])
def test_any_other_status_is_rejected_naming_the_field(status: object) -> None:
    with pytest.raises(ValidationError) as excinfo:
        AssertionResult.model_validate(_assertion(status=status))
    assert _locs(excinfo) == [("status",)]
    assert _types(excinfo) == ["literal_error"]
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(_scenario(status=status))
    assert _locs(excinfo) == [("status",)]
    with pytest.raises(ValidationError) as excinfo:
        SuiteOutcome.model_validate(_outcome(suite_status=status))
    assert _locs(excinfo) == [("suite_status",)]


def test_status_field_is_the_shared_status_literal() -> None:
    assert get_args(AssertionResult.model_fields["status"].annotation) == STATUSES
    assert get_args(ScenarioResult.model_fields["status"].annotation) == STATUSES
    assert get_args(SuiteOutcome.model_fields["suite_status"].annotation) == STATUSES


# --- criterion 1: assertion id, type, message, evidence, detail ------------------------


@pytest.mark.parametrize("field", ["assertion_id", "type", "status", "message", "evidence"])
def test_required_assertion_result_fields_are_required(field: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        AssertionResult.model_validate(_assertion(**{field: ...}))
    assert _locs(excinfo) == [(field,)]
    assert _types(excinfo) == ["missing"]


@pytest.mark.parametrize("field", ["assertion_id", "type"])
def test_empty_assertion_id_and_type_are_rejected(field: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        AssertionResult.model_validate(_assertion(**{field: ""}))
    assert _locs(excinfo) == [(field,)]
    assert _types(excinfo) == ["string_too_short"]


def test_type_is_any_non_empty_string_not_only_the_built_in_six() -> None:
    assert AssertionResult.model_validate(_assertion(type="my_plugin_check")).type == (
        "my_plugin_check"
    )


@pytest.mark.parametrize("evidence", [[], [1], [0, 3], [7, 7]])
def test_evidence_lists_of_seqs_validate_into_tuples(evidence: list[int]) -> None:
    result = AssertionResult.model_validate(_assertion(evidence=evidence))
    assert result.evidence == tuple(evidence)


@pytest.mark.parametrize(
    ("bad", "code"),
    [("1", "int_type"), (True, "int_type"), (1.0, "int_type"), (-1, "greater_than_equal")],
)
def test_evidence_items_must_be_exact_non_negative_integers(bad: object, code: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        AssertionResult.model_validate(_assertion(evidence=[0, bad]))
    assert _locs(excinfo) == [("evidence", 1)]
    assert _types(excinfo) == [code]


def test_evidence_must_be_a_list_not_a_single_seq() -> None:
    with pytest.raises(ValidationError) as excinfo:
        AssertionResult.model_validate(_assertion(evidence=1))
    assert _locs(excinfo) == [("evidence",)]
    assert _types(excinfo) == ["tuple_type"]


@pytest.mark.parametrize(
    "detail", [None, {}, {"expected": 1, "actual": [1, 2]}, "text", 3.5, [None, True]]
)
def test_detail_is_any_json_value_and_defaults_to_none(detail: object) -> None:
    assert AssertionResult.model_validate(_assertion(detail=detail)).detail == detail
    assert AssertionResult.model_validate(_assertion(detail=...)).detail is None


# --- criterion 1: Counts and count_statuses ----------------------------------------------


def test_counts_has_one_required_key_per_status() -> None:
    counts = Counts.model_validate({"passed": 2, "failed": 1, "error": 0, "skipped": 0})
    assert (counts.passed, counts.failed, counts.error, counts.skipped) == (2, 1, 0, 0)
    with pytest.raises(ValidationError) as excinfo:
        Counts.model_validate({"passed": 2, "failed": 1, "error": 0})
    assert _locs(excinfo) == [("skipped",)]
    assert _types(excinfo) == ["missing"]


@pytest.mark.parametrize(
    ("bad", "code"),
    [("1", "int_type"), (True, "int_type"), (1.0, "int_type"), (-1, "greater_than_equal")],
)
def test_counts_values_must_be_exact_non_negative_integers(bad: object, code: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Counts.model_validate({**ZERO, "failed": bad})
    assert _locs(excinfo) == [("failed",)]
    assert _types(excinfo) == [code]


def test_count_statuses_tallies_each_status_and_an_empty_iterable_is_all_zero() -> None:
    tally = count_statuses(["passed", "failed", "passed", "error", "skipped", "passed"])
    assert tally == Counts(passed=3, failed=1, error=1, skipped=1)
    assert count_statuses([]) == Counts(passed=0, failed=0, error=0, skipped=0)
    assert count_statuses(iter(["skipped"])) == Counts(passed=0, failed=0, error=0, skipped=1)


def test_require_counts_returns_matching_counts_and_raises_at_counts_otherwise() -> None:
    counts = Counts(passed=1, failed=0, error=0, skipped=0)
    assert require_counts(counts, ["passed"], title="Caller") is counts
    with pytest.raises(ValidationError) as excinfo:
        require_counts(counts, ["failed"], title="Caller")
    assert excinfo.value.title == "Caller"
    assert _locs(excinfo) == [("counts",)]
    assert _types(excinfo) == ["counts_mismatch"]
    (_, message), *_rest = _errors(excinfo)
    assert "'passed': 1" in message
    assert "'failed': 1" in message


def test_require_non_empty_raises_pydantics_too_short_at_the_named_field() -> None:
    require_non_empty("assertions", (1,), title="Caller")
    with pytest.raises(ValidationError) as excinfo:
        require_non_empty("assertions", (), title="Caller")
    assert excinfo.value.title == "Caller"
    assert _locs(excinfo) == [("assertions",)]
    assert _types(excinfo) == ["too_short"]
    assert _errors(excinfo)[0][1] == "Tuple should have at least 1 item after validation, not 0"


def test_require_unique_ids_points_at_the_later_duplicate_and_names_the_first() -> None:
    require_unique_ids("scenarios", ["a", "b"], "scenario_id", title="Caller")
    require_unique_ids("scenarios", [], "scenario_id", title="Caller")
    with pytest.raises(ValidationError) as excinfo:
        require_unique_ids("scenarios", ["a", "b", "a", "b"], "scenario_id", title="Caller")
    assert excinfo.value.title == "Caller"
    assert _locs(excinfo) == [("scenarios", 2, "scenario_id")]
    assert _types(excinfo) == ["duplicate_id"]
    assert _errors(excinfo)[0][1] == "duplicate scenario_id 'a' at scenarios[2] and scenarios[0]"


def test_require_execution_failed_names_the_first_scenario_with_an_error_or_none() -> None:
    clean = ScenarioResult.model_validate(_scenario())
    errored = ScenarioResult.model_validate(
        _scenario(
            _assertion(status="error"),
            scenario_id="broken",
            status="error",
            execution_error="adapter raised",
        )
    )
    require_execution_failed(False, [clean], title="Caller")
    require_execution_failed(True, [clean, errored], title="Caller")
    with pytest.raises(ValidationError) as excinfo:
        require_execution_failed(False, [clean, errored], title="Caller")
    assert excinfo.value.title == "Caller"
    assert _locs(excinfo) == [("execution_failed",)]
    assert _types(excinfo) == ["execution_failed_mismatch"]
    assert _errors(excinfo)[0][1] == (
        "execution_failed is false but scenarios[1] ('broken') sets execution_error"
    )
    with pytest.raises(ValidationError) as excinfo:
        require_execution_failed(True, [clean], title="Caller")
    assert _types(excinfo) == ["execution_failed_mismatch"]
    assert _errors(excinfo)[0][1] == (
        "execution_failed is true but no scenario sets execution_error"
    )


# --- criterion 1: ScenarioResult ---------------------------------------------------------


def test_scenario_result_validates_with_counts_matching_its_assertions() -> None:
    scenario = ScenarioResult.model_validate(
        _scenario(
            _assertion(assertion_id="a", status="passed"),
            _assertion(assertion_id="b", status="passed"),
            _assertion(assertion_id="c", status="failed"),
        )
    )
    assert scenario.scenario_id == "reject-over-limit"
    assert scenario.status == "failed"
    assert scenario.skip_reason is None
    assert scenario.execution_error is None
    assert scenario.counts == Counts(passed=2, failed=1, error=0, skipped=0)
    assert [result.assertion_id for result in scenario.assertions] == ["a", "b", "c"]
    assert isinstance(scenario.assertions, tuple)
    assert isinstance(scenario.trace, Trace)
    assert scenario.trace.run_id == "fixture-reject-over-limit"
    assert scenario.cost is None


def test_scenario_counts_mismatch_is_rejected_at_counts_naming_both_tallies() -> None:
    data = _scenario(
        _assertion(assertion_id="a", status="passed"),
        _assertion(assertion_id="b", status="passed"),
        _assertion(assertion_id="c", status="failed"),
    )
    data["counts"] = {"passed": 3, "failed": 1, "error": 0, "skipped": 0}
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(data)
    assert _locs(excinfo) == [("counts",)]
    assert _types(excinfo) == ["counts_mismatch"]
    message = _errors(excinfo)[0][1]
    assert "'passed': 3" in message
    assert "tally to" in message
    assert "'passed': 2, 'failed': 1" in message


def test_scenario_counts_mismatch_in_a_single_bucket_is_rejected() -> None:
    data = _scenario(_assertion(status="skipped"), status="skipped")
    data["counts"] = {"passed": 0, "failed": 0, "error": 1, "skipped": 0}
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(data)
    assert _types(excinfo) == ["counts_mismatch"]


def test_scenario_counts_are_required() -> None:
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(_scenario(counts=...))
    assert _locs(excinfo) == [("counts",)]
    assert _types(excinfo) == ["missing"]


def test_scenario_with_no_assertion_results_is_rejected_at_assertions() -> None:
    data = _scenario()
    data["assertions"] = []
    data["counts"] = dict(ZERO)
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(data)
    assert _locs(excinfo) == [("assertions",)]
    assert _types(excinfo) == ["too_short"]


def test_an_invalid_assertion_result_yields_only_its_own_error() -> None:
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(_scenario(_assertion(status="failed", evidence=["x"])))
    assert _locs(excinfo) == [("assertions", 0, "evidence", 0)]


def test_distinct_assertion_ids_validate_and_a_duplicate_is_rejected_at_the_later_one() -> None:
    ok = ScenarioResult.model_validate(
        _scenario(_assertion(assertion_id="a"), _assertion(assertion_id="b"))
    )
    assert [result.assertion_id for result in ok.assertions] == ["a", "b"]
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(
            _scenario(
                _assertion(assertion_id="a"),
                _assertion(assertion_id="b"),
                _assertion(assertion_id="a"),
            )
        )
    assert excinfo.value.title == "ScenarioResult"
    assert _locs(excinfo) == [("assertions", 2, "assertion_id")]
    assert _types(excinfo) == ["duplicate_id"]
    assert "assertions[2] and assertions[0]" in _errors(excinfo)[0][1]


def test_skip_reason_and_execution_error_are_optional_strings() -> None:
    skipped = ScenarioResult.model_validate(
        _scenario(_assertion(status="skipped"), status="skipped", skip_reason="not today")
    )
    assert skipped.skip_reason == "not today"
    errored = ScenarioResult.model_validate(
        _scenario(
            _assertion(status="error"), status="error", execution_error="trace missing", trace=None
        )
    )
    assert errored.execution_error == "trace missing"
    assert errored.trace is None
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(_scenario(skip_reason=3))
    assert _locs(excinfo) == [("skip_reason",)]
    assert _types(excinfo) == ["string_type"]


@pytest.mark.parametrize("field", ["skip_reason", "execution_error"])
def test_empty_skip_reason_or_execution_error_is_rejected(field: str) -> None:
    status = "skipped" if field == "skip_reason" else "error"
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(
            _scenario(_assertion(status=status), status=status, **{field: ""})
        )
    assert _locs(excinfo) == [(field,)]
    assert _types(excinfo) == ["string_too_short"]


def test_skip_reason_and_execution_error_cannot_both_be_set() -> None:
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(
            _scenario(
                _assertion(status="skipped"),
                status="skipped",
                skip_reason="not today",
                execution_error="adapter raised",
            )
        )
    assert _locs(excinfo) == [("execution_error",)]
    assert _types(excinfo) == ["skip_reason_and_execution_error"]


@pytest.mark.parametrize("status", ["passed", "failed", "error"])
def test_skip_reason_requires_status_skipped(status: Status) -> None:
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(
            _scenario(_assertion(status=status), status=status, skip_reason="not today")
        )
    assert _locs(excinfo) == [("skip_reason",)]
    assert _types(excinfo) == ["skip_reason_requires_skipped"]
    assert f"status is {status}" in _errors(excinfo)[0][1]


@pytest.mark.parametrize("status", ["passed", "failed", "skipped"])
def test_execution_error_requires_status_error(status: Status) -> None:
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(
            _scenario(_assertion(status=status), status=status, execution_error="trace missing")
        )
    assert _locs(excinfo) == [("execution_error",)]
    assert _types(excinfo) == ["execution_error_requires_error"]
    assert f"status is {status}" in _errors(excinfo)[0][1]


@pytest.mark.parametrize("status", STATUSES)
def test_a_status_without_a_cause_is_always_allowed(status: Status) -> None:
    # ``skipped`` and ``error`` results need no cause string: the engine may skip through
    # ``fail_on_missing_trace: false`` and an assertion may error on its own (AC-17.3).
    scenario = ScenarioResult.model_validate(_scenario(_assertion(status=status), status=status))
    assert scenario.skip_reason is None
    assert scenario.execution_error is None


@pytest.mark.parametrize(("duration", "stored"), [(0, 0), (2500, 2500), (None, None)])
def test_duration_ms_is_an_optional_whole_millisecond_count(
    duration: object, stored: object
) -> None:
    assert ScenarioResult.model_validate(_scenario(duration_ms=duration)).duration_ms == stored
    assert ScenarioResult.model_validate(_scenario()).duration_ms is None


@pytest.mark.parametrize(
    ("bad", "code"), [("5", "int_type"), (1.5, "int_type"), (-1, "greater_than_equal")]
)
def test_duration_ms_rejects_strings_fractions_and_negatives(bad: object, code: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(_scenario(duration_ms=bad))
    assert _locs(excinfo) == [("duration_ms",)]
    assert _types(excinfo) == [code]


def test_trace_is_a_trace_or_none_and_a_malformed_trace_is_rejected_at_its_path() -> None:
    assert ScenarioResult.model_validate(_scenario(trace=...)).trace is None
    broken = copy.deepcopy(TRACE_SEED)
    broken["events"][1]["seq"] = 5
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(_scenario(trace=broken))
    assert _locs(excinfo) == [("trace", "events", 1, "seq")]
    assert _types(excinfo) == ["seq_not_contiguous"]


@pytest.mark.parametrize(("cost", "stored"), [(0.25, 0.25), (3, 3.0), (None, None)])
def test_cost_is_an_optional_number(cost: object, stored: object) -> None:
    scenario = ScenarioResult.model_validate(_scenario(cost=cost))
    assert scenario.cost == stored
    assert type(scenario.cost) is type(stored)


@pytest.mark.parametrize("cost", ["0.25", True])
def test_cost_rejects_numeric_strings_and_booleans(cost: object) -> None:
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(_scenario(cost=cost))
    assert _locs(excinfo) == [("cost",)]
    assert _types(excinfo) == ["float_type"]


# --- criterion 1: SuiteOutcome ----------------------------------------------------------


def test_suite_outcome_validates_with_the_fields_of_criterion_1() -> None:
    outcome = SuiteOutcome.model_validate(_outcome())
    assert len(outcome.scenarios) == 1
    assert isinstance(outcome.scenarios, tuple)
    assert isinstance(outcome.scenarios[0], ScenarioResult)
    assert outcome.suite_status == "failed"
    assert outcome.execution_failed is False
    assert outcome.evaluated_assertions == 1


@pytest.mark.parametrize(
    "field", ["scenarios", "suite_status", "execution_failed", "evaluated_assertions"]
)
def test_every_suite_outcome_field_is_required(field: str) -> None:
    data = _outcome()
    del data[field]
    with pytest.raises(ValidationError) as excinfo:
        SuiteOutcome.model_validate(data)
    assert _locs(excinfo) == [(field,)]
    assert _types(excinfo) == ["missing"]


@pytest.mark.parametrize(
    ("bad", "code"), [("2", "int_type"), (-1, "greater_than_equal"), (1.0, "int_type")]
)
def test_evaluated_assertions_is_an_exact_non_negative_integer(bad: object, code: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        SuiteOutcome.model_validate(_outcome(evaluated_assertions=bad))
    assert _locs(excinfo) == [("evaluated_assertions",)]
    assert _types(excinfo) == [code]


def test_suite_outcome_with_no_scenarios_is_rejected_at_scenarios() -> None:
    with pytest.raises(ValidationError) as excinfo:
        SuiteOutcome.model_validate(_outcome(scenarios=[]))
    assert _locs(excinfo) == [("scenarios",)]
    assert _types(excinfo) == ["too_short"]


def test_a_scenario_counts_mismatch_inside_an_outcome_is_located_at_the_scenario() -> None:
    bad = _scenario(scenario_id="other")
    bad["counts"] = {"passed": 1, "failed": 0, "error": 0, "skipped": 0}
    with pytest.raises(ValidationError) as excinfo:
        SuiteOutcome.model_validate(_outcome(scenarios=[_scenario(), bad]))
    assert _locs(excinfo) == [("scenarios", 1, "counts")]
    assert _types(excinfo) == ["counts_mismatch"]


def test_distinct_scenario_ids_validate_and_a_duplicate_is_rejected_at_the_later_one() -> None:
    ok = SuiteOutcome.model_validate(
        _outcome(scenarios=[_scenario(scenario_id="a"), _scenario(scenario_id="b")])
    )
    assert [scenario.scenario_id for scenario in ok.scenarios] == ["a", "b"]
    with pytest.raises(ValidationError) as excinfo:
        SuiteOutcome.model_validate(
            _outcome(
                scenarios=[
                    _scenario(scenario_id="a"),
                    _scenario(scenario_id="b"),
                    _scenario(scenario_id="a"),
                ]
            )
        )
    assert excinfo.value.title == "SuiteOutcome"
    assert _locs(excinfo) == [("scenarios", 2, "scenario_id")]
    assert _types(excinfo) == ["duplicate_id"]


def _errored_scenario(scenario_id: str = "broken") -> dict[str, Any]:
    return _scenario(
        _assertion(status="error"),
        scenario_id=scenario_id,
        status="error",
        execution_error="adapter raised",
        trace=None,
    )


def test_execution_failed_true_with_an_execution_error_validates() -> None:
    outcome = SuiteOutcome.model_validate(
        _outcome(scenarios=[_scenario(), _errored_scenario()], execution_failed=True)
    )
    assert outcome.execution_failed is True
    assert outcome.scenarios[1].execution_error == "adapter raised"


def test_execution_failed_false_with_an_execution_error_is_rejected_naming_the_scenario() -> None:
    with pytest.raises(ValidationError) as excinfo:
        SuiteOutcome.model_validate(
            _outcome(scenarios=[_scenario(), _errored_scenario()], execution_failed=False)
        )
    assert _locs(excinfo) == [("execution_failed",)]
    assert _types(excinfo) == ["execution_failed_mismatch"]
    assert "scenarios[1] ('broken')" in _errors(excinfo)[0][1]


def test_execution_failed_true_without_an_execution_error_is_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        SuiteOutcome.model_validate(_outcome(execution_failed=True))
    assert _locs(excinfo) == [("execution_failed",)]
    assert _types(excinfo) == ["execution_failed_mismatch"]
    assert "no scenario sets execution_error" in _errors(excinfo)[0][1]


# --- AD-3: frozen and forbid-unknown at every level -------------------------------------


@pytest.mark.parametrize(
    ("model", "data"),
    [
        (AssertionResult, _assertion()),
        (Counts, dict(ZERO)),
        (ScenarioResult, _scenario()),
        (SuiteOutcome, _outcome()),
    ],
)
def test_every_model_is_frozen_and_forbids_unknown_fields(
    model: type[BaseModel], data: dict[str, Any]
) -> None:
    assert model.model_config.get("frozen") is True
    assert model.model_config.get("extra") == "forbid"
    assert "strict" not in model.model_config
    with pytest.raises(ValidationError) as excinfo:
        model.model_validate({**data, "surprise": 1})
    assert _locs(excinfo) == [("surprise",)]
    assert _types(excinfo) == ["extra_forbidden"]
    instance = model.model_validate(data)
    first = next(iter(model.model_fields))
    with pytest.raises(ValidationError) as excinfo:
        setattr(instance, first, getattr(instance, first))
    assert _types(excinfo) == ["frozen_instance"]


def test_unknown_fields_nested_in_a_scenario_are_rejected_at_their_path() -> None:
    data = _scenario()
    data["assertions"][0]["traceback"] = "..."
    data["counts"]["total"] = 1
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(data)
    assert set(_locs(excinfo)) == {("counts", "total"), ("assertions", 0, "traceback")}
    assert set(_types(excinfo)) == {"extra_forbidden"}


def test_sequence_fields_are_tuples_that_cannot_be_appended_to() -> None:
    scenario = ScenarioResult.model_validate(_scenario())
    with pytest.raises(AttributeError):
        scenario.assertions.append(None)  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        scenario.assertions[0].evidence.append(2)  # type: ignore[attr-defined]
    assert hash(scenario.assertions[0].model_copy(update={"detail": None})) is not None


def test_json_mode_dump_writes_arrays_and_round_trips() -> None:
    scenario = ScenarioResult.model_validate(_scenario())
    dumped = scenario.model_dump(mode="json")
    assert isinstance(dumped["assertions"], list)
    assert dumped["assertions"][0]["evidence"] == [1]
    assert ScenarioResult.model_validate(dumped) == scenario


# --- AD-19: null equals absent for fields with a default --------------------------------


def test_null_optional_fields_read_as_their_defaults() -> None:
    scenario = ScenarioResult.model_validate(
        _scenario(
            _assertion(detail=None),
            skip_reason=None,
            execution_error=None,
            trace=None,
            duration_ms=None,
            cost=None,
        )
    )
    assert scenario.skip_reason is None
    assert scenario.execution_error is None
    assert scenario.trace is None
    assert scenario.duration_ms is None
    assert scenario.cost is None
    assert scenario.assertions[0].detail is None
    assert scenario == ScenarioResult.model_validate(
        _scenario(
            _assertion(detail=...),
            skip_reason=...,
            execution_error=...,
            trace=...,
            duration_ms=...,
            cost=...,
        )
    )


@pytest.mark.parametrize(
    ("model", "data", "field"),
    [
        (AssertionResult, _assertion(), "evidence"),
        (AssertionResult, _assertion(), "message"),
        (ScenarioResult, _scenario(), "scenario_id"),
        (ScenarioResult, _scenario(), "counts"),
        (ScenarioResult, _scenario(), "assertions"),
        (SuiteOutcome, _outcome(), "execution_failed"),
    ],
)
def test_null_for_a_required_field_keeps_its_error(
    model: type[BaseModel], data: dict[str, Any], field: str
) -> None:
    with pytest.raises(ValidationError) as excinfo:
        model.model_validate({**data, field: None})
    assert _locs(excinfo) == [(field,)]
    assert _types(excinfo) != ["missing"]


def test_null_for_an_unknown_key_is_still_an_unknown_key() -> None:
    with pytest.raises(ValidationError) as excinfo:
        AssertionResult.model_validate(_assertion(elapsed_ms=None))
    assert _locs(excinfo) == [("elapsed_ms",)]
    assert _types(excinfo) == ["extra_forbidden"]


# --- epic R4: non-finite numbers --------------------------------------------------------


@pytest.mark.parametrize("number", [math.nan, math.inf, -math.inf])
def test_non_finite_numbers_in_detail_and_cost_are_rejected(number: float) -> None:
    with pytest.raises(ValidationError) as excinfo:
        AssertionResult.model_validate(_assertion(detail={"actual": [number]}))
    assert all(loc[0] == "detail" for loc in _locs(excinfo))
    assert "finite_number" in _types(excinfo)
    with pytest.raises(ValidationError) as excinfo:
        ScenarioResult.model_validate(_scenario(cost=number))
    assert _locs(excinfo) == [("cost",)]
    assert _types(excinfo) == ["finite_number"]


# --- AD-4: the generated JSON Schema ----------------------------------------------------


def test_every_field_of_the_result_models_has_a_description() -> None:
    props = _schema_properties(SuiteOutcome.model_json_schema())
    own = {"SuiteOutcome", "ScenarioResult", "AssertionResult", "Counts"}
    assert own <= {name.split(".")[0] for name in props}
    missing = [
        name
        for name, prop in props.items()
        if name.split(".")[0] in own and not prop.get("description", "").strip()
    ]
    assert missing == []
    for model in (AssertionResult, Counts, ScenarioResult, SuiteOutcome):
        for field, info in model.model_fields.items():
            assert info.description, f"{model.__name__}.{field}"


def test_json_schema_exports_status_enums_arrays_and_min_items() -> None:
    props = _schema_properties(SuiteOutcome.model_json_schema())
    assert props["AssertionResult.status"]["enum"] == list(STATUSES)
    assert props["ScenarioResult.status"]["enum"] == list(STATUSES)
    assert props["SuiteOutcome.suite_status"]["enum"] == list(STATUSES)
    assert props["AssertionResult.evidence"]["type"] == "array"
    assert props["AssertionResult.evidence"]["items"] == {"minimum": 0, "type": "integer"}
    assert props["ScenarioResult.assertions"]["type"] == "array"
    assert props["ScenarioResult.assertions"]["minItems"] == 1
    assert props["SuiteOutcome.scenarios"]["type"] == "array"
    assert props["SuiteOutcome.scenarios"]["minItems"] == 1
    assert props["Counts.passed"] == {
        "description": "How many Assertion Results have status passed.",
        "minimum": 0,
        "title": "Passed",
        "type": "integer",
    }
    assert props["SuiteOutcome.evaluated_assertions"]["minimum"] == 0
    assert props["ScenarioResult.duration_ms"]["anyOf"] == [
        {"minimum": 0, "type": "integer"},
        {"type": "null"},
    ]
    assert props["ScenarioResult.skip_reason"]["anyOf"] == [
        {"minLength": 1, "type": "string"},
        {"type": "null"},
    ]
