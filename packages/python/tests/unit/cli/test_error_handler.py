"""The one error handler through Typer's ``CliRunner`` (story 3.1 criterion 2; AD-7; PRD
AC-28.1).

A test app is built from the real root callback (``--verbose``, ``--no-color``) and the
real ``_handled`` wrapper around commands that raise each exception family, so the
handler is exercised exactly as ``cli/app.py`` uses it without adding commands to the
shipped app.
"""

import pytest
import typer
from typer.testing import CliRunner

from agentproof.cli import app as app_module
from agentproof.errors import (
    InputError,
    PathError,
    SuiteError,
    TraceMissingError,
    Violation,
)

runner = CliRunner()

SECRET = "sk-live-planted-secret-value"

VIOLATIONS = [
    Violation(source="suite.yaml", field="scenarios.0.id", message="duplicate id 'a'"),
    Violation(source="suite.yaml", field="version", message="unsupported version 2"),
]


def two_violations() -> None:
    raise SuiteError(VIOLATIONS)


def no_violations() -> None:
    raise InputError([])


def whole_document() -> None:
    raise PathError([Violation(source="missing.yaml", field="", message="file not found")])


def with_argument(name: str) -> None:
    raise SuiteError([Violation(source=name, field="id", message="bad id")])


def execution() -> None:
    raise TraceMissingError("no trace for reject-over-limit")


def boom() -> None:
    raise RuntimeError("boom")


def silent() -> None:
    raise RuntimeError()


def passthrough() -> None:
    raise typer.Exit(7)


def fine() -> None:
    typer.echo("ok")


def leaks_in_execution_error() -> None:
    raise TraceMissingError(f"adapter failed with token {SECRET}")


def leaks_in_internal_error() -> None:
    raise RuntimeError(f"connection to host failed with token {SECRET}")


def leaks_in_violation() -> None:
    raise SuiteError([Violation(source="suite.yaml", field="x", message=f"bad value {SECRET}")])


handled_app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)
handled_app.callback()(app_module._root)
for command in (
    two_violations,
    no_violations,
    whole_document,
    with_argument,
    execution,
    boom,
    silent,
    passthrough,
    fine,
    leaks_in_execution_error,
    leaks_in_internal_error,
    leaks_in_violation,
):
    handled_app.command(command.__name__.replace("_", "-"))(app_module._handled(command))


def test_two_violations_print_two_lines_and_exit_2_without_a_traceback() -> None:
    result = runner.invoke(handled_app, ["two-violations"])
    assert result.exit_code == 2
    assert result.stderr.splitlines() == [
        "SuiteError: duplicate id 'a' (suite.yaml:scenarios.0.id)",
        "SuiteError: unsupported version 2 (suite.yaml:version)",
    ]
    assert result.stdout == ""
    assert "Traceback" not in result.output


def test_an_input_error_with_no_violations_still_prints_one_line_and_exits_2() -> None:
    """errors.py allows an empty list (message "invalid input"); silence would hide it."""
    result = runner.invoke(handled_app, ["no-violations"])
    assert result.exit_code == 2
    assert result.stderr.splitlines() == ["InputError: invalid input"]
    assert "Traceback" not in result.output


def test_verbose_adds_nothing_for_an_input_error() -> None:
    result = runner.invoke(handled_app, ["--verbose", "two-violations"])
    assert result.exit_code == 2
    assert len(result.stderr.splitlines()) == 2
    assert "Traceback" not in result.output
    result = runner.invoke(handled_app, ["--verbose", "no-violations"])
    assert result.stderr.splitlines() == ["InputError: invalid input"]


def test_a_whole_document_violation_names_the_source_alone() -> None:
    result = runner.invoke(handled_app, ["whole-document"])
    assert result.exit_code == 2
    assert result.stderr.splitlines() == ["PathError: file not found (missing.yaml)"]


def test_the_wrapper_keeps_the_command_signature() -> None:
    """Typer reads parameters from the wrapper's signature; the argument reaches the command."""
    result = runner.invoke(handled_app, ["with-argument", "other.yaml"])
    assert result.exit_code == 2
    assert result.stderr.splitlines() == ["SuiteError: bad id (other.yaml:id)"]
    assert runner.invoke(handled_app, ["with-argument"]).exit_code == 2  # click: missing argument


