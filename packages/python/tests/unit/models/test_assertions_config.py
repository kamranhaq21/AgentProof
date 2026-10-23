"""``agentproof.models.assertions``: the six config models and the discriminated union.

Story 2.2 criterion 1 (and the assertion-level rows of criterion 4): one passing and one
failing case per rule. Models are validated from dicts only, the way ``parse_suite`` will
feed them (AD-3). Every failing test asserts the Pydantic ``loc`` so the field path a user
sees is part of the contract.
"""

from typing import get_args

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from agentproof.models.assertions import (
    ARGUMENT_PATH_PATTERN,
    ASSERTION_MODELS,
    ASSERTION_TYPES,
    MODEL_CONFIG,
    OPERATORS,
    AssertionConfig,
    AssertionConfigBase,
    FinalOutputContains,
    Operator,
    ToolArgumentsMatch,
    ToolCallCount,
    ToolCalled,
    ToolNotCalled,
    ToolOrder,
)

ADAPTER: TypeAdapter[AssertionConfig] = TypeAdapter(AssertionConfig)

MODELS: tuple[type[AssertionConfigBase], ...] = (
    ToolCalled,
    ToolNotCalled,
    ToolCallCount,
    ToolArgumentsMatch,
    ToolOrder,
    FinalOutputContains,
)

# One valid flat mapping per type, in the only YAML form AD-8 allows.
VALID: dict[str, dict[str, object]] = {
    "tool_called": {"type": "tool_called", "tool": "approve_expense"},
    "tool_not_called": {"type": "tool_not_called", "tool": "approve_expense"},
    "tool_call_count": {"type": "tool_call_count", "tool": "reject_expense", "equals": 1},
    "tool_arguments_match": {
        "type": "tool_arguments_match",
        "tool": "approve_expense",
        "arguments": {"amount": 5000, "items.0.amount": 12.5},
    },
    "tool_order": {"type": "tool_order", "tools": ["confirm_with_user", "delete_file"]},
    "final_output_contains": {"type": "final_output_contains", "value": "rejected"},
}


def errors(exc_info: pytest.ExceptionInfo[ValidationError]) -> list[tuple[tuple[object, ...], str]]:
    """``(loc, type)`` for every error, in order."""
    return [(tuple(error["loc"]), error["type"]) for error in exc_info.value.errors()]


def messages(exc_info: pytest.ExceptionInfo[ValidationError]) -> str:
    return "\n".join(error["msg"] for error in exc_info.value.errors())


# --- criterion 1: six models, their type literals, the union -------------------------------


def test_six_models_exist_with_their_type_literals_in_order() -> None:
    assert ASSERTION_MODELS == MODELS
    literals = tuple(get_args(model.model_fields["type"].annotation)[0] for model in MODELS)
    assert literals == ASSERTION_TYPES, "ASSERTION_TYPES is derived from the models"
    assert ASSERTION_TYPES == (
        "tool_called",
        "tool_not_called",
        "tool_call_count",
        "tool_arguments_match",
        "tool_order",
        "final_output_contains",
    )


@pytest.mark.parametrize("type_name", ASSERTION_TYPES)
def test_union_picks_the_model_for_each_type(type_name: str) -> None:
    config = ADAPTER.validate_python(VALID[type_name])
    assert config.type == type_name
    assert type(config) is MODELS[ASSERTION_TYPES.index(type_name)]
    assert config.id is None, "the default id is the Scenario's job, not the model's"


def test_union_rejects_an_unknown_type_naming_the_tag() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ADAPTER.validate_python({"type": "tool_exists", "tool": "x"})
    assert errors(exc_info) == [((), "union_tag_invalid")]
    assert "tool_exists" in messages(exc_info)
    for type_name in ASSERTION_TYPES:
        assert type_name in messages(exc_info)


def test_union_rejects_a_missing_type() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ADAPTER.validate_python({"tool": "x"})
    assert errors(exc_info) == [((), "union_tag_not_found")]


def test_union_is_discriminated_on_type() -> None:
    schema = ADAPTER.json_schema()
    assert schema["discriminator"]["propertyName"] == "type"
    assert set(schema["discriminator"]["mapping"]) == set(ASSERTION_TYPES)
    assert len(schema["oneOf"]) == len(ASSERTION_TYPES)


def test_every_model_is_frozen_and_forbids_unknown_fields_and_rejects_nan() -> None:
    assert MODEL_CONFIG == {"frozen": True, "extra": "forbid", "allow_inf_nan": False}
    for model in MODELS:
        assert model.model_config["frozen"] is True
        assert model.model_config["extra"] == "forbid"
        assert "strict" not in model.model_config, "AD-3: no model-level strict mode"


# --- criterion 1: fields per PRD FR-11 to FR-16 --------------------------------------------


def test_tool_called_and_tool_not_called_carry_the_tool() -> None:
    assert ToolCalled.model_validate(VALID["tool_called"]).tool == "approve_expense"
    assert ToolNotCalled.model_validate(VALID["tool_not_called"]).tool == "approve_expense"


