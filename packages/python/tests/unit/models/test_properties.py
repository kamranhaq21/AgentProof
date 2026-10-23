"""Property tests over the models and the Canonical serializer (story 2.6).

Criterion 1 (round trip): ``model_validate(json.loads(dumps(model_dump(mode="json"))))``
is the identity for generated ``JsonValue``s, Traces, Reports, and Suites, 200 examples
each. Criterion 2 (null versus absent): a Trace generated with every optional field
omitted serializes with every field present, ``null`` where the default is ``None``, and
reads back equal; the same input with explicit ``null``s validates to an equal object.
Criterion 3 (non-finite numbers): NaN and infinity anywhere inside a tool argument, an
event payload, a Suite input, a Final Output, a result detail, a cost, or a Comparison
value raise a ``ValidationError`` whose location names the path. Criterion 4 (Unicode):
generated strings with non-ASCII, combining characters, and newlines survive the round
trip exactly and ``dumps`` is byte-identical across calls and under key-order shuffles.

The strategies live in ``strategies.py`` and produce the JSON shape (AD-3). Every property
sets ``max_examples`` explicitly; the profile in ``tests/conftest.py`` derandomizes and
disables the example database. The non-finite properties start from a fixed minimal
artifact and generate only the hole, which keeps the file fast. A property that exposes a
model defect is marked ``xfail(strict=True)`` with a pointer to the finding; the models
themselves are out of this story's scope.
"""

import copy
import json
import math
from collections.abc import Sequence
from typing import Any

import pytest
from hypothesis import Phase, given, settings
from hypothesis import strategies as st
from pydantic import BaseModel, ValidationError

from agentproof.models.canonical import dumps
from agentproof.models.common import JsonValue
from agentproof.models.report import Comparison, Report
from agentproof.models.suite import Suite
from agentproof.models.trace import (
    AdapterInfo,
    AgentInfo,
    Capture,
    Environment,
    ModelInfo,
    RedactionState,
    Trace,
    TraceEvent,
)

from .strategies import (
    HolePath,
    JsonObject,
    argument_paths,
    json_values,
    json_values_with_a_hole,
    non_ascii_texts,
    path_segments,
    report_dicts,
    suite_dicts,
    texts,
    timestamps,
    trace_dicts,
)

# An xfail property is expected to fail on its first examples; skipping the shrink phase keeps
# the expected failure from costing a minute of minimization.
EXPECTED_FAILURE = settings(max_examples=20, phases=(Phase.generate,))

NON_FINITE = st.sampled_from([math.nan, math.inf, -math.inf])

# Finding F1: routed to stories 2.7/3.3 by the orchestrator (deferred-work.md entry added by
# story 2.5's implementer); see the Implementation Notes of the story 2.6 plan.
F1 = (
    "F1: Suite.model_dump(mode='json') writes 'skip': null for an unskipped Scenario and "
    "Scenario._present_skip_is_a_reason rejects that null on re-validation (AD-19)"
)
# Finding F2: see the Implementation Notes of the story 2.6 plan and deferred-work.md.
F2 = (
    "F2: _null_means_absent is applied only to Trace and TraceEvent, so an explicit null for a "
    "nested field with a non-null default (capture.tool_calls, redaction.*) is rejected (AD-19)"
)

MIN_T = "2026-10-22T13:05:00+00:00"


def _min_trace() -> JsonObject:
    return {
        "version": 1,
        "run_id": "r",
        "scenario_id": "s",
        "started_at": MIN_T,
        "ended_at": MIN_T,
        "agent": {"name": "a"},
        "adapter": {"name": "x", "version": "1"},
        "events": [],
    }


def _min_suite() -> JsonObject:
    return {
        "version": 1,
        "suite": "s",
        "scenarios": [
            {
                "id": "a",
                "skip": "r",
                "input": {},
                "assertions": [{"type": "tool_called", "tool": "t"}],
            }
        ],
    }


