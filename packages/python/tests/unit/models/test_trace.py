"""``agentproof.models.trace``: the spine's Trace seed, the event rules, timestamps, defaults.

``SEED`` is the Trace JSON seed from the architecture spine ("Schemas (seed)") with the
abbreviated events completed to the full key set and the ``"..."`` timestamp placeholders
filled with real RFC 3339 values. Every test validates through ``model_validate(dict)``,
the only path ``loading.parse_trace`` will use (AD-3).
"""

import copy
import datetime
import math
from typing import Any, get_args

import pytest
from pydantic import BaseModel, ValidationError

import agentproof.models.trace as trace_module
from agentproof.constants import SUPPORTED_VERSIONS
from agentproof.models.canonical import VOLATILE_PATHS
from agentproof.models.trace import (
    EVENT_TYPES,
    AdapterInfo,
    AgentInfo,
    Capture,
    CaptureLevel,
    Environment,
    EventError,
    EventType,
    ModelInfo,
    RedactionState,
    ToolRef,
    Trace,
    TraceEvent,
)

T0 = "2026-10-22T13:05:00+00:00"
T1 = "2026-10-22T13:05:00.250+00:00"
T2 = "2026-10-22T13:05:01Z"
T3 = "2026-10-22T13:05:02+00:00"

EMPTY_EVENT_FIELDS: dict[str, Any] = {
    "timestamp": None,
    "duration_ms": None,
    "tool": None,
    "arguments": None,
    "result": None,
    "status": None,
    "error": None,
    "output": None,
    "redacted": False,
    "metadata": {},
}

SEED: dict[str, Any] = {
    "version": 1,
    "run_id": "fixture-reject-over-limit",
    "scenario_id": "reject-over-limit",
    "started_at": T0,
    "ended_at": T3,
    "agent": {"name": "expense-agent", "version": "1.2.0"},
    "adapter": {"name": "fixture", "version": "0.1.0"},
    "model": {"provider": None, "name": None},
    "capture": {"tool_calls": "complete"},
    "environment": {
        "package_version": "0.1.0",
        "python_version": "3.12.15",
        "os": "Linux",
        "source_revision": None,
    },
    "redaction": {"applied": True, "paths": ["arguments.api_key"], "env_names": ["OPENAI_API_KEY"]},
    "events": [
        {**EMPTY_EVENT_FIELDS, "seq": 0, "type": "agent_started", "timestamp": T0},
        {
            **EMPTY_EVENT_FIELDS,
            "seq": 1,
            "type": "tool_call",
            "timestamp": T1,
            "tool": {"name": "reject_expense", "call_id": "c1"},
            "arguments": {"amount": 5000},
        },
        {
            **EMPTY_EVENT_FIELDS,
            "seq": 2,
            "type": "tool_result",
            "timestamp": T2,
            "duration_ms": 750,
            "tool": {"name": "reject_expense", "call_id": "c1"},
            "result": {"ok": True},
            "status": "ok",
        },
        {
            **EMPTY_EVENT_FIELDS,
            "seq": 3,
            "type": "agent_finished",
            "timestamp": T3,
            "output": "Expense rejected: over limit",
        },
    ],
}

