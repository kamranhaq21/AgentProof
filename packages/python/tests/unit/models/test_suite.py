"""``agentproof.models.suite``: Suite, SuiteDefaults, Scenario, and the id rules.

Story 2.2 criteria 2 to 4: the spine's Suite YAML seed validates to the expected Suite;
every default has its documented value; assertion ids default to ``<type>-<index>``;
duplicate assertion ids, case-insensitive duplicate scenario ids, ids outside
``SCENARIO_ID_RE``, and Windows device names are rejected naming the id and the path;
unknown fields are rejected naming the path and assignment raises. The seed is parsed
here with ``yaml.safe_load`` (tests may; the models never do), everything else is a dict
literal, the way ``parse_suite`` will feed the models (AD-3).
"""

import math
from typing import get_args

import pytest
import yaml
from pydantic import ValidationError

from agentproof.constants import SCENARIO_ID_RE, SUPPORTED_VERSIONS, WINDOWS_DEVICE_NAMES
from agentproof.models.assertions import (
    ARGUMENT_PATH_PATTERN,
    FinalOutputContains,
    ToolCallCount,
    ToolNotCalled,
)
from agentproof.models.common import JsonValue
from agentproof.models.suite import (
    CompareDefaults,
    FixtureDefaults,
    RedactDefaults,
    Scenario,
    Suite,
    SuiteDefaults,
    validate_id,
)

# The Suite seed from the architecture spine, "Schemas (seed)": every key and value
# verbatim; one trailing comment shortened to fit the line length.
SPINE_SEED = """\
version: 1
suite: expense-agent              # id, same charset as scenario ids
description: "..."                # optional
defaults:                         # all optional
  adapter: fixture                # adapter name; CLI --adapter overrides
  fail_on_missing_trace: true
  fixture: {deterministic: true}  # runner derives run_id and timestamps from the fixture Trace
  compare: {include_arguments: ["approve_expense.amount"]}
  redact: {keys: [], paths: [], env: ["OPENAI_API_KEY"]}
scenarios:
  - id: reject-over-limit
    description: "..."            # optional
    skip: "reason"                # optional; presence means skipped
    input: {expense_amount: 5000} # JsonValue object passed to the adapter
    trace: traces/reject-over-limit.trace.json   # optional; fixture source and replay default
    assertions:
      - type: tool_not_called
        tool: approve_expense
      - type: tool_call_count
        tool: reject_expense
        equals: 1
      - id: says-rejected        # optional; default tool_called-2 style per AD-8
        type: final_output_contains
        value: "rejected"
        case_sensitive: true
"""

TOOL_CALLED: dict[str, JsonValue] = {"type": "tool_called", "tool": "approve_expense"}


def scenario(id: str = "reject-over-limit", **override: JsonValue) -> dict[str, JsonValue]:
    """A minimal valid Scenario dict with overrides."""
    base: dict[str, JsonValue] = {"id": id, "input": {}, "assertions": [dict(TOOL_CALLED)]}
    base.update(override)
    return base


def suite(**override: JsonValue) -> dict[str, JsonValue]:
    """A minimal valid Suite dict with overrides."""
    base: dict[str, JsonValue] = {"version": 1, "suite": "expense-agent", "scenarios": [scenario()]}
    base.update(override)
    return base


def errors(exc_info: pytest.ExceptionInfo[ValidationError]) -> list[tuple[tuple[object, ...], str]]:
    """``(loc, type)`` for every error, in order."""
    return [(tuple(error["loc"]), error["type"]) for error in exc_info.value.errors()]


def messages(exc_info: pytest.ExceptionInfo[ValidationError]) -> str:
    return "\n".join(error["msg"] for error in exc_info.value.errors())


# --- criterion 2: the spine seed and the defaults -----------------------------------------


