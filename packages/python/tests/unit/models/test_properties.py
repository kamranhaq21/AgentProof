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


def _assert_one_finite_error(
    excinfo: pytest.ExceptionInfo[ValidationError],
    loc: tuple[object, ...],
    number: float,
    inner: HolePath,
) -> None:
    """Exactly one error: ``finite_number`` at ``loc`` whose structured context is exact.

    ``ctx`` is what the error was built from (``PydanticCustomError``'s context), not text
    searched in the message: ``ctx["path"]`` must equal the hole's path and
    ``ctx["number"]`` the value, so a wrong path cannot pass by appearing in the prose.
    """
    errors = _errors(excinfo)
    assert [(tuple(e["loc"]), e["type"]) for e in errors] == [(loc, "finite_number")]
    assert errors[0]["ctx"] == {"number": str(number), "path": _inner_path_text(inner)}


def _assert_identical(left: object, right: object, where: str = "") -> None:
    """Equal value, same type at every node, same ``repr`` for floats (``-0.0`` is not ``0.0``).

    ``==`` alone cannot see ``1`` versus ``1.0`` versus ``True``; this can.
    """
    assert type(left) is type(right), f"{where or 'root'}: {left!r} vs {right!r}"
    if isinstance(left, dict):
        assert isinstance(right, dict) and set(left) == set(right), where
        for key in left:
            _assert_identical(left[key], right[key], f"{where}.{key}")
    elif isinstance(left, list | tuple):
        assert isinstance(right, list | tuple) and len(left) == len(right), where
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            _assert_identical(a, b, f"{where}[{index}]")
    elif isinstance(left, float):
        assert repr(left) == repr(right), where
    else:
        assert left == right, where


def _assert_models_identical(left: BaseModel, right: BaseModel) -> None:
    """Models equal, and their Python and JSON dumps identical down to scalar types."""
    assert left == right
    _assert_identical(left.model_dump(), right.model_dump())
    _assert_identical(left.model_dump(mode="json"), right.model_dump(mode="json"))


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
    _assert_identical(value, again)
    assert dumps(again) == text


@given(trace=trace_dicts())
@settings(max_examples=200)
def test_trace_round_trips_through_canonical_dumps(trace: JsonObject) -> None:
    original, text, again = _round_trip(Trace, trace)
    _assert_models_identical(original, again)
    assert dumps(again.model_dump(mode="json")) == text


@given(report=report_dicts())
@settings(max_examples=200)
def test_report_round_trips_through_canonical_dumps(report: JsonObject) -> None:
    original, text, again = _round_trip(Report, report)
    _assert_models_identical(original, again)
    assert dumps(again.model_dump(mode="json")) == text


@given(suite=suite_dicts(skipped=True))
@settings(max_examples=200)
def test_suite_with_every_scenario_skipped_round_trips_through_canonical_dumps(
    suite: JsonObject,
) -> None:
    original, text, again = _round_trip(Suite, suite)
    _assert_models_identical(original, again)
    assert dumps(again.model_dump(mode="json")) == text


@pytest.mark.xfail(strict=True, raises=ValidationError, reason=F1)
@given(suite=suite_dicts(skipped=False))
@EXPECTED_FAILURE
def test_suite_with_an_unskipped_scenario_round_trips_through_canonical_dumps(
    suite: JsonObject,
) -> None:
    # xfail: finding F1 (see the story 2.6 plan; routed to stories 2.7/3.3 in deferred-work.md).
    # The expected failure is exactly "skip: null" at each unskipped Scenario; any other error
    # (or a missing one) is a different outcome and must not hide behind the xfail.
    original = Suite.model_validate(suite)
    dumped = json.loads(dumps(original.model_dump(mode="json")))
    try:
        again = Suite.model_validate(dumped)
    except ValidationError as error:
        found = [(tuple(e["loc"]), e["type"]) for e in error.errors(include_url=False)]
        expected = [
            (("scenarios", index, "skip"), "value_error")
            for index, scenario in enumerate(suite["scenarios"])
            if "skip" not in scenario
        ]
        assert found == expected
        raise
    _assert_models_identical(original, again)


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


NESTED_NULLS: dict[str, tuple[JsonObject, tuple[str, ...], str]] = {
    "capture.tool_calls": (
        {"capture": {"tool_calls": None}},
        ("capture", "tool_calls"),
        "literal_error",
    ),
    "redaction.applied": ({"redaction": {"applied": None}}, ("redaction", "applied"), "bool_type"),
    "redaction.paths": ({"redaction": {"paths": None}}, ("redaction", "paths"), "tuple_type"),
    "redaction.env_names": (
        {"redaction": {"env_names": None}},
        ("redaction", "env_names"),
        "tuple_type",
    ),
}
"""Per field: the nested object holding one explicit null, the expected error location, type."""


