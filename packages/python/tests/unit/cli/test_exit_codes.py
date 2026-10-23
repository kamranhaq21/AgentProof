"""``cli.exit_codes``: the AD-6 mapping, one test per branch, the constants, and the exact
surface (story 3.1 criterion 3; PRD AC-18.5, AC-26.4, AC-27.2, AC-27.3)."""

import ast
import inspect
from collections.abc import Sequence
from pathlib import Path

import pytest

from agentproof.cli import exit_codes
from agentproof.cli.exit_codes import from_comparison, from_outcome
from agentproof.models.common import Status
from agentproof.models.report import Comparison
from agentproof.models.result import (
    AssertionResult,
    ScenarioResult,
    SuiteOutcome,
    count_statuses,
)

CLI_ROOT = Path(__file__).resolve().parents[3] / "src" / "agentproof" / "cli"


def _scenario(
    scenario_id: str,
    status: Status,
    statuses: Sequence[Status],
    *,
    execution_error: str | None = None,
    skip_reason: str | None = None,
) -> ScenarioResult:
    """A ScenarioResult with one Assertion Result per status; the fold is given, not derived."""
    return ScenarioResult(
        scenario_id=scenario_id,
        status=status,
        execution_error=execution_error,
        skip_reason=skip_reason,
        counts=count_statuses(statuses),
        assertions=tuple(
            AssertionResult(
                assertion_id=f"a{index}",
                type="says",
                status=item,
                message="m",
                evidence=(),
            )
            for index, item in enumerate(statuses)
        ),
    )


def _outcome(
    scenarios: Sequence[ScenarioResult],
    suite_status: Status,
    *,
    execution_failed: bool = False,
    evaluated_assertions: int | None = None,
) -> SuiteOutcome:
    if evaluated_assertions is None:
        evaluated_assertions = sum(
            1
            for scenario in scenarios
            for result in scenario.assertions
            if result.status != "skipped"
        )
    return SuiteOutcome(
        scenarios=tuple(scenarios),
        suite_status=suite_status,
        execution_failed=execution_failed,
        evaluated_assertions=evaluated_assertions,
    )


def test_execution_failure_exits_3() -> None:
    """AC-27.3: an adapter raise or a missing Trace under fail_on_missing_trace is exit 3."""
    outcome = _outcome(
        [_scenario("s", "error", ["error"], execution_error="trace missing")],
        "error",
        execution_failed=True,
    )
    assert from_outcome(outcome) == 3


def test_execution_failure_outranks_an_assertion_failure() -> None:
    """AC-27.3, AC-27.4: 3 wins over 1 when a Scenario failed and another could not run."""
    outcome = _outcome(
        [
            _scenario("failed", "failed", ["failed", "passed"]),
            _scenario("broken", "error", ["error"], execution_error="adapter raised"),
        ],
        "failed",
        execution_failed=True,
    )
    assert from_outcome(outcome) == 3


def test_a_failed_suite_exits_1() -> None:
    outcome = _outcome([_scenario("s", "failed", ["failed", "passed"])], "failed")
    assert from_outcome(outcome) == 1


def test_an_assertion_only_error_exits_1() -> None:
    """AC-27.2: an Assertion that errored, with no execution failure, is 1 not 3."""
    outcome = _outcome([_scenario("s", "error", ["error", "passed"])], "error")
    assert outcome.execution_failed is False
    assert from_outcome(outcome) == 1


def test_nothing_evaluated_exits_1() -> None:
    """AC-18.5: every Scenario skipped means no Assertion was evaluated; never 0."""
    outcome = _outcome(
        [_scenario("s", "skipped", ["skipped", "skipped"], skip_reason="not today")],
        "skipped",
    )
    assert outcome.evaluated_assertions == 0
    assert from_outcome(outcome) == 1


def test_zero_evaluated_assertions_exits_1_whatever_the_status_says() -> None:
    """The branch is on ``evaluated_assertions``, not re-derived from the scenarios."""
    outcome = _outcome(
        [_scenario("s", "passed", ["passed"])],
        "passed",
        evaluated_assertions=0,
    )
    assert from_outcome(outcome) == 1