ELEVEN_TYPES = (
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


def _trace(**overrides: Any) -> dict[str, Any]:
    """A deep copy of ``SEED`` with top-level keys replaced; a ``...`` value removes the key."""
    data = copy.deepcopy(SEED)
    for key, value in overrides.items():
        if value is ...:
            data.pop(key, None)
        else:
            data[key] = value
    return data


def _events(*seqs: int, **fields: Any) -> list[dict[str, Any]]:
    return [{"seq": seq, "type": "custom", **fields} for seq in seqs]


def _errors(
    excinfo: pytest.ExceptionInfo[ValidationError],
) -> list[tuple[tuple[int | str, ...], str]]:
    return [(error["loc"], error["msg"]) for error in excinfo.value.errors()]


def _locs(excinfo: pytest.ExceptionInfo[ValidationError]) -> list[tuple[int | str, ...]]:
    return [loc for loc, _ in _errors(excinfo)]


def _types(excinfo: pytest.ExceptionInfo[ValidationError]) -> list[str]:
    """The stable error type codes ``loading.parse_trace`` keys on."""
    return [error["type"] for error in excinfo.value.errors()]


# --- criterion 1: Trace shape -----------------------------------------------------------


def test_spine_seed_validates_with_every_field_of_criterion_1() -> None:
    trace = Trace.model_validate(SEED)
    assert trace.version == 1
    assert trace.run_id == "fixture-reject-over-limit"
    assert trace.scenario_id == "reject-over-limit"
    assert trace.started_at == T0
    assert trace.ended_at == T3
    assert trace.agent == AgentInfo(name="expense-agent", version="1.2.0")
    assert trace.adapter == AdapterInfo(name="fixture", version="0.1.0")
    assert trace.model == ModelInfo(provider=None, name=None)
    assert trace.capture == Capture(tool_calls="complete")
    assert trace.environment == Environment(
        package_version="0.1.0", python_version="3.12.15", os="Linux", source_revision=None
    )
    assert trace.redaction == RedactionState(
        applied=True, paths=["arguments.api_key"], env_names=["OPENAI_API_KEY"]
    )
    assert [event.seq for event in trace.events] == [0, 1, 2, 3]
    assert trace.events[1].tool == ToolRef(name="reject_expense", call_id="c1")
    assert trace.events[1].arguments == {"amount": 5000}
    assert trace.events[2].result == {"ok": True}
    assert trace.events[2].status == "ok"
    assert trace.events[2].duration_ms == 750
    assert trace.events[3].output == "Expense rejected: over limit"


def test_trace_field_set_is_exactly_criterion_1() -> None:
    assert set(Trace.model_fields) == {
        "version",
        "run_id",
        "scenario_id",
        "started_at",
        "ended_at",
        "agent",
        "adapter",
        "model",
        "capture",
        "environment",
        "redaction",
        "events",
    }


def test_seed_round_trips_through_model_dump_in_json_mode() -> None:
    dumped = Trace.model_validate(SEED).model_dump(mode="json")
    assert dumped == SEED
    assert isinstance(dumped["events"], list)
    assert isinstance(dumped["redaction"]["paths"], list)
    assert isinstance(dumped["redaction"]["env_names"], list)


def test_trace_without_model_key_validates_with_model_none() -> None:
    assert Trace.model_validate(_trace(model=...)).model is None


@pytest.mark.parametrize("model", [{}, {"provider": None, "name": None}, {"provider": "openai"}])
def test_trace_without_model_values_validates(model: dict[str, Any]) -> None:
    trace = Trace.model_validate(_trace(model=model))
    assert trace.model == ModelInfo(provider=model.get("provider"), name=None)


def test_agent_version_is_optional_and_adapter_version_is_required() -> None:
    assert Trace.model_validate(_trace(agent={"name": "a"})).agent.version is None
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(adapter={"name": "fixture"}))
    assert _locs(excinfo) == [("adapter", "version")]


@pytest.mark.parametrize(
    "missing",
    ["version", "run_id", "scenario_id", "started_at", "ended_at", "agent", "adapter", "events"],
)
def test_required_trace_fields_are_reported_by_name_when_missing(missing: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(**{missing: ...}))
    assert _locs(excinfo) == [(missing,)]


def test_version_1_is_the_supported_trace_version() -> None:
    assert SUPPORTED_VERSIONS["trace"] == (1,)
    assert Trace.model_validate(_trace(version=1)).version == 1


def test_unsupported_version_is_rejected_naming_both_versions() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(version=2))
    [(loc, message)] = _errors(excinfo)
    assert loc == ("version",)
    assert "version 2" in message
    assert "supported versions: 1" in message
    assert _types(excinfo) == ["unsupported_version"]


@pytest.mark.parametrize("version", ["1", 1.0, True, None], ids=["str", "float", "bool", "null"])
def test_non_integer_version_is_rejected(version: object) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(version=version))
    assert _locs(excinfo) == [("version",)]
    assert _types(excinfo) == ["integer_required"]


def test_unsupported_version_with_an_unknown_field_reports_both_codes() -> None:
    """The loader must prefer ``unsupported_version`` (UnsupportedVersionError) over the rest."""
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(version=2, result_summary={}))
    assert sorted(_types(excinfo)) == ["extra_forbidden", "unsupported_version"]
    assert sorted(_locs(excinfo)) == [("result_summary",), ("version",)]


# --- criterion 2: events ----------------------------------------------------------------


def test_event_type_literal_lists_the_eleven_types_in_order() -> None:
    assert get_args(EventType) == ELEVEN_TYPES
    assert EVENT_TYPES == ELEVEN_TYPES
    assert len(set(EVENT_TYPES)) == 11