def test_spine_seed_validates_to_the_expected_suite() -> None:
    loaded = yaml.safe_load(SPINE_SEED)
    result = Suite.model_validate(loaded)

    assert result.version == 1
    assert result.suite == "expense-agent"
    assert result.description == "..."
    assert result.defaults == SuiteDefaults(
        adapter="fixture",
        fail_on_missing_trace=True,
        fixture=FixtureDefaults(deterministic=True),
        compare=CompareDefaults(include_arguments=["approve_expense.amount"]),
        redact=RedactDefaults(keys=[], paths=[], env=["OPENAI_API_KEY"]),
    )
    assert len(result.scenarios) == 1
    only = result.scenarios[0]
    assert only.id == "reject-over-limit"
    assert only.description == "..."
    assert only.skip == "reason"
    assert only.input == {"expense_amount": 5000}
    assert only.trace == "traces/reject-over-limit.trace.json"
    assert only.assertions == (
        ToolNotCalled(id="tool_not_called-0", type="tool_not_called", tool="approve_expense"),
        ToolCallCount(
            id="tool_call_count-1", type="tool_call_count", tool="reject_expense", equals=1
        ),
        FinalOutputContains(
            id="says-rejected", type="final_output_contains", value="rejected", case_sensitive=True
        ),
    )
    assert result.defaults.compare.include_arguments == ("approve_expense.amount",)
    assert result.defaults.redact.env == ("OPENAI_API_KEY",)


def test_spine_seed_round_trips_through_model_dump_and_model_validate() -> None:
    first = Suite.model_validate(yaml.safe_load(SPINE_SEED))
    assert Suite.model_validate(first.model_dump()) == first


def test_minimal_suite_gets_the_documented_defaults() -> None:
    result = Suite.model_validate(suite())
    assert result.description is None
    assert result.defaults == SuiteDefaults()
    assert result.defaults.adapter is None
    assert result.defaults.fail_on_missing_trace is True
    assert result.defaults.fixture.deterministic is False
    assert result.defaults.compare.include_arguments == ()
    assert result.defaults.redact == RedactDefaults(keys=(), paths=(), env=())
    only = result.scenarios[0]
    assert only.description is None
    assert only.skip is None
    assert only.trace is None
    assert only.input == {}


def test_defaults_sections_are_each_optional() -> None:
    result = Suite.model_validate(suite(defaults={"fail_on_missing_trace": False}))
    assert result.defaults.fail_on_missing_trace is False
    assert result.defaults.fixture == FixtureDefaults()
    assert result.defaults.compare == CompareDefaults()
    assert result.defaults.redact == RedactDefaults()


def test_defaults_snapshot_dumps_every_field() -> None:
    # JSON mode writes the tuples as arrays; Python mode keeps the tuples.
    assert SuiteDefaults().model_dump(mode="json") == {
        "adapter": None,
        "fail_on_missing_trace": True,
        "fixture": {"deterministic": False},
        "compare": {"include_arguments": []},
        "redact": {"keys": [], "paths": [], "env": []},
    }
    assert SuiteDefaults().model_dump()["redact"] == {"keys": (), "paths": (), "env": ()}


def test_version_literal_matches_supported_versions() -> None:
    assert get_args(Suite.model_fields["version"].annotation) == SUPPORTED_VERSIONS["suite"]


@pytest.mark.parametrize(
    ("bad", "error_type"),
    [("1", "value_error"), (True, "value_error"), (1.0, "value_error"), (2, "literal_error")],
    ids=["string", "bool", "float", "other-integer"],
)
def test_version_must_be_the_integer_one(bad: object, error_type: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(version=bad))  # type: ignore[arg-type]
    assert errors(exc_info) == [(("version",), error_type)]


def test_missing_version_is_rejected_naming_the_field() -> None:
    document = suite()
    del document["version"]
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(document)
    assert errors(exc_info) == [(("version",), "missing")]


@pytest.mark.parametrize("field", ["suite", "scenarios"])
def test_missing_required_suite_field_is_rejected_naming_it(field: str) -> None:
    document = suite()
    del document[field]
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(document)
    assert errors(exc_info) == [((field,), "missing")]


def test_suite_needs_at_least_one_scenario() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(scenarios=[]))
    assert errors(exc_info) == [(("scenarios",), "too_short")]