@pytest.mark.xfail(strict=True, raises=ValidationError, reason=F2)
@pytest.mark.parametrize("field", list(NESTED_NULLS))
@given(trace=trace_dicts(presence=False))
@EXPECTED_FAILURE
def test_explicit_null_for_a_nested_field_with_a_default_reads_as_absent(
    field: str, trace: JsonObject
) -> None:
    # xfail: finding F2 (see the story 2.6 plan; routed to story 2.7 in deferred-work.md).
    # One case per field, so fixing some fields turns exactly those cases into strict XPASS
    # failures. The dump of an omitted ``capture`` is ``{"tool_calls": "unknown"}``, never
    # null, so this input is not something the serializer writes; AD-19 says null reads as
    # absent. The expected failure is exactly this field's error and nothing else.
    nulls, loc, error_type = NESTED_NULLS[field]
    with_null = {**trace, **nulls}
    try:
        validated = Trace.model_validate(with_null)
    except ValidationError as error:
        found = [(tuple(e["loc"]), e["type"]) for e in error.errors(include_url=False)]
        assert found == [(loc, error_type)]
        raise
    assert validated == Trace.model_validate(trace)


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

    _assert_one_finite_error(excinfo, ("events", 0, field), number, path)


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

    _assert_one_finite_error(excinfo, ("events", 0, "metadata"), number, (key, *path))


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

    _assert_one_finite_error(
        excinfo, ("scenarios", 0, "trace", "events", 0, "output"), number, path
    )


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


def _nested(depth: int, leaf: JsonValue, key: str = "k") -> JsonValue:
    """``{key: {key: ... leaf}}`` with ``depth`` objects, built iteratively."""
    value = leaf
    for _ in range(depth):
        value = {key: value}
    return value


F3 = (
    "F3: JsonValue nesting beyond about 90 levels fails validation with recursion_loop and one "
    "error per union branch (hundreds of lines), even for finite valid JSON"
)


@pytest.mark.xfail(strict=False, raises=ValidationError, reason=F3)
def test_finite_json_one_hundred_and_fifty_levels_deep_is_accepted() -> None:
    # xfail (non-strict): finding F3 (see the story 2.6 plan; deferred-work.md).
    # ``json.loads`` and ``dumps`` handle this depth; on the implementer's machine
    # (Windows, CPython 3.13) the model did not, failing around depth 100. CI then
    # showed this threshold is itself platform-dependent: on Linux/CPython 3.12.3 this
    # exact 150-level payload validates fine (XPASS), almost certainly because
    # pydantic-core's recursive-validation depth limit rides on the native C stack,
    # and POSIX threads default to a larger stack than Windows threads. ``strict`` is
    # therefore off: an XPASS here is not itself a regression to fail the build over,
    # only the threshold moving, which is exactly the kind of platform noise F3's
    # eventual fix (a documented, enforced depth limit, story 3.3 + architect) should
    # replace with a limit that behaves the same everywhere. When fixed, this test can
    # go back to asserting the real validation outcome directly.
    value: JsonValue = 1
    for level in range(150):
        value = [0, value] if level % 10 == 9 else {"k": value}
    assert json.loads(dumps(value)) == value
    trace = _min_trace()
    trace["events"] = [{"seq": 0, "type": "tool_call", "arguments": value}]
    try:
        Trace.model_validate(trace)
    except ValidationError as error:
        errors = error.errors(include_url=False)
        assert {tuple(e["loc"][:3]) for e in errors} == {("events", 0, "arguments")}
        assert "recursion_loop" in {e["type"] for e in errors}
        raise


@pytest.mark.parametrize("depth", [50, 80])
def test_non_finite_deep_in_a_trace_payload_names_the_exact_path(depth: int) -> None:
    # Fixed, not generated: real depth, with a list index mixed in every tenth level.
    value: JsonValue = math.nan
    path: list[int | str] = []
    for level in range(depth):
        if level % 10 == 9:
            value, path = [0, value], [1, *path]
        else:
            value, path = {"k": value}, ["k", *path]
    assert len(path) == depth
    trace = _min_trace()
    trace["events"] = [{"seq": 0, "type": "tool_call", "arguments": value}]

    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(trace)

    _assert_one_finite_error(excinfo, ("events", 0, "arguments"), math.nan, tuple(path))