@pytest.mark.parametrize("event_type", ELEVEN_TYPES)
def test_each_of_the_eleven_event_types_is_accepted(event_type: str) -> None:
    trace = Trace.model_validate(_trace(events=[{"seq": 0, "type": event_type}]))
    assert trace.events[0].type == event_type


def test_all_eleven_event_types_validate_together_in_one_trace() -> None:
    events = [{"seq": index, "type": name} for index, name in enumerate(ELEVEN_TYPES)]
    trace = Trace.model_validate(_trace(events=events))
    assert tuple(event.type for event in trace.events) == ELEVEN_TYPES


def test_unknown_event_type_is_rejected_naming_the_type_and_the_index() -> None:
    events = _events(0) + [{"seq": 1, "type": "bogus"}]
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(events=events))
    [(loc, _)] = _errors(excinfo)
    assert loc == ("events", 1, "type")
    text = str(excinfo.value)
    assert "events.1.type" in text
    assert "bogus" in text


def test_event_type_is_required() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(events=[{"seq": 0}]))
    assert _locs(excinfo) == [("events", 0, "type")]


def test_event_optional_fields_default_to_none_false_and_empty_metadata() -> None:
    event = Trace.model_validate(_trace(events=[{"seq": 0, "type": "custom"}])).events[0]
    assert event.seq == 0
    assert event.timestamp is None
    assert event.duration_ms is None
    assert event.tool is None
    assert event.arguments is None
    assert event.result is None
    assert event.status is None
    assert event.error is None
    assert event.output is None
    assert event.redacted is False
    assert event.metadata == {}


def test_event_field_set_is_exactly_the_seeds_key_set() -> None:
    assert set(TraceEvent.model_fields) == {
        "seq",
        "type",
        "timestamp",
        "duration_ms",
        "tool",
        "arguments",
        "result",
        "status",
        "error",
        "output",
        "redacted",
        "metadata",
    }


def test_event_carries_tool_error_output_redacted_and_metadata() -> None:
    event = Trace.model_validate(
        _trace(
            events=[
                {
                    "seq": 0,
                    "type": "exception",
                    "tool": {"name": "fetch"},
                    "error": {"type": "TimeoutError", "message": "timed out", "unhandled": True},
                    "output": {"items": [1, 2.5, "x", None, {"k": False}]},
                    "redacted": True,
                    "metadata": {"model": "gpt", "tokens": 12},
                }
            ]
        )
    ).events[0]
    assert event.tool == ToolRef(name="fetch", call_id=None)
    assert event.error == EventError(type="TimeoutError", message="timed out", unhandled=True)
    assert event.output == {"items": [1, 2.5, "x", None, {"k": False}]}
    assert event.redacted is True
    assert event.metadata == {"model": "gpt", "tokens": 12}


def test_tool_requires_a_name_and_error_requires_all_three_fields() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(events=[{"seq": 0, "type": "tool_call", "tool": {}}]))
    assert _locs(excinfo) == [("events", 0, "tool", "name")]
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(
            _trace(events=[{"seq": 0, "type": "exception", "error": {"type": "E", "message": "m"}}])
        )
    assert _locs(excinfo) == [("events", 0, "error", "unhandled")]


def test_contiguous_seq_is_accepted_and_an_empty_events_list_is_valid() -> None:
    assert [e.seq for e in Trace.model_validate(_trace(events=_events(0, 1, 2, 3))).events] == [
        0,
        1,
        2,
        3,
    ]
    assert Trace.model_validate(_trace(events=[])).events == ()


@pytest.mark.parametrize(
    ("seqs", "index", "found"),
    [
        ((0, 2), 1, 2),
        ((0, 1, 3, 4), 2, 3),
        ((0, 0), 1, 0),
        ((0, 1, 1), 2, 1),
        ((1, 0), 0, 1),
        ((0, 2, 1), 1, 2),
        ((1,), 0, 1),
        ((5, 6, 7), 0, 5),
    ],
    ids=[
        "gap",
        "gap-later",
        "duplicate",
        "duplicate-later",
        "disorder",
        "swap",
        "starts-at-1",
        "offset",
    ],
)
def test_seq_gap_duplicate_and_disorder_name_the_first_offending_index(
    seqs: tuple[int, ...], index: int, found: int
) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(events=_events(*seqs)))
    [(loc, message)] = _errors(excinfo)
    assert loc == ("events", index, "seq")
    assert f"events[{index}].seq is {found}; expected {index}" in message
    assert f"events.{index}.seq" in str(excinfo.value)
    assert _types(excinfo) == ["seq_not_contiguous"]