@pytest.mark.parametrize("field", ["id", "input", "assertions"])
def test_missing_required_scenario_field_is_rejected_with_the_path(field: str) -> None:
    broken = scenario()
    del broken[field]
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(scenarios=[scenario(id="first"), broken]))
    assert errors(exc_info) == [(("scenarios", 1, field), "missing")]


def test_scenario_needs_at_least_one_assertion() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(scenarios=[scenario(assertions=[])]))
    assert errors(exc_info) == [(("scenarios", 0, "assertions"), "too_short")]


def test_unknown_assertion_type_is_rejected_with_the_scenario_path_and_tag() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(
            suite(scenarios=[scenario(assertions=[{"type": "tool_exists", "tool": "x"}])])
        )
    assert errors(exc_info) == [(("scenarios", 0, "assertions", 0), "union_tag_invalid")]
    assert "tool_exists" in messages(exc_info)


def test_tool_call_count_operator_rule_reports_the_scenario_path() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(
            suite(scenarios=[scenario(assertions=[{"type": "tool_call_count", "tool": "x"}])])
        )
    assert errors(exc_info) == [
        (("scenarios", 0, "assertions", 0, "tool_call_count"), "value_error")
    ]
    assert "exactly one of equals, greater_than, less_than" in messages(exc_info)


@pytest.mark.parametrize("field", ["skip", "trace"])
def test_skip_and_trace_are_optional_strings_that_cannot_be_empty(field: str) -> None:
    assert getattr(Suite.model_validate(suite()).scenarios[0], field) is None
    present = Suite.model_validate(suite(scenarios=[scenario(**{field: "x"})]))
    assert getattr(present.scenarios[0], field) == "x"
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(scenarios=[scenario(**{field: ""})]))
    assert errors(exc_info) == [(("scenarios", 0, field), "string_too_short")]


@pytest.mark.parametrize("bad", [None, 3, True, ["r"]], ids=["null", "int", "bool", "list"])
def test_present_skip_must_be_a_reason_string(bad: JsonValue) -> None:
    # Presence means skipped (spine seed), so ``skip: null`` is a mistake, not "not skipped".
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(scenarios=[scenario(skip=bad)]))
    assert errors(exc_info) == [(("scenarios", 0, "skip"), "value_error")]
    assert "skip needs a reason string" in messages(exc_info)


def test_absent_skip_is_none_and_a_present_reason_is_kept() -> None:
    assert Suite.model_validate(suite()).scenarios[0].skip is None
    result = Suite.model_validate(suite(scenarios=[scenario(skip="flaky upstream")]))
    assert result.scenarios[0].skip == "flaky upstream"


def test_input_is_a_json_object() -> None:
    nested: JsonValue = {"a": [1, 2.5, "x", None, True, {"b": {}}]}
    result = Suite.model_validate(suite(scenarios=[scenario(input=nested)]))
    assert result.scenarios[0].input == nested
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(scenarios=[scenario(input=[1, 2])]))
    assert errors(exc_info) == [(("scenarios", 0, "input"), "dict_type")]


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf], ids=["nan", "inf", "-inf"])
def test_non_finite_numbers_in_input_are_rejected(bad: float) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(scenarios=[scenario(input={"amount": [bad]})]))
    assert any(error["type"] == "finite_number" for error in exc_info.value.errors())


def test_redact_names_are_non_empty_and_paths_are_dotted() -> None:
    result = Suite.model_validate(
        suite(
            defaults={"redact": {"keys": ["Secret"], "paths": ["arguments.api_key"], "env": ["K"]}}
        )
    )
    assert result.defaults.redact == RedactDefaults(
        keys=("Secret",), paths=("arguments.api_key",), env=("K",)
    )
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(defaults={"redact": {"env": ["OK", ""], "keys": [""]}}))
    assert errors(exc_info) == [
        (("defaults", "redact", "keys", 0), "string_too_short"),
        (("defaults", "redact", "env", 1), "string_too_short"),
    ]
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(defaults={"redact": {"paths": ["a..b", "ok.path", "a b"]}}))
    assert errors(exc_info) == [
        (("defaults", "redact", "paths", 0), "string_pattern_mismatch"),
        (("defaults", "redact", "paths", 2), "string_pattern_mismatch"),
    ]