def test_a_passed_suite_with_evaluated_assertions_exits_0() -> None:
    outcome = _outcome(
        [
            _scenario("a", "passed", ["passed", "passed"]),
            _scenario("b", "skipped", ["skipped"], skip_reason="later"),
        ],
        "passed",
    )
    assert outcome.evaluated_assertions == 2
    assert from_outcome(outcome) == 0


@pytest.mark.parametrize(
    ("suite_status", "execution_failed", "evaluated", "expected"),
    [
        ("passed", False, 1, 0),
        ("passed", False, 0, 1),
        ("failed", False, 1, 1),
        ("error", False, 1, 1),
        ("skipped", False, 0, 1),
        ("passed", True, 1, 3),
        ("failed", True, 1, 3),
        ("error", True, 0, 3),
    ],
)
def test_from_outcome_grid(
    suite_status: Status, execution_failed: bool, evaluated: int, expected: int
) -> None:
    """The whole AD-6 table in one place: 3 if execution failed; else 1 on failed, error,
    or nothing evaluated; else 0."""
    execution_error = "adapter raised" if execution_failed else None
    scenario_status: Status = "error" if execution_failed else suite_status
    scenario = _scenario(
        "s",
        scenario_status,
        [scenario_status],
        execution_error=execution_error,
        skip_reason="skip" if scenario_status == "skipped" else None,
    )
    outcome = _outcome(
        [scenario],
        suite_status,
        execution_failed=execution_failed,
        evaluated_assertions=evaluated,
    )
    assert from_outcome(outcome) == expected


def test_a_regressed_comparison_exits_1() -> None:
    """AC-26.4: a Scenario went from passed to failed or error."""
    comparison = Comparison(
        baseline_suite_status="passed", current_suite_status="failed", regressed=True
    )
    assert from_comparison(comparison) == 1


def test_a_comparison_without_regression_exits_0() -> None:
    """Improvements and sequence-only changes are reported but do not fail (AC-26.4)."""
    comparison = Comparison(
        baseline_suite_status="failed",
        current_suite_status="passed",
        added_scenarios=("new",),
        regressed=False,
    )
    assert from_comparison(comparison) == 0


def test_the_named_constants_are_the_documented_codes() -> None:
    assert exit_codes.EXIT_OK == 0
    assert exit_codes.EXIT_FAILED == 1
    assert exit_codes.EXIT_INPUT_ERROR == 2
    assert exit_codes.EXIT_EXECUTION_ERROR == 3
    assert exit_codes.EXIT_INTERNAL_ERROR == 4


def test_the_codes_are_defined_once_and_app_py_has_no_literal_code() -> None:
    """app.py imports the constants; no integer 0 to 4 appears as a literal in it, and no
    other cli module assigns an ``EXIT_*`` name."""
    app_tree = ast.parse((CLI_ROOT / "app.py").read_text(encoding="utf-8"))
    literals = [
        node.value
        for node in ast.walk(app_tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, int)
        and not isinstance(node.value, bool)
        and 0 <= node.value <= 4
    ]
    assert literals == []
    for path in sorted(CLI_ROOT.rglob("*.py")):
        if path.name == "exit_codes.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assigned = {
            target.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign | ast.AnnAssign)
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
            if isinstance(target, ast.Name) and target.id.startswith("EXIT_")
        }
        assert assigned == set(), f"{path.name} redefines {assigned}"


def test_the_module_exposes_exactly_the_two_functions() -> None:
    assert exit_codes.__all__ == ["from_comparison", "from_outcome"]
    defined_here = {
        name
        for name, value in vars(exit_codes).items()
        if not name.startswith("_") and getattr(value, "__module__", None) == exit_codes.__name__
    }
    assert defined_here == set(exit_codes.__all__)


def test_the_signatures_are_the_ad_6_ones() -> None:
    outcome_signature = inspect.signature(from_outcome)
    assert list(outcome_signature.parameters) == ["outcome"]
    assert outcome_signature.parameters["outcome"].annotation is SuiteOutcome
    assert outcome_signature.return_annotation is int
    comparison_signature = inspect.signature(from_comparison)
    assert list(comparison_signature.parameters) == ["comparison"]
    assert comparison_signature.parameters["comparison"].annotation is Comparison
    assert comparison_signature.return_annotation is int