def test_negative_seq_is_rejected_at_its_index() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(events=_events(-1)))
    assert _locs(excinfo) == [("events", 0, "seq")]
    assert _types(excinfo) == ["greater_than_equal"]


@pytest.mark.parametrize("seq", ["0", 0.0, False], ids=["str", "float", "bool"])
def test_non_integer_seq_is_rejected_at_its_index(seq: object) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(events=[{"seq": seq, "type": "custom"}]))
    assert _locs(excinfo) == [("events", 0, "seq")]
    assert _types(excinfo) == ["integer_required"]


@pytest.mark.parametrize(
    ("duration", "code"),
    [
        ("750", "integer_required"),
        (1.5, "integer_required"),
        (True, "integer_required"),
        (-1, "greater_than_equal"),
    ],
    ids=["str", "float", "bool", "negative"],
)
def test_duration_ms_must_be_a_non_negative_integer(duration: object, code: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(events=_events(0, duration_ms=duration)))
    assert _locs(excinfo) == [("events", 0, "duration_ms")]
    assert _types(excinfo) == [code]


def test_duration_ms_zero_is_accepted() -> None:
    assert Trace.model_validate(_trace(events=_events(0, duration_ms=0))).events[0].duration_ms == 0


# --- criterion 3: timestamps ------------------------------------------------------------

VALID_TIMESTAMPS = [
    "2026-10-22T13:05:00+00:00",
    "2026-10-22T13:05:00Z",
    "2026-10-22T13:05:00.123456-05:00",
    "2026-10-22T13:05:00.1Z",
    "2026-10-22T13:05:00.123456789+05:30",
]

INVALID_TIMESTAMPS = [
    pytest.param("2026-10-22T13:05:00", id="naive"),
    pytest.param("2026-10-22 13:05:00Z", id="space-separator"),
    pytest.param("2026-10-22T13:05Z", id="no-seconds"),
    pytest.param("x2026-10-22T13:05:00Zy", id="embedded"),
    pytest.param("2026-10-22T13:05:00Z\n", id="trailing-newline"),
    pytest.param("", id="empty"),
]

NON_STRING_TIMESTAMPS = [
    pytest.param(1761138300, id="int"),
    pytest.param(1761138300.0, id="float"),
    pytest.param(datetime.datetime(2026, 10, 22, 13, 5, tzinfo=datetime.UTC), id="datetime"),
    pytest.param(["2026-10-22T13:05:00Z"], id="list"),
]


@pytest.mark.parametrize("timestamp", VALID_TIMESTAMPS)
def test_rfc3339_timestamps_with_offset_or_z_are_stored_unchanged(timestamp: str) -> None:
    events = _events(0, timestamp=timestamp)
    trace = Trace.model_validate(_trace(started_at=timestamp, ended_at=timestamp, events=events))
    assert trace.started_at == timestamp
    assert trace.ended_at == timestamp
    assert trace.events[0].timestamp == timestamp
    assert trace.model_dump()["started_at"] == timestamp


def test_z_timestamp_is_not_rewritten_to_plus_zero_offset() -> None:
    trace = Trace.model_validate(_trace(started_at="2026-10-22T13:05:00Z"))
    assert trace.started_at == "2026-10-22T13:05:00Z"
    assert trace.started_at != "2026-10-22T13:05:00+00:00"


@pytest.mark.parametrize("field", ["started_at", "ended_at"])
@pytest.mark.parametrize("timestamp", INVALID_TIMESTAMPS + NON_STRING_TIMESTAMPS)
def test_naive_or_non_string_trace_timestamps_are_rejected_naming_the_field(
    field: str, timestamp: object
) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(**{field: timestamp}))
    [(loc, message)] = _errors(excinfo)
    assert loc == (field,)
    assert "RFC 3339" in message
    expected = "timestamp_format" if isinstance(timestamp, str) else "timestamp_type"
    assert _types(excinfo) == [expected]


@pytest.mark.parametrize("timestamp", INVALID_TIMESTAMPS + NON_STRING_TIMESTAMPS)
def test_naive_or_non_string_event_timestamp_is_rejected_at_its_index(timestamp: object) -> None:
    events = _events(0) + _events(1, timestamp=timestamp)
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(events=events))
    assert _locs(excinfo) == [("events", 1, "timestamp")]
    expected = "timestamp_format" if isinstance(timestamp, str) else "timestamp_type"
    assert _types(excinfo) == [expected]