def _min_report() -> JsonObject:
    counts = {"passed": 1, "failed": 0, "error": 0, "skipped": 0}
    return {
        "version": 1,
        "suite_id": "s",
        "run_id": "r",
        "created_at": MIN_T,
        "package_version": "0",
        "schema_versions": {"suite": 1, "trace": 1},
        "defaults": {},
        "suite_status": "passed",
        "execution_failed": False,
        "counts": counts,
        "scenarios": [
            {
                "scenario_id": "a",
                "status": "passed",
                "counts": counts,
                "assertions": [
                    {
                        "assertion_id": "x",
                        "type": "t",
                        "status": "passed",
                        "message": "m",
                        "evidence": [],
                    }
                ],
            }
        ],
    }


# --- helpers ---------------------------------------------------------------------------------


def _round_trip[M: BaseModel](model: type[M], data: JsonObject) -> tuple[M, str, M]:
    """Validate ``data``, dump it to Canonical text, validate the text; return all three."""
    original = model.model_validate(data)
    text = dumps(original.model_dump(mode="json"))
    again = model.model_validate(json.loads(text))
    return original, text, again


def _errors(excinfo: pytest.ExceptionInfo[ValidationError]) -> list[dict[str, Any]]:
    return excinfo.value.errors(include_url=False)


def _locs_and_types(excinfo: pytest.ExceptionInfo[ValidationError]) -> list[tuple[Any, str]]:
    return [(tuple(error["loc"]), error["type"]) for error in _errors(excinfo)]


def _is_subsequence(expected: Sequence[object], loc: Sequence[object]) -> bool:
    """Whether ``expected`` appears in ``loc`` in order, with other items in between.

    Under ``MODEL_CONFIG`` a ``JsonValue`` error location interleaves the path with the
    union branch labels (``'float'``, ``'dict[str,...]'`` ...); the path is still there.
    """
    position = 0
    for item in loc:
        if position < len(expected) and item == expected[position]:
            position += 1
    return position == len(expected)


def _assert_finite_number_error_at(
    excinfo: pytest.ExceptionInfo[ValidationError], path: Sequence[object]
) -> None:
    """Some ``finite_number`` error has ``path`` in its location, in order."""
    finite = [error for error in _errors(excinfo) if error["type"] == "finite_number"]
    assert finite, _locs_and_types(excinfo)
    assert any(_is_subsequence(path, error["loc"]) for error in finite), [
        error["loc"] for error in finite
    ]


def _inner_path_text(path: HolePath) -> str:
    """How ``models.trace._require_finite`` names the path inside a payload."""
    return ".".join(str(item) for item in path) or "the value itself"


def _none_default_fields(model: type[BaseModel]) -> list[str]:
    return [
        name
        for name, field in model.model_fields.items()
        if not field.is_required() and field.default is None
    ]


def _optional_fields(model: type[BaseModel]) -> list[str]:
    return [name for name, field in model.model_fields.items() if not field.is_required()]


def _null_for_absent(trace: JsonObject) -> JsonObject:
    """A copy of ``trace`` with an explicit ``null`` for every optional key it leaves out.

    Covers the Trace- and event-level fields (``_null_means_absent`` drops those whatever
    their default) and the nested fields whose default is already ``None``.
    """
    data = copy.deepcopy(trace)
    for name in _optional_fields(Trace):
        data.setdefault(name, None)
    for name in _none_default_fields(AgentInfo):
        data["agent"].setdefault(name, None)
    for key, nested in (("model", ModelInfo), ("environment", Environment)):
        if isinstance(data.get(key), dict):
            for name in _none_default_fields(nested):
                data[key].setdefault(name, None)
    for event in data["events"]:
        for name in _optional_fields(TraceEvent):
            event.setdefault(name, None)
        if isinstance(event.get("tool"), dict):
            event["tool"].setdefault("call_id", None)
    return data


@st.composite
def shuffled_pairs(draw: st.DrawFn) -> tuple[JsonValue, JsonValue]:
    """A ``JsonValue`` and an equal copy whose every object has a permuted insertion order."""
    value = draw(json_values())

    def shuffle(item: JsonValue) -> JsonValue:
        if isinstance(item, dict):
            keys = draw(st.permutations(list(item)))
            return {key: shuffle(item[key]) for key in keys}
        if isinstance(item, list):
            return [shuffle(element) for element in item]
        return item

    return value, shuffle(value)