@pytest.mark.parametrize("model", [ToolCalled, ToolNotCalled, ToolCallCount, ToolArgumentsMatch])
def test_tool_is_required_and_non_empty(model: type[AssertionConfigBase]) -> None:
    type_name = get_args(model.model_fields["type"].annotation)[0]
    with pytest.raises(ValidationError) as exc_info:
        model.model_validate({"type": type_name})
    assert (("tool",), "missing") in errors(exc_info)
    with pytest.raises(ValidationError) as exc_info:
        model.model_validate({**VALID[type_name], "tool": ""})
    assert (("tool",), "string_too_short") in errors(exc_info)


def test_tool_arguments_match_maps_paths_to_json_values() -> None:
    config = ToolArgumentsMatch.model_validate(
        {
            "type": "tool_arguments_match",
            "tool": "t",
            "arguments": {
                "amount": 5000,
                "items.0.amount": 12.5,
                "note": None,
                "ok": True,
                "nested": {"a": [1, "two", None]},
            },
        }
    )
    assert config.arguments == {
        "amount": 5000,
        "items.0.amount": 12.5,
        "note": None,
        "ok": True,
        "nested": {"a": [1, "two", None]},
    }


def test_tool_arguments_match_rejects_an_empty_mapping() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ToolArgumentsMatch.model_validate(
            {"type": "tool_arguments_match", "tool": "t", "arguments": {}}
        )
    assert errors(exc_info) == [(("arguments",), "too_short")]