def test_null_started_at_is_rejected_because_the_field_is_required() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(started_at=None))
    assert _locs(excinfo) == [("started_at",)]
    assert _types(excinfo) == ["timestamp_type"]


def test_event_timestamp_may_be_null() -> None:
    assert (
        Trace.model_validate(_trace(events=_events(0, timestamp=None))).events[0].timestamp is None
    )


# --- criterion 4: capture, redaction state, environment ---------------------------------


def test_capture_defaults_to_unknown_when_absent() -> None:
    trace = Trace.model_validate(_trace(capture=...))
    assert trace.capture == Capture(tool_calls="unknown")
    assert Capture() == Capture(tool_calls="unknown")


@pytest.mark.parametrize("level", get_args(CaptureLevel))
def test_capture_accepts_complete_partial_and_unknown(level: str) -> None:
    assert Trace.model_validate(_trace(capture={"tool_calls": level})).capture.tool_calls == level


def test_capture_rejects_other_levels_and_unknown_keys() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(capture={"tool_calls": "all"}))
    assert _locs(excinfo) == [("capture", "tool_calls")]
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(capture={"llm_calls": "complete"}))
    assert _locs(excinfo) == [("capture", "llm_calls")]


def test_redaction_defaults_to_not_applied_with_empty_lists() -> None:
    trace = Trace.model_validate(_trace(redaction=...))
    assert trace.redaction == RedactionState(applied=False, paths=(), env_names=())
    assert trace.redaction.applied is False
    assert trace.redaction.paths == ()
    assert trace.redaction.env_names == ()


def test_redaction_state_carries_paths_and_env_names_never_values() -> None:
    state = Trace.model_validate(SEED).redaction
    assert state.applied is True
    assert state.paths == ("arguments.api_key",)
    assert state.env_names == ("OPENAI_API_KEY",)
    assert set(RedactionState.model_fields) == {"applied", "paths", "env_names"}
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(redaction={"applied": True, "values": ["sk-secret"]}))
    assert _locs(excinfo) == [("redaction", "values")]


# --- shallow frozen: sequence fields are tuples, payloads are not deep-frozen ------------


def test_sequence_fields_validate_from_json_lists_into_tuples() -> None:
    trace = Trace.model_validate(SEED)
    assert isinstance(trace.events, tuple)
    assert isinstance(trace.redaction.paths, tuple)
    assert isinstance(trace.redaction.env_names, tuple)
    assert [event.seq for event in trace.events] == [0, 1, 2, 3]


def test_sequence_fields_export_as_json_schema_arrays() -> None:
    props = _schema_properties(Trace.model_json_schema())
    assert props["Trace.events"]["type"] == "array"
    assert props["RedactionState.paths"]["type"] == "array"
    assert props["RedactionState.env_names"]["type"] == "array"


def test_trace_without_events_is_hashable_and_tuples_block_mutation() -> None:
    trace = Trace.model_validate(_trace(events=[]))
    assert hash(trace) == hash(Trace.model_validate(_trace(events=[])))
    assert hash(trace.redaction) == hash(
        RedactionState(applied=True, paths=("arguments.api_key",), env_names=("OPENAI_API_KEY",))
    )
    assert not hasattr(trace.events, "append")
    assert not hasattr(trace.redaction.paths, "append")


def test_payload_fields_are_not_deep_frozen() -> None:
    """``metadata``, ``arguments``, ``result`` and ``output`` keep the input's dicts and lists.

    Every event's ``metadata`` is a dict, so a Trace with at least one event is unhashable.
    """
    trace = Trace.model_validate(SEED)
    assert isinstance(trace.events[1].arguments, dict)
    assert isinstance(trace.events[0].metadata, dict)
    with pytest.raises(TypeError):
        hash(trace)
    with pytest.raises(TypeError):
        hash(Trace.model_validate(_trace(events=_events(0))))


def test_environment_accepts_exactly_the_four_allowlisted_keys() -> None:
    assert set(Environment.model_fields) == {
        "package_version",
        "python_version",
        "os",
        "source_revision",
    }
    env = Trace.model_validate(SEED).environment
    assert (env.package_version, env.python_version, env.os, env.source_revision) == (
        "0.1.0",
        "3.12.15",
        "Linux",
        None,
    )