# --- criterion 1: round trip ---------------------------------------------------------------


@given(value=json_values())
@settings(max_examples=200)
def test_json_values_round_trip_through_canonical_dumps(value: JsonValue) -> None:
    text = dumps(value)
    again = json.loads(text)
    assert again == value
    assert dumps(again) == text


@given(trace=trace_dicts())
@settings(max_examples=200)
def test_trace_round_trips_through_canonical_dumps(trace: JsonObject) -> None:
    original, text, again = _round_trip(Trace, trace)
    assert again == original
    assert dumps(again.model_dump(mode="json")) == text


@given(report=report_dicts())
@settings(max_examples=200)
def test_report_round_trips_through_canonical_dumps(report: JsonObject) -> None:
    original, text, again = _round_trip(Report, report)
    assert again == original
    assert dumps(again.model_dump(mode="json")) == text


@given(suite=suite_dicts(skipped=True))
@settings(max_examples=200)
def test_suite_with_every_scenario_skipped_round_trips_through_canonical_dumps(
    suite: JsonObject,
) -> None:
    original, text, again = _round_trip(Suite, suite)
    assert again == original
    assert dumps(again.model_dump(mode="json")) == text


@pytest.mark.xfail(strict=True, raises=ValidationError, reason=F1)
@given(suite=suite_dicts(skipped=False))
@EXPECTED_FAILURE
def test_suite_with_an_unskipped_scenario_round_trips_through_canonical_dumps(
    suite: JsonObject,
) -> None:
    # xfail: finding F1 (see the story 2.6 plan; routed to stories 2.7/3.3 in deferred-work.md).
    original, _, again = _round_trip(Suite, suite)
    assert again == original


# --- criterion 2: null versus absent ---------------------------------------------------------


@given(trace=trace_dicts(presence=False))
@settings(max_examples=200)
def test_trace_with_optional_fields_omitted_writes_every_field_and_reads_back_equal(
    trace: JsonObject,
) -> None:
    original = Trace.model_validate(trace)
    dumped = original.model_dump(mode="json")

    assert set(dumped) == set(Trace.model_fields)
    assert set(dumped["agent"]) == set(AgentInfo.model_fields)
    assert set(dumped["adapter"]) == set(AdapterInfo.model_fields)
    assert set(dumped["capture"]) == set(Capture.model_fields)
    assert set(dumped["environment"]) == set(Environment.model_fields)
    assert set(dumped["redaction"]) == set(RedactionState.model_fields)
    for name in _none_default_fields(Trace):
        assert dumped[name] is None, name
    for name in _none_default_fields(AgentInfo):
        assert dumped["agent"][name] is None, name
    assert dumped["capture"] == {"tool_calls": "unknown"}
    assert dumped["environment"] == dict.fromkeys(Environment.model_fields)
    assert dumped["redaction"] == {"applied": False, "paths": [], "env_names": []}
    for event in dumped["events"]:
        assert set(event) == set(TraceEvent.model_fields)
        for name in _none_default_fields(TraceEvent):
            assert event[name] is None, name
        assert event["redacted"] is False
        assert event["metadata"] == {}

    text = dumps(dumped)
    again = Trace.model_validate(json.loads(text))
    assert again == original
    assert dumps(again.model_dump(mode="json")) == text


@given(trace=trace_dicts(presence=False))
@settings(max_examples=200)
def test_trace_with_explicit_nulls_equals_the_trace_with_the_fields_omitted(
    trace: JsonObject,
) -> None:
    with_nulls = _null_for_absent(trace)
    assert with_nulls != trace, "the explicit-null variant must add at least one key"
    assert Trace.model_validate(with_nulls) == Trace.model_validate(trace)


@given(trace=trace_dicts())
@settings(max_examples=100)
def test_null_for_any_absent_optional_field_reads_as_absent(trace: JsonObject) -> None:
    assert Trace.model_validate(_null_for_absent(trace)) == Trace.model_validate(trace)