def test_compare_include_arguments_are_tool_dot_argument_paths() -> None:
    result = Suite.model_validate(
        suite(defaults={"compare": {"include_arguments": ["approve_expense.amount", "t.items.0"]}})
    )
    assert result.defaults.compare.include_arguments == ("approve_expense.amount", "t.items.0")
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(defaults={"compare": {"include_arguments": ["amount"]}}))
    assert errors(exc_info) == [(("defaults", "compare", "include_arguments", 0), "value_error")]
    text = messages(exc_info)
    assert "'amount'" in text
    assert "<tool>.<argument path>" in text
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(defaults={"compare": {"include_arguments": ["", "a. b"]}}))
    assert errors(exc_info) == [
        (("defaults", "compare", "include_arguments", 0), "string_pattern_mismatch"),
        (("defaults", "compare", "include_arguments", 1), "string_pattern_mismatch"),
    ]


def test_adapter_is_an_optional_non_empty_name() -> None:
    assert (
        Suite.model_validate(suite(defaults={"adapter": "fixture"})).defaults.adapter == "fixture"
    )
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(defaults={"adapter": ""}))
    assert errors(exc_info) == [(("defaults", "adapter"), "string_too_short")]


# --- criterion 3: assertion ids ------------------------------------------------------------


def test_assertions_without_id_get_type_and_zero_based_position() -> None:
    result = Suite.model_validate(
        suite(
            scenarios=[
                scenario(
                    assertions=[
                        {"type": "tool_called", "tool": "a"},
                        {"type": "tool_called", "tool": "b"},
                        {"type": "final_output_contains", "value": "x"},
                        {"type": "tool_order", "tools": ["a", "b"]},
                    ]
                )
            ]
        )
    )
    ids = [config.id for config in result.scenarios[0].assertions]
    # The index is the position in the Scenario list, not a per-type counter.
    assert ids == ["tool_called-0", "tool_called-1", "final_output_contains-2", "tool_order-3"]


def test_explicit_id_is_kept_and_does_not_shift_the_positions_of_others() -> None:
    result = Suite.model_validate(
        suite(
            scenarios=[
                scenario(
                    assertions=[
                        {"type": "tool_called", "tool": "a"},
                        {"id": "says-rejected", "type": "final_output_contains", "value": "x"},
                        {"type": "tool_called", "tool": "b"},
                    ]
                )
            ]
        )
    )
    ids = [config.id for config in result.scenarios[0].assertions]
    assert ids == ["tool_called-0", "says-rejected", "tool_called-2"]


def test_default_ids_are_assigned_per_scenario() -> None:
    result = Suite.model_validate(
        suite(
            scenarios=[
                scenario(id="first", assertions=[dict(TOOL_CALLED), dict(TOOL_CALLED)]),
                scenario(id="second", assertions=[dict(TOOL_CALLED)]),
            ]
        )
    )
    assert [c.id for c in result.scenarios[0].assertions] == ["tool_called-0", "tool_called-1"]
    assert [c.id for c in result.scenarios[1].assertions] == ["tool_called-0"]


def test_validated_scenario_never_carries_a_none_assertion_id() -> None:
    result = Scenario.model_validate(scenario(assertions=[dict(TOOL_CALLED), dict(TOOL_CALLED)]))
    assert all(config.id is not None for config in result.assertions)


def test_duplicate_assertion_ids_in_one_scenario_are_rejected_naming_id_and_path() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(
            suite(
                scenarios=[
                    scenario(id="first"),
                    scenario(
                        id="second",
                        assertions=[
                            {"id": "dup", "type": "tool_called", "tool": "a"},
                            {"type": "tool_called", "tool": "b"},
                            {"id": "dup", "type": "tool_not_called", "tool": "c"},
                        ],
                    ),
                ]
            )
        )
    # Reported at the later duplicate's own id, so the loader can print its path.
    assert errors(exc_info) == [(("scenarios", 1, "assertions", 2, "id"), "duplicate_assertion_id")]
    text = messages(exc_info)
    assert "'dup'" in text
    assert "scenario 'second'" in text
    assert "assertions[0]" in text and "assertions[2]" in text