def test_an_execution_error_prints_one_line_and_exits_3() -> None:
    result = runner.invoke(handled_app, ["execution"])
    assert result.exit_code == 3
    assert result.stderr.splitlines() == ["TraceMissingError: no trace for reject-over-limit"]
    assert result.stdout == ""


def test_verbose_appends_the_traceback_to_an_execution_error() -> None:
    result = runner.invoke(handled_app, ["--verbose", "execution"])
    assert result.exit_code == 3
    lines = result.stderr.splitlines()
    assert lines[0] == "TraceMissingError: no trace for reject-over-limit"
    assert lines[1] == "Traceback (most recent call last):"
    assert lines[-1] == "agentproof.errors.TraceMissingError: no trace for reject-over-limit"


def test_an_unexpected_exception_prints_one_line_and_exits_4() -> None:
    result = runner.invoke(handled_app, ["boom"])
    assert result.exit_code == 4
    assert result.stderr.splitlines() == [
        "internal error: RuntimeError: boom (re-run with --verbose for the traceback)"
    ]
    assert result.stdout == ""
    assert "Traceback" not in result.output


def test_verbose_appends_the_traceback_to_an_unexpected_exception() -> None:
    result = runner.invoke(handled_app, ["--verbose", "boom"])
    assert result.exit_code == 4
    lines = result.stderr.splitlines()
    assert lines[0] == "internal error: RuntimeError: boom"
    assert lines[1] == "Traceback (most recent call last):"
    assert lines[-1] == "RuntimeError: boom"


def test_an_exception_without_a_message_prints_its_type_alone() -> None:
    result = runner.invoke(handled_app, ["silent"])
    assert result.exit_code == 4
    assert result.stderr.splitlines() == [
        "internal error: RuntimeError (re-run with --verbose for the traceback)"
    ]


def test_a_typer_exit_raised_inside_a_command_passes_through_unchanged() -> None:
    result = runner.invoke(handled_app, ["passthrough"])
    assert result.exit_code == 7
    assert result.output == ""


def test_a_command_that_returns_exits_0() -> None:
    result = runner.invoke(handled_app, ["fine"])
    assert result.exit_code == 0
    assert result.stdout == "ok\n"
    assert result.stderr == ""


def test_no_color_output_carries_no_escape_sequence() -> None:
    for argv in (["--no-color", "two-violations"], ["--no-color", "--verbose", "boom"]):
        result = runner.invoke(handled_app, argv)
        assert "\x1b" not in result.output, argv


def test_options_live_on_the_context_and_never_leak_between_invocations() -> None:
    """``--verbose`` on one command line must not carry into the next, in one process."""
    assert not hasattr(app_module, "_options")
    assert "Traceback" in runner.invoke(handled_app, ["--verbose", "boom"]).stderr
    assert "Traceback" not in runner.invoke(handled_app, ["boom"]).stderr
    assert "Traceback" in runner.invoke(handled_app, ["--verbose", "boom"]).stderr
    assert "Traceback" not in runner.invoke(handled_app, ["boom"]).stderr


# Story 3.5 installs scrub_text on every print (io.console). Until then the handler prints
# the exception's own text, the traceback, and violation messages as they are; these strict
# xfails pin that gap so the day 3.5 closes it they fail and must be flipped to plain tests.
SCRUB_GAP = "story 3.5: io.console scrub_text is not installed on the CLI's output yet"


@pytest.mark.xfail(strict=True, reason=SCRUB_GAP)
@pytest.mark.parametrize(
    "argv",
    [
        ["leaks-in-execution-error"],
        ["--verbose", "leaks-in-execution-error"],
        ["leaks-in-internal-error"],
        ["--verbose", "leaks-in-internal-error"],
        ["leaks-in-violation"],
    ],
)
def test_a_planted_secret_never_reaches_the_output(argv: list[str]) -> None:
    result = runner.invoke(handled_app, argv)
    assert SECRET not in result.output