@pytest.mark.xfail(strict=True, raises=ValidationError, reason=F2)
@given(
    trace=trace_dicts(presence=False),
    tool_calls=st.none(),
    redaction=st.fixed_dictionaries(
        {}, optional={"applied": st.none(), "paths": st.none(), "env_names": st.none()}
    ),
)
@EXPECTED_FAILURE
def test_explicit_null_for_a_nested_field_with_a_default_reads_as_absent(
    trace: JsonObject, tool_calls: None, redaction: JsonObject
) -> None:
    # xfail: finding F2 (see the story 2.6 plan; routed to story 2.7 in deferred-work.md).
    # The dump of an omitted ``capture`` is ``{"tool_calls": "unknown"}``, never null, so
    # this input is not something the serializer writes; AD-19 still says null reads as absent.
    with_nulls = {**trace, "capture": {"tool_calls": tool_calls}, "redaction": redaction}
    assert Trace.model_validate(with_nulls) == Trace.model_validate(trace)


# --- criterion 3: non-finite numbers ---------------------------------------------------------


@given(
    hole=json_values_with_a_hole(),
    number=NON_FINITE,
    field=st.sampled_from(["arguments", "result", "output"]),
)
@settings(max_examples=200)
def test_non_finite_in_a_tool_argument_result_or_final_output_is_rejected_naming_the_path(
    hole: Any, number: float, field: str
) -> None:
    build, path = hole
    event_type = {"arguments": "tool_call", "result": "tool_result", "output": "agent_finished"}
    trace = _min_trace()
    trace["events"] = [{"seq": 0, "type": event_type[field], field: build(number)}]

    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(trace)

    assert _locs_and_types(excinfo) == [(("events", 0, field), "finite_number")]
    assert _inner_path_text(path) in _errors(excinfo)[0]["msg"]


@given(hole=json_values_with_a_hole(), number=NON_FINITE, key=path_segments())
@settings(max_examples=100)
def test_non_finite_in_event_metadata_is_rejected_naming_the_path(
    hole: Any, number: float, key: str
) -> None:
    build, path = hole
    trace = _min_trace()
    trace["events"] = [{"seq": 0, "type": "custom", "metadata": {key: build(number)}}]

    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(trace)

    assert _locs_and_types(excinfo) == [(("events", 0, "metadata"), "finite_number")]
    assert _inner_path_text((key, *path)) in _errors(excinfo)[0]["msg"]


@given(hole=json_values_with_a_hole(), number=NON_FINITE, key=texts())
@settings(max_examples=200)
def test_non_finite_in_a_suite_input_is_rejected_naming_the_path(
    hole: Any, number: float, key: str
) -> None:
    build, path = hole
    suite = _min_suite()
    suite["scenarios"][0]["input"] = {key: build(number)}

    with pytest.raises(ValidationError) as excinfo:
        Suite.model_validate(suite)

    _assert_finite_number_error_at(excinfo, ("scenarios", 0, "input", key, *path))


@given(hole=json_values_with_a_hole(), number=NON_FINITE, argument=argument_paths())
@settings(max_examples=100)
def test_non_finite_in_a_tool_arguments_match_value_is_rejected_naming_the_path(
    hole: Any, number: float, argument: str
) -> None:
    build, path = hole
    suite = _min_suite()
    suite["scenarios"][0]["assertions"].append(
        {"type": "tool_arguments_match", "tool": "t", "arguments": {argument: build(number)}}
    )

    with pytest.raises(ValidationError) as excinfo:
        Suite.model_validate(suite)

    _assert_finite_number_error_at(
        excinfo, ("scenarios", 0, "assertions", 1, "arguments", argument, *path)
    )


@given(hole=json_values_with_a_hole(), number=NON_FINITE)
@settings(max_examples=200)
def test_non_finite_in_a_result_detail_is_rejected_naming_the_path(
    hole: Any, number: float
) -> None:
    build, path = hole
    report = _min_report()
    report["scenarios"][0]["assertions"][0]["detail"] = build(number)

    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(report)

    _assert_finite_number_error_at(excinfo, ("scenarios", 0, "assertions", 0, "detail", *path))