def test_explicit_id_colliding_with_a_generated_default_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Scenario.model_validate(
            scenario(
                assertions=[
                    {"type": "tool_called", "tool": "a"},
                    {"id": "tool_called-0", "type": "tool_called", "tool": "b"},
                ]
            )
        )
    assert errors(exc_info) == [(("assertions", 1, "id"), "duplicate_assertion_id")]
    assert "'tool_called-0'" in messages(exc_info)


def test_same_assertion_id_in_different_scenarios_is_allowed() -> None:
    result = Suite.model_validate(
        suite(
            scenarios=[
                scenario(id="first", assertions=[{"id": "same", **TOOL_CALLED}]),
                scenario(id="second", assertions=[{"id": "same", **TOOL_CALLED}]),
            ]
        )
    )
    assert [s.assertions[0].id for s in result.scenarios] == ["same", "same"]


# --- criterion 3: scenario and suite ids --------------------------------------------------


@pytest.mark.parametrize(
    "good", ["reject-over-limit", "a.b_c", "R1", "0", "A" * 64, "x.trace.json"]
)
def test_scenario_id_in_the_charset_is_accepted(good: str) -> None:
    result = Suite.model_validate(suite(scenarios=[scenario(id=good)]))
    assert result.scenarios[0].id == good
    assert SCENARIO_ID_RE.fullmatch(good) is not None


@pytest.mark.parametrize("bad", ["-bad", "has space", "é", "A" * 65, "", "a/b", ".hidden", "a\\b"])
def test_scenario_id_outside_the_charset_is_rejected_naming_id_and_path(bad: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(scenarios=[scenario(id="ok"), scenario(id=bad)]))
    assert errors(exc_info) == [(("scenarios", 1, "id"), "value_error")]
    text = messages(exc_info)
    assert repr(bad) in text
    assert SCENARIO_ID_RE.pattern in text


@pytest.mark.parametrize("device", ["con", "CON", "Nul", "COM1", "lpt9", "com0", "AUX", "PRN"])
def test_windows_device_name_as_scenario_id_is_rejected_in_any_case(device: str) -> None:
    assert device.upper() in WINDOWS_DEVICE_NAMES
    assert SCENARIO_ID_RE.fullmatch(device) is not None, "the regex alone would accept it"
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(scenarios=[scenario(id=device)]))
    assert errors(exc_info) == [(("scenarios", 0, "id"), "value_error")]
    text = messages(exc_info)
    assert repr(device) in text
    assert "Windows device name" in text


@pytest.mark.parametrize("near_miss", ["con.txt", "console", "com10", "nul-1", "lpt"])
def test_names_that_merely_resemble_device_names_are_accepted(near_miss: str) -> None:
    assert (
        Suite.model_validate(suite(scenarios=[scenario(id=near_miss)])).scenarios[0].id == near_miss
    )


def test_scenario_ids_differing_only_by_case_are_rejected_naming_both() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(
            suite(scenarios=[scenario(id="reject"), scenario(id="other"), scenario(id="Reject")])
        )
    assert errors(exc_info) == [(("scenarios", 2, "id"), "duplicate_scenario_id")]
    text = messages(exc_info)
    assert "'Reject'" in text and "'reject'" in text
    assert "scenarios[2]" in text and "scenarios[0]" in text
    assert "case-insensitively" in text


def test_exact_duplicate_scenario_ids_are_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(scenarios=[scenario(id="same"), scenario(id="same")]))
    assert errors(exc_info) == [(("scenarios", 1, "id"), "duplicate_scenario_id")]
    assert "'same'" in messages(exc_info)


def test_distinct_scenario_ids_are_accepted() -> None:
    result = Suite.model_validate(suite(scenarios=[scenario(id="a"), scenario(id="b")]))
    assert [s.id for s in result.scenarios] == ["a", "b"]


@pytest.mark.parametrize("bad", ["bad id", "NUL", "", "-x"])
def test_suite_id_follows_the_scenario_id_rule(bad: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(suite=bad))
    assert errors(exc_info) == [(("suite",), "value_error")]
    assert repr(bad) in messages(exc_info)
    assert "suite id" in messages(exc_info)


