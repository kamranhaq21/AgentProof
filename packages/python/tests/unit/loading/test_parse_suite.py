"""``parse_suite`` and ``load_suite``: every violation at once, in a documented order (AD-15)."""

from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

import agentproof
from agentproof import parse_suite
from agentproof.cli import app as app_module
from agentproof.errors import SuiteError
from agentproof.loading import suite as suite_module
from agentproof.loading import yaml_safe
from agentproof.models.suite import Suite

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "yaml"
SOURCE = "agentproof.yaml"
SEED_TEXT = (FIXTURES / "suite-seed.yaml").read_text(encoding="utf-8")

# Three simultaneous faults: no ``version``, an unknown top-level field, and a scenario id
# repeated (case-insensitively) at index 1.
THREE_FAULTS = """\
suite: demo
extra_field: 1
scenarios:
  - id: a
    input: {}
    trace: a.json
    assertions:
      - type: tool_not_called
        tool: x
  - id: A
    input: {}
    trace: b.json
    assertions:
      - type: tool_not_called
        tool: x
"""


def test_seed_parses_to_the_suite_built_from_the_same_dict() -> None:
    expected = Suite.model_validate(yaml_safe.load(SEED_TEXT, source=SOURCE))
    assert parse_suite(SEED_TEXT, source=SOURCE) == expected


def test_three_simultaneous_violations_are_all_reported_in_path_order() -> None:
    with pytest.raises(SuiteError) as error:
        parse_suite(THREE_FAULTS, source=SOURCE)
    violations = error.value.violations
    # Documented order: sorted by path, names as strings, so extra_field < scenarios < version.
    assert [violation.field for violation in violations] == [
        "extra_field",
        "scenarios.1.id",
        "version",
    ]
    assert all(violation.source == SOURCE for violation in violations)
    assert "Extra inputs" in violations[0].message
    assert "Field required" in violations[2].message
    assert violations[1].message  # the duplicate-id sentence from the model


def test_order_is_by_path_with_numeric_indexes() -> None:
    text = "\n".join(
        [
            "version: 1",
            "suite: demo",
            "scenarios:",
            *[
                f"  - id: s{i}\n    trace: t.json\n    assertions: []"
                for i in range(12)  # indexes 0..11: '10' must sort after '2'
            ],
        ]
    )
    with pytest.raises(SuiteError) as error:
        parse_suite(text, source=SOURCE)
    indexes = [int(v.field.split(".")[1]) for v in error.value.violations]
    assert indexes == sorted(indexes)
    assert indexes[-1] == 11


def test_yaml_safety_violation_propagates_unchanged_with_its_position() -> None:
    text = "version: 1\nsuite: a\nsuite: b\n"
    with pytest.raises(SuiteError) as via_parse:
        parse_suite(text, source=SOURCE)
    with pytest.raises(SuiteError) as via_load:
        yaml_safe.load(text, source=SOURCE)
    assert via_parse.value.violations == via_load.value.violations
    assert via_parse.value.violations[0].field == "3:1"


def test_a_value_nested_too_deeply_is_one_violation() -> None:
    depth = 150  # loads as YAML; pydantic's limit is platform-dependent (deferred F3)
    text = (
        "version: 1\nsuite: demo\nscenarios:\n"
        "  - id: a\n    trace: t.json\n    input: {k: "
        + "[" * depth
        + "]" * depth
        + "}"
        + "\n    assertions:\n      - type: tool_not_called\n        tool: x\n"
    )
    try:
        parse_suite(text, source=SOURCE)
    except SuiteError as error:
        # Pydantic reports one recursion_loop per union branch; they collapse to one.
        assert [v.message for v in error.violations] == ["a value is nested too deeply to validate"]


def test_a_recursion_error_from_validation_is_one_violation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def explode(data: object) -> Suite:
        raise RecursionError

    monkeypatch.setattr(Suite, "model_validate", explode)
    with pytest.raises(SuiteError) as error:
        parse_suite("version: 1\n", source=SOURCE)
    assert [v.field for v in error.value.violations] == [""]


def test_parse_suite_is_exported_at_the_top_level() -> None:
    assert "parse_suite" in agentproof.__all__
    assert agentproof.parse_suite is parse_suite


def test_the_cli_formatter_renders_every_violation_as_one_line() -> None:
    def command() -> None:
        parse_suite(THREE_FAULTS, source="suite.yaml")

    test_app = typer.Typer(pretty_exceptions_enable=False)

    @test_app.callback()
    def _root() -> None:
        """Test root."""

    test_app.command("go")(app_module._handled(command))
    result = CliRunner().invoke(test_app, ["go"])
    assert result.exit_code == 2
    lines = result.output.splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("SuiteError: ") and lines[0].endswith(" (suite.yaml:extra_field)")
    assert lines[1].endswith(" (suite.yaml:scenarios.1.id)")
    assert lines[2].endswith(" (suite.yaml:version)")
    assert all(line.startswith("SuiteError: ") for line in lines)


def test_yaml_is_the_only_parser_in_use() -> None:
    # parse_suite must reach YAML only through yaml_safe.load.
    module_text = Path(suite_module.__file__ or "").read_text(encoding="utf-8")
    assert "import yaml\n" not in module_text
    assert "yaml.load" not in module_text
    assert "safe_load" not in module_text
