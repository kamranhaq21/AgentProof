"""``agentproof.constants`` holds every shared rule with the value the architecture fixes."""

import dataclasses
import re

import pytest

from agentproof.constants import (
    MAX_REPORT_BYTES,
    MAX_SUITE_BYTES,
    MAX_TRACE_BYTES,
    REDACTED,
    RFC3339_WITH_OFFSET,
    SCENARIO_ID_RE,
    STATEMENTS,
    SUPPORTED_VERSIONS,
    WINDOWS_DEVICE_NAMES,
    Statements,
)

FIVE_MEGABYTES = 5 * 1024 * 1024

SENTENCE_FIELDS = (
    "compare_is_saved_data",
    "redaction_limits",
    "capture_limited",
    "limits_v01",
    "artifacts_visible_to_readers",
)
STATEMENT_FIELDS = (*SENTENCE_FIELDS[:3], "capture_declaration", *SENTENCE_FIELDS[3:])


def test_supported_versions_list_version_one_for_each_artifact_kind() -> None:
    assert SUPPORTED_VERSIONS == {"suite": (1,), "trace": (1,), "report": (1,)}
    assert all(isinstance(versions, tuple) for versions in SUPPORTED_VERSIONS.values())


def test_redaction_marker_is_the_bracketed_word() -> None:
    assert REDACTED == "[REDACTED]"


def test_size_limits_are_five_megabytes_each() -> None:
    assert MAX_SUITE_BYTES == FIVE_MEGABYTES
    assert MAX_TRACE_BYTES == FIVE_MEGABYTES
    assert MAX_REPORT_BYTES == FIVE_MEGABYTES


def test_regexes_are_compiled_patterns() -> None:
    assert isinstance(SCENARIO_ID_RE, re.Pattern)
    assert isinstance(RFC3339_WITH_OFFSET, re.Pattern)


@pytest.mark.parametrize(
    "scenario_id",
    ["reject-over-limit", "Reject", "a.b_c", "a" * 64, "1", "x-", "x.", "x_"],
)
def test_scenario_id_regex_accepts_the_charset(scenario_id: str) -> None:
    assert SCENARIO_ID_RE.fullmatch(scenario_id) is not None


@pytest.mark.parametrize(
    "scenario_id",
    ["-bad", "has space", "a" * 65, "", ".hidden", "_x", "é", "a/b", "a\\b", "a\n"],
)
def test_scenario_id_regex_rejects_bad_ids(scenario_id: str) -> None:
    assert SCENARIO_ID_RE.fullmatch(scenario_id) is None


def test_regex_alone_matches_device_names_the_model_rejects_them() -> None:
    # Matrix row: the device-name check is the model's job (case-insensitive); the regex
    # accepts ``con`` and the upper-cased lookup in the set is what catches it.
    assert SCENARIO_ID_RE.fullmatch("con") is not None
    assert "con".upper() in WINDOWS_DEVICE_NAMES
    assert "Com1".upper() in WINDOWS_DEVICE_NAMES
    assert "console".upper() not in WINDOWS_DEVICE_NAMES


def test_windows_device_names_are_the_reserved_set_in_upper_case() -> None:
    expected = (
        {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
        | {f"COM{digit}" for digit in range(10)}
        | {f"LPT{digit}" for digit in range(10)}
    )
    assert WINDOWS_DEVICE_NAMES == frozenset(expected)
    assert len(WINDOWS_DEVICE_NAMES) == 26
    assert all(name == name.upper() for name in WINDOWS_DEVICE_NAMES)


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-10-22T13:05:00+00:00",
        "2026-10-22T13:05:00Z",
        "2026-10-22T13:05:00.123456-05:00",
        "2026-10-22T13:05:00.1Z",
        "2026-10-22T13:05:00.123456789+09:30",
    ],
)
def test_rfc3339_regex_accepts_offset_and_zulu_forms(timestamp: str) -> None:
    assert RFC3339_WITH_OFFSET.fullmatch(timestamp) is not None


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-10-22T13:05:00",
        "2026-10-22 13:05:00Z",
        "2026-10-22T13:05:00+0000",
        "2026-10-22T13:05:00.Z",
        "2026-10-22T13:05:00.1234567890Z",
        "２０２６-１０-２２T１３:０５:００Z",
        "2026-10-22T13:05Z",
        "2026-10-22",
        "",
    ],
)
def test_rfc3339_regex_rejects_naive_and_malformed_timestamps(timestamp: str) -> None:
    assert RFC3339_WITH_OFFSET.fullmatch(timestamp) is None


def test_statements_is_a_frozen_dataclass_instance_with_six_named_fields() -> None:
    assert dataclasses.is_dataclass(Statements)
    assert isinstance(STATEMENTS, Statements)
    assert tuple(field.name for field in dataclasses.fields(Statements)) == STATEMENT_FIELDS
    assert len(STATEMENT_FIELDS) == 6
    with pytest.raises(dataclasses.FrozenInstanceError):
        STATEMENTS.compare_is_saved_data = "changed"  # type: ignore[misc]


def test_capture_declaration_formats_the_trace_capture_value() -> None:
    assert STATEMENTS.capture_declaration == "capture: {tool_calls}"
    assert STATEMENTS.capture_declaration.format(tool_calls="partial") == "capture: partial"


@pytest.mark.parametrize("field", SENTENCE_FIELDS)
def test_each_statement_is_one_plain_sentence(field: str) -> None:
    sentence = getattr(STATEMENTS, field)
    assert isinstance(sentence, str)
    assert sentence == sentence.strip()
    assert sentence.endswith(".")
    assert ". " not in sentence, "a statement is exactly one sentence"
    assert "\n" not in sentence


@pytest.mark.parametrize(
    ("field", "phrases"),
    [
        ("compare_is_saved_data", ("exact comparison of saved data",)),
        ("redaction_limits", ("configured keys", "environment values", "inspect")),
        ("capture_limited", ("adapter observed",)),
        ("limits_v01", ("stochastic", "runtime", "configured keys")),
        ("artifacts_visible_to_readers", ("read access",)),
    ],
)
def test_each_statement_carries_its_prd_claim(field: str, phrases: tuple[str, ...]) -> None:
    sentence = getattr(STATEMENTS, field)
    for phrase in phrases:
        assert phrase in sentence, f"{field} must mention {phrase!r}"