def test_validate_id_is_the_one_implementation_and_returns_the_value() -> None:
    assert validate_id("ok-1", kind="scenario id") == "ok-1"
    with pytest.raises(ValueError, match="scenario id 'COM3' is a reserved Windows device name"):
        validate_id("COM3", kind="scenario id")
    with pytest.raises(ValueError, match="suite id ' ' must match"):
        validate_id(" ", kind="suite id")


# --- criterion 4: forbid unknown fields, frozen ---------------------------------------------


@pytest.mark.parametrize(
    ("document", "loc"),
    [
        (suite(scenario_count=1), ("scenario_count",)),
        (suite(defaults={"timeout": 5}), ("defaults", "timeout")),
        (suite(defaults={"fixture": {"path": "x"}}), ("defaults", "fixture", "path")),
        (suite(defaults={"compare": {"strict": True}}), ("defaults", "compare", "strict")),
        (suite(defaults={"redact": {"values": []}}), ("defaults", "redact", "values")),
        (suite(scenarios=[scenario(expected="x")]), ("scenarios", 0, "expected")),
        (
            suite(scenarios=[scenario(assertions=[{**TOOL_CALLED, "strict": True}])]),
            ("scenarios", 0, "assertions", 0, "tool_called", "strict"),
        ),
    ],
    ids=["suite", "defaults", "fixture", "compare", "redact", "scenario", "assertion"],
)
def test_unknown_field_at_every_level_is_rejected_naming_the_path(
    document: dict[str, JsonValue], loc: tuple[object, ...]
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(document)
    assert errors(exc_info) == [(loc, "extra_forbidden")]


def test_known_fields_at_every_level_are_accepted() -> None:
    document = suite(
        description="d",
        defaults={
            "adapter": "fixture",
            "fail_on_missing_trace": False,
            "fixture": {"deterministic": True},
            "compare": {"include_arguments": ["t.a"]},
            "redact": {"keys": ["k"], "paths": ["p"], "env": ["E"]},
        },
        scenarios=[scenario(description="d", skip="s", trace="t.json")],
    )
    assert Suite.model_validate(document).defaults.fixture.deterministic is True


def test_assignment_after_construction_raises_on_every_model() -> None:
    result = Suite.model_validate(yaml.safe_load(SPINE_SEED))
    targets: list[tuple[object, str]] = [
        (result, "suite"),
        (result.defaults, "adapter"),
        (result.defaults.fixture, "deterministic"),
        (result.defaults.compare, "include_arguments"),
        (result.defaults.redact, "env"),
        (result.scenarios[0], "id"),
        (result.scenarios[0].assertions[0], "id"),
    ]
    for target, field in targets:
        before = getattr(target, field)
        with pytest.raises(ValidationError) as exc_info:
            setattr(target, field, "changed")
        assert errors(exc_info) == [((field,), "frozen_instance")]
        assert getattr(target, field) == before


def test_models_declare_no_strict_mode() -> None:
    for model in (FixtureDefaults, CompareDefaults, RedactDefaults, SuiteDefaults, Scenario, Suite):
        assert model.model_config["frozen"] is True
        assert model.model_config["extra"] == "forbid"
        assert "strict" not in model.model_config


# --- all violations at once (AC-2.4): uniqueness rules fire beside element errors ----------


def test_duplicate_scenario_id_is_reported_even_when_that_scenario_is_invalid() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(
            suite(
                scenarios=[
                    scenario(id="a"),
                    scenario(id="A", assertions=[{"type": "tool_exists", "tool": "x"}]),
                ]
            )
        )
    assert errors(exc_info) == [
        (("scenarios", 1, "id"), "duplicate_scenario_id"),
        (("scenarios", 1, "assertions", 0), "union_tag_invalid"),
    ]
    text = messages(exc_info)
    assert "'A'" in text and "'a'" in text and "tool_exists" in text


def test_duplicate_assertion_id_is_reported_even_when_a_sibling_is_invalid() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Scenario.model_validate(
            scenario(
                assertions=[
                    {"id": "dup", "type": "tool_called", "tool": "a"},
                    {"id": "dup", "type": "tool_called", "tool": "b"},
                    {"type": "tool_called", "tool": ""},
                ]
            )
        )
    assert errors(exc_info) == [
        (("assertions", 1, "id"), "duplicate_assertion_id"),
        (("assertions", 2, "tool_called", "tool"), "string_too_short"),
    ]


def test_an_invalid_sibling_does_not_add_a_spurious_length_error() -> None:
    # pydantic-core counts only validated tuple items for ``min_length``; that line is
    # dropped so the user sees the element's own error and nothing else.
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(scenarios=[scenario(assertions=[{"type": "nope"}])]))
    assert errors(exc_info) == [(("scenarios", 0, "assertions", 0), "union_tag_invalid")]
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(scenarios=[scenario(skip=None)]))
    assert errors(exc_info) == [(("scenarios", 0, "skip"), "value_error")]