def test_environment_defaults_to_all_none_when_absent() -> None:
    assert Trace.model_validate(_trace(environment=...)).environment == Environment()
    assert Trace.model_validate(_trace(environment={})).environment == Environment()


@pytest.mark.parametrize("key", ["hostname", "HOME", "user", "OPENAI_API_KEY"])
def test_environment_rejects_any_other_key_naming_it(key: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(environment={"os": "Linux", key: "value"}))
    [(loc, message)] = _errors(excinfo)
    assert loc == ("environment", key)
    assert "Extra inputs are not permitted" in message
    assert f"environment.{key}" in str(excinfo.value)


# --- AD-19: null equals absent for fields with a default ---------------------------------


def test_null_capture_environment_and_redaction_read_as_their_defaults() -> None:
    trace = Trace.model_validate(_trace(capture=None, environment=None, redaction=None))
    assert trace.capture == Capture(tool_calls="unknown")
    assert trace.environment == Environment()
    assert trace.redaction == RedactionState(applied=False, paths=[], env_names=[])


def test_null_event_metadata_and_redacted_read_as_their_defaults() -> None:
    event = Trace.model_validate(_trace(events=_events(0, metadata=None, redacted=None))).events[0]
    assert event.metadata == {}
    assert event.redacted is False


def test_null_model_reads_as_none_like_an_absent_key() -> None:
    assert Trace.model_validate(_trace(model=None)).model is None


@pytest.mark.parametrize(
    ("field", "code"),
    [("run_id", "string_type"), ("scenario_id", "string_type"), ("events", "tuple_type")],
)
def test_null_for_a_required_trace_field_keeps_its_normal_error(field: str, code: str) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(**{field: None}))
    assert _locs(excinfo) == [(field,)]
    assert _types(excinfo) == [code]


def test_null_for_a_required_event_field_keeps_its_normal_error() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(events=[{"seq": 0, "type": None}]))
    assert _locs(excinfo) == [("events", 0, "type")]
    assert _types(excinfo) == ["literal_error"]


def test_null_for_an_unknown_key_is_still_an_unknown_key() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(result_summary=None))
    assert _locs(excinfo) == [("result_summary",)]
    assert _types(excinfo) == ["extra_forbidden"]


# --- AD-3: frozen, forbid-unknown, version-independent of the package -------------------


@pytest.mark.parametrize(
    ("overrides", "loc"),
    [
        ({"result_summary": {}}, ("result_summary",)),
        ({"agent": {"name": "a", "version": "1", "vendor": "x"}}, ("agent", "vendor")),
        ({"adapter": {"name": "a", "version": "1", "extra": 1}}, ("adapter", "extra")),
        ({"model": {"provider": "p", "name": "n", "temperature": 0.1}}, ("model", "temperature")),
        ({"events": [{"seq": 0, "type": "custom", "payload": 1}]}, ("events", 0, "payload")),
        (
            {"events": [{"seq": 0, "type": "tool_call", "tool": {"name": "t", "args": {}}}]},
            ("events", 0, "tool", "args"),
        ),
        (
            {
                "events": [
                    {
                        "seq": 0,
                        "type": "exception",
                        "error": {"type": "E", "message": "m", "unhandled": True, "stack": "..."},
                    }
                ]
            },
            ("events", 0, "error", "stack"),
        ),
    ],
    ids=["trace", "agent", "adapter", "model", "event", "tool", "error"],
)
def test_unknown_fields_are_rejected_at_their_path(
    overrides: dict[str, Any], loc: tuple[Any, ...]
) -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(**overrides))
    assert _errors(excinfo) == [(loc, "Extra inputs are not permitted")]


def test_models_are_frozen() -> None:
    trace = Trace.model_validate(SEED)
    with pytest.raises(ValidationError) as excinfo:
        trace.run_id = "other"
    assert excinfo.value.errors()[0]["type"] == "frozen_instance"
    assert trace.run_id == "fixture-reject-over-limit"
    with pytest.raises(ValidationError):
        trace.events[0].seq = 7
    assert trace.events[0].seq == 0
    with pytest.raises(ValidationError):
        trace.capture.tool_calls = "partial"