@given(number=NON_FINITE)
@settings(max_examples=20)
def test_non_finite_cost_is_rejected_at_the_cost(number: float) -> None:
    report = _min_report()
    report["scenarios"][0]["cost"] = number

    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(report)

    assert _locs_and_types(excinfo) == [(("scenarios", 0, "cost"), "finite_number")]


@given(hole=json_values_with_a_hole(), number=NON_FINITE)
@settings(max_examples=100)
def test_non_finite_final_output_inside_an_embedded_trace_is_rejected_naming_the_path(
    hole: Any, number: float
) -> None:
    build, path = hole
    trace = _min_trace()
    trace["events"] = [{"seq": 0, "type": "agent_finished", "output": build(number)}]
    report = _min_report()
    report["scenarios"][0]["trace"] = trace

    with pytest.raises(ValidationError) as excinfo:
        Report.model_validate(report)

    assert _locs_and_types(excinfo) == [
        (("scenarios", 0, "trace", "events", 0, "output"), "finite_number")
    ]
    assert _inner_path_text(path) in _errors(excinfo)[0]["msg"]


@given(
    hole=json_values_with_a_hole(), number=NON_FINITE, side=st.sampled_from(["baseline", "current"])
)
@settings(max_examples=100)
def test_non_finite_in_a_comparison_argument_change_is_rejected_naming_the_path(
    hole: Any, number: float, side: str
) -> None:
    build, path = hole
    change: JsonObject = {"scenario_id": "s", "path": "tool.amount", "baseline": 0, "current": 0}
    change[side] = build(number)

    with pytest.raises(ValidationError) as excinfo:
        Comparison.model_validate(
            {
                "baseline_suite_status": "passed",
                "current_suite_status": "passed",
                "regressed": False,
                "argument_changes": [change],
            }
        )

    _assert_finite_number_error_at(excinfo, ("argument_changes", 0, side, *path))


@given(hole=json_values_with_a_hole(), number=NON_FINITE)
@settings(max_examples=100)
def test_dumps_refuses_a_non_finite_number_anywhere(hole: Any, number: float) -> None:
    build, _ = hole
    with pytest.raises(ValueError, match="Out of range float values"):
        dumps(build(number))


# --- criterion 4: Unicode and byte identity --------------------------------------------------


@given(text=texts(), stamp=timestamps())
@settings(max_examples=200)
def test_generated_strings_survive_the_round_trip_exactly(text: str, stamp: str) -> None:
    trace: JsonObject = {
        "version": 1,
        "run_id": text,
        "scenario_id": text,
        "started_at": stamp,
        "ended_at": stamp,
        "agent": {"name": text, "version": text},
        "adapter": {"name": text, "version": text},
        "events": [
            {"seq": 0, "type": "tool_call", "tool": {"name": text}, "arguments": {text: text}},
            {"seq": 1, "type": "agent_finished", "output": text, "status": text},
        ],
    }
    original, _, again = _round_trip(Trace, trace)
    assert again == original
    assert again.run_id == text
    assert again.started_at == stamp
    assert again.events[0].arguments == {text: text}
    assert again.events[1].output == text
    assert [ord(ch) for ch in again.run_id] == [ord(ch) for ch in text]


@given(value=json_values())
@settings(max_examples=200)
def test_dumps_is_byte_identical_across_two_calls(value: JsonValue) -> None:
    first = dumps(value).encode("utf-8")
    second = dumps(copy.deepcopy(value)).encode("utf-8")
    assert first == second
    assert b"\r" not in first
    assert first.endswith(b"\n") and not first.endswith(b"\n\n")


@given(pair=shuffled_pairs())
@settings(max_examples=200)
def test_dumps_is_stable_under_key_insertion_order_shuffles(
    pair: tuple[JsonValue, JsonValue],
) -> None:
    value, shuffled = pair
    assert shuffled == value
    assert dumps(shuffled) == dumps(value)


@given(text=non_ascii_texts())
@settings(max_examples=200)
def test_dumps_preserves_non_ascii_literally(text: str) -> None:
    written = dumps({"text": text})
    for character in text:
        if ord(character) >= 0x80:
            assert character in written
    assert json.loads(written) == {"text": text}