def test_non_finite_fifty_levels_deep_in_a_suite_input_is_located_by_the_path() -> None:
    suite = _min_suite()
    suite["scenarios"][0]["input"] = {"k": _nested(49, math.inf)}

    with pytest.raises(ValidationError) as excinfo:
        Suite.model_validate(suite)

    _assert_finite_number_error_at(excinfo, ("scenarios", 0, "input", *["k"] * 50))


def test_two_holes_in_one_trace_payload_report_the_first_in_document_order() -> None:
    trace = _min_trace()
    trace["events"] = [
        {"seq": 0, "type": "tool_call", "arguments": {"a": [1, {"b": math.nan}], "c": math.inf}}
    ]

    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(trace)

    _assert_one_finite_error(excinfo, ("events", 0, "arguments"), math.nan, ("a", 1, "b"))


def test_two_holes_in_different_trace_events_each_get_their_own_error() -> None:
    trace = _min_trace()
    trace["events"] = [
        {"seq": 0, "type": "tool_call", "arguments": {"x": [math.inf]}},
        {"seq": 1, "type": "custom", "metadata": {"fine": 1}},
        {"seq": 2, "type": "agent_finished", "output": {"y": {"z": -math.inf}}},
    ]

    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(trace)

    assert [(tuple(e["loc"]), e["type"], e["ctx"]) for e in _errors(excinfo)] == [
        (("events", 0, "arguments"), "finite_number", {"number": "inf", "path": "x.0"}),
        (("events", 2, "output"), "finite_number", {"number": "-inf", "path": "y.z"}),
    ]


def test_two_holes_in_a_suite_input_are_both_located_and_the_clean_key_is_not() -> None:
    suite = _min_suite()
    suite["scenarios"][0]["input"] = {
        "first": [1, math.nan],
        "clean": {"n": 1.5},
        "second": {"deep": math.inf},
    }

    with pytest.raises(ValidationError) as excinfo:
        Suite.model_validate(suite)

    locs = [tuple(error["loc"]) for error in _errors(excinfo)]
    finite = [tuple(e["loc"]) for e in _errors(excinfo) if e["type"] == "finite_number"]
    base = ("scenarios", 0, "input")
    assert any(_is_subsequence((*base, "first", 1), loc) for loc in finite)
    assert any(_is_subsequence((*base, "second", "deep"), loc) for loc in finite)
    assert not any("clean" in loc for loc in locs)


@given(hole=json_values_with_a_hole(), number=NON_FINITE)
@settings(max_examples=100)
def test_dumps_refuses_a_non_finite_number_anywhere(hole: Any, number: float) -> None:
    build, _ = hole
    with pytest.raises(ValueError, match="Out of range float values"):
        dumps(build(number))


# --- criterion 4: Unicode and byte identity --------------------------------------------------


@given(
    values=st.lists(texts(), min_size=11, max_size=11, unique=True),
    started=timestamps(),
    ended=timestamps(),
)
@settings(max_examples=200)
def test_generated_strings_survive_the_round_trip_exactly(
    values: list[str], started: str, ended: str
) -> None:
    # Eleven pairwise-distinct strings, one per field, so a swap between fields fails.
    (run_id, scenario_id, agent, agent_version, adapter, adapter_version) = values[:6]
    (tool, argument_key, argument_value, output, status) = values[6:]
    trace: JsonObject = {
        "version": 1,
        "run_id": run_id,
        "scenario_id": scenario_id,
        "started_at": started,
        "ended_at": ended,
        "agent": {"name": agent, "version": agent_version},
        "adapter": {"name": adapter, "version": adapter_version},
        "events": [
            {
                "seq": 0,
                "type": "tool_call",
                "tool": {"name": tool},
                "arguments": {argument_key: argument_value},
            },
            {"seq": 1, "type": "agent_finished", "output": output, "status": status},
        ],
    }
    original, _, again = _round_trip(Trace, trace)
    _assert_models_identical(original, again)
    assert (again.run_id, again.scenario_id) == (run_id, scenario_id)
    assert (again.started_at, again.ended_at) == (started, ended)
    assert (again.agent.name, again.agent.version) == (agent, agent_version)
    assert (again.adapter.name, again.adapter.version) == (adapter, adapter_version)
    first, second = again.events
    assert first.tool is not None and first.tool.name == tool
    assert first.arguments == {argument_key: argument_value}
    assert (second.output, second.status) == (output, status)
    assert [ord(ch) for ch in again.run_id] == [ord(ch) for ch in run_id]


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