@pytest.mark.parametrize(
    "model",
    [
        Trace,
        TraceEvent,
        ToolRef,
        EventError,
        AgentInfo,
        AdapterInfo,
        ModelInfo,
        Capture,
        RedactionState,
        Environment,
    ],
)
def test_every_model_is_frozen_forbids_unknown_fields_and_is_not_strict(
    model: type[BaseModel],
) -> None:
    config = model.model_config
    assert config.get("frozen") is True
    assert config.get("extra") == "forbid"
    assert "strict" not in config


def test_trace_version_field_is_independent_of_the_package_version() -> None:
    trace = Trace.model_validate(SEED)
    assert isinstance(trace.version, int)
    assert trace.version in SUPPORTED_VERSIONS["trace"]


def test_public_names_are_exported_and_the_version_alias_is_trace_specific() -> None:
    assert "TraceSchemaVersion" in trace_module.__all__
    assert "SchemaVersion" not in trace_module.__all__
    assert all(hasattr(trace_module, name) for name in trace_module.__all__)


# --- AD-4: the generated JSON Schema carries bounds, the version enum, descriptions ------


def _schema_properties(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Every property of the root and of every ``$defs`` entry, keyed ``Model.field``."""
    found: dict[str, dict[str, Any]] = {}
    for name, definition in [(schema["title"], schema), *schema.get("$defs", {}).items()]:
        for field, prop in definition.get("properties", {}).items():
            found[f"{name}.{field}"] = prop
    return found


def test_seq_and_duration_ms_export_minimum_zero() -> None:
    props = _schema_properties(Trace.model_json_schema())
    assert props["TraceEvent.seq"]["minimum"] == 0
    assert props["TraceEvent.seq"]["type"] == "integer"
    assert "ge" not in props["TraceEvent.seq"]
    [duration_int] = [
        option
        for option in props["TraceEvent.duration_ms"]["anyOf"]
        if option.get("type") == "integer"
    ]
    assert duration_int["minimum"] == 0


def test_version_exports_an_enum_of_the_supported_trace_versions() -> None:
    props = _schema_properties(Trace.model_json_schema())
    assert props["Trace.version"]["enum"] == list(SUPPORTED_VERSIONS["trace"]) == [1]
    assert props["Trace.version"]["type"] == "integer"


def test_every_serialized_field_has_a_description() -> None:
    props = _schema_properties(Trace.model_json_schema())
    model_names = {name.split(".")[0] for name in props}
    assert model_names == {
        "Trace",
        "TraceEvent",
        "ToolRef",
        "EventError",
        "AgentInfo",
        "AdapterInfo",
        "ModelInfo",
        "Capture",
        "RedactionState",
        "Environment",
    }
    missing = [name for name, prop in props.items() if not prop.get("description", "").strip()]
    assert missing == []


# --- Consistency Conventions: finite numbers, volatile path names ----------------------


@pytest.mark.parametrize("field", ["arguments", "result", "output", "metadata"])
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf], ids=["nan", "inf", "-inf"])
def test_non_finite_numbers_nested_in_event_payloads_are_rejected(field: str, bad: float) -> None:
    payload: Any = {"items": [1, {"amount": bad}]}
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(events=_events(0, **{field: payload})))
    [(loc, message)] = _errors(excinfo)
    assert loc == ("events", 0, field)
    assert "finite" in message
    assert "items.1.amount" in message
    assert _types(excinfo) == ["finite_number"]


def test_top_level_non_finite_output_is_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Trace.model_validate(_trace(events=_events(0, output=math.nan)))
    assert _locs(excinfo) == [("events", 0, "output")]
    assert _types(excinfo) == ["finite_number"]


def test_finite_floats_bools_and_ints_keep_their_types_in_payloads() -> None:
    event = Trace.model_validate(
        _trace(events=_events(0, arguments={"f": 1.0, "i": 1, "b": True, "n": None}))
    ).events[0]
    assert event.arguments == {"f": 1.0, "i": 1, "b": True, "n": None}
    arguments = event.arguments
    assert isinstance(arguments, dict)
    assert type(arguments["f"]) is float
    assert type(arguments["i"]) is int
    assert type(arguments["b"]) is bool


def test_volatile_trace_paths_name_real_trace_and_event_fields() -> None:
    prefix = "scenarios[*].trace."
    for path in VOLATILE_PATHS:
        if not path.startswith(prefix):
            continue
        head, _, tail = path.removeprefix(prefix).partition(".")
        if head == "events[*]":
            assert tail in TraceEvent.model_fields
        else:
            assert head in Trace.model_fields
            assert tail == ""