@pytest.mark.parametrize("path", ["", "a..b", ".a", "a.", " a . b ", "a b", "a\tb", "a.\nb"])
def test_tool_arguments_match_rejects_a_malformed_path_naming_it(path: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        ToolArgumentsMatch.model_validate(
            {"type": "tool_arguments_match", "tool": "t", "arguments": {path: 1}}
        )
    # The path is the loc itself (dict key), the error names the pattern, and ``input``
    # carries the offending key.
    assert errors(exc_info) == [(("arguments", path, "[key]"), "string_pattern_mismatch")]
    assert exc_info.value.errors()[0]["input"] == path
    assert ARGUMENT_PATH_PATTERN in messages(exc_info)


@pytest.mark.parametrize("path", ["a", "items.0.amount", "a_b.c-d.0.e$f", "0", "ключ.値"])
def test_tool_arguments_match_accepts_dotted_paths(path: str) -> None:
    config = ToolArgumentsMatch.model_validate(
        {"type": "tool_arguments_match", "tool": "t", "arguments": {path: 1}}
    )
    assert config.arguments == {path: 1}


def test_argument_path_pattern_is_in_the_exported_json_schema() -> None:
    schema = ToolArgumentsMatch.model_json_schema()
    arguments = schema["properties"]["arguments"]
    assert arguments["type"] == "object"
    assert arguments["minProperties"] == 1
    # Pydantic exports a constrained dict key as ``patternProperties``, so the schema and
    # the Python validation state the same grammar.
    assert list(arguments["patternProperties"]) == [ARGUMENT_PATH_PATTERN]


def test_tool_order_carries_the_tools_as_a_tuple_in_order() -> None:
    config = ToolOrder.model_validate(VALID["tool_order"])
    assert config.tools == ("confirm_with_user", "delete_file")
    assert isinstance(config.tools, tuple), "sequence fields are tuples (shallow frozen)"
    single = ToolOrder.model_validate({"type": "tool_order", "tools": ["only"]})
    assert single.tools == ("only",)


def test_tool_order_is_hashable_and_dumps_tools_as_a_json_array() -> None:
    config = ToolOrder.model_validate(VALID["tool_order"])
    assert hash(config) == hash(ToolOrder.model_validate(VALID["tool_order"]))
    assert {config: 1}[ToolOrder.model_validate(VALID["tool_order"])] == 1
    assert config.model_dump(mode="json")["tools"] == ["confirm_with_user", "delete_file"]
    assert config.model_dump()["tools"] == ("confirm_with_user", "delete_file")
    with pytest.raises(AttributeError):
        config.tools.append("x")  # type: ignore[attr-defined]
    tools_schema = ToolOrder.model_json_schema()["properties"]["tools"]
    assert tools_schema["type"] == "array"
    assert tools_schema["minItems"] == 1


def test_tool_order_rejects_an_empty_list_and_an_empty_name() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ToolOrder.model_validate({"type": "tool_order", "tools": []})
    assert errors(exc_info) == [(("tools",), "too_short")]
    with pytest.raises(ValidationError) as exc_info:
        ToolOrder.model_validate({"type": "tool_order", "tools": ["a", ""]})
    assert errors(exc_info) == [(("tools", 1), "string_too_short")]


def test_final_output_contains_value_and_case_sensitive_default_true() -> None:
    config = FinalOutputContains.model_validate(VALID["final_output_contains"])
    assert config.value == "rejected"
    assert config.case_sensitive is True
    insensitive = FinalOutputContains.model_validate(
        {"type": "final_output_contains", "value": "Rejected", "case_sensitive": False}
    )
    assert insensitive.case_sensitive is False


def test_final_output_contains_rejects_a_missing_or_empty_value() -> None:
    with pytest.raises(ValidationError) as exc_info:
        FinalOutputContains.model_validate({"type": "final_output_contains"})
    assert errors(exc_info) == [(("value",), "missing")]
    with pytest.raises(ValidationError) as exc_info:
        FinalOutputContains.model_validate({"type": "final_output_contains", "value": ""})
    assert errors(exc_info) == [(("value",), "string_too_short")]


# --- criterion 1: optional id ------------------------------------------------------------------


def test_id_is_optional_and_kept_when_given() -> None:
    assert ToolCalled.model_validate(VALID["tool_called"]).id is None
    config = ToolCalled.model_validate({**VALID["tool_called"], "id": "says-rejected"})
    assert config.id == "says-rejected"


def test_id_rejects_the_empty_string_and_non_strings() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ToolCalled.model_validate({**VALID["tool_called"], "id": ""})
    assert errors(exc_info) == [(("id",), "string_too_short")]
    with pytest.raises(ValidationError) as exc_info:
        ToolCalled.model_validate({**VALID["tool_called"], "id": 3})
    assert errors(exc_info) == [(("id",), "string_type")]


# --- criterion 1: tool_call_count takes exactly one operator (AC-13.2) --------------------


@pytest.mark.parametrize("operator", OPERATORS)
def test_tool_call_count_accepts_each_operator_alone(operator: Operator) -> None:
    config = ToolCallCount.model_validate({"type": "tool_call_count", "tool": "t", operator: 2})
    assert config.operator == (operator, 2)
    others = set(OPERATORS) - {operator}
    assert all(getattr(config, other) is None for other in others)


def test_operators_tuple_matches_the_operator_literal_in_order() -> None:
    assert get_args(Operator) == ("equals", "greater_than", "less_than")
    assert OPERATORS == get_args(Operator)
    config = ToolCallCount.model_validate({"type": "tool_call_count", "tool": "t", "less_than": 3})
    name, bound = config.operator
    assert name in get_args(Operator)
    assert bound == 3


def test_tool_call_count_accepts_zero_as_a_bound() -> None:
    config = ToolCallCount.model_validate({"type": "tool_call_count", "tool": "t", "equals": 0})
    assert config.operator == ("equals", 0)


def test_tool_call_count_with_no_operator_is_rejected_naming_the_fields() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ToolCallCount.model_validate({"type": "tool_call_count", "tool": "t"})
    assert errors(exc_info) == [((), "value_error")]
    text = messages(exc_info)
    assert "exactly one of equals, greater_than, less_than" in text
    assert "got none" in text


def test_tool_call_count_with_two_operators_is_rejected_naming_the_fields() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ToolCallCount.model_validate(
            {"type": "tool_call_count", "tool": "t", "equals": 1, "less_than": 2}
        )
    assert errors(exc_info) == [((), "value_error")]
    assert "got equals, less_than" in messages(exc_info)


def test_tool_call_count_with_three_operators_is_rejected() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ToolCallCount.model_validate(
            {"type": "tool_call_count", "tool": "t", "equals": 1, "greater_than": 0, "less_than": 2}
        )
    assert "got equals, greater_than, less_than" in messages(exc_info)


@pytest.mark.parametrize(
    ("bad", "error_type"),
    [(-1, "greater_than_equal"), ("1", "int_type"), (1.0, "int_type"), (True, "int_type")],
    ids=["negative", "string", "float", "bool"],
)
def test_tool_call_count_needs_a_non_negative_integer(bad: object, error_type: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        ToolCallCount.model_validate({"type": "tool_call_count", "tool": "t", "equals": bad})
    assert errors(exc_info) == [(("equals",), error_type)]


# --- criterion 4 at assertion level: forbid unknown, frozen ---------------------------------


@pytest.mark.parametrize("type_name", ASSERTION_TYPES)
def test_unknown_field_is_rejected_naming_it(type_name: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        ADAPTER.validate_python({**VALID[type_name], "strict": True})
    assert errors(exc_info) == [((type_name, "strict"), "extra_forbidden")]


@pytest.mark.parametrize("type_name", ASSERTION_TYPES)
def test_assignment_after_construction_raises(type_name: str) -> None:
    config = ADAPTER.validate_python(VALID[type_name])
    with pytest.raises(ValidationError) as exc_info:
        config.id = "late"
    assert errors(exc_info) == [(("id",), "frozen_instance")]
    assert config.id is None


def test_the_literal_type_cannot_be_changed_to_another_model_type() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ToolCalled.model_validate({"type": "tool_not_called", "tool": "t"})
    assert errors(exc_info) == [(("type",), "literal_error")]


def test_base_class_is_a_pydantic_model_with_the_shared_config() -> None:
    assert issubclass(AssertionConfigBase, BaseModel)
    for key, value in MODEL_CONFIG.items():
        assert AssertionConfigBase.model_config[key] == value