def test_raw_shapes_that_are_not_lists_or_mappings_still_report_the_type_error() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(scenarios={"a": 1}))
    assert errors(exc_info) == [(("scenarios",), "tuple_type")]
    with pytest.raises(ValidationError) as exc_info:
        Suite.model_validate(suite(scenarios=[scenario(), 3]))
    assert errors(exc_info) == [(("scenarios", 1), "model_type")]
    with pytest.raises(ValidationError) as exc_info:
        Scenario.model_validate(scenario(assertions="tool_called"))
    assert errors(exc_info) == [(("assertions",), "tuple_type")]
    with pytest.raises(ValidationError) as exc_info:
        Scenario.model_validate(scenario(assertions=[5]))
    assert errors(exc_info) == [(("assertions", 0), "model_attributes_type")]


def test_explicit_null_assertion_id_gets_the_default() -> None:
    result = Scenario.model_validate(scenario(assertions=[{"id": None, **TOOL_CALLED}]))
    assert result.assertions[0].id == "tool_called-0"


# --- shallow frozen: sequences are tuples, mappings are plain dicts -------------------------


def test_sequence_fields_are_tuples_that_cannot_be_appended_to() -> None:
    result = Suite.model_validate(yaml.safe_load(SPINE_SEED))
    assert isinstance(result.scenarios, tuple)
    assert isinstance(result.scenarios[0].assertions, tuple)
    assert isinstance(result.defaults.compare.include_arguments, tuple)
    assert isinstance(result.defaults.redact.env, tuple)
    with pytest.raises(AttributeError):
        result.scenarios.append(result.scenarios[0])  # type: ignore[attr-defined]
    assert len(result.scenarios) == 1
    assert isinstance(result.scenarios[0].input, dict), "mapping fields are not deep-frozen"


def test_json_dump_writes_arrays_and_json_schema_exports_array_types() -> None:
    result = Suite.model_validate(yaml.safe_load(SPINE_SEED))
    dumped = result.model_dump(mode="json")
    assert isinstance(dumped["scenarios"], list)
    assert isinstance(dumped["scenarios"][0]["assertions"], list)
    assert dumped["defaults"]["compare"]["include_arguments"] == ["approve_expense.amount"]
    assert dumped["defaults"]["redact"]["env"] == ["OPENAI_API_KEY"]
    assert Suite.model_validate(dumped) == result

    schema = Suite.model_json_schema()
    assert schema["properties"]["scenarios"]["type"] == "array"
    assert schema["properties"]["scenarios"]["minItems"] == 1
    assert schema["$defs"]["Scenario"]["properties"]["assertions"]["type"] == "array"
    assert schema["$defs"]["Scenario"]["properties"]["assertions"]["minItems"] == 1
    for name in ("keys", "paths", "env"):
        assert schema["$defs"]["RedactDefaults"]["properties"][name]["type"] == "array"
    include = schema["$defs"]["CompareDefaults"]["properties"]["include_arguments"]
    assert include["type"] == "array"
    assert include["items"]["pattern"] == ARGUMENT_PATH_PATTERN
