"""Typer application behind the ``agentproof`` console script (architecture AD-6, AD-7, AD-20).

This is the only module in the package that exits: every ``Exit`` is raised here and an
AST test over the source tree keeps it that way. Each command is a plain function in
``cli/commands/`` wrapped by ``_handled`` before it is registered, so one handler maps the
error taxonomy to the exit codes for every command:

* ``InputError`` (the user's input is wrong): one line per ``Violation`` on stderr in the
  shape ``<kind>: <message> (<source>:<field>)`` (one line, ``<kind>: invalid input``,
  when the list is empty), exit 2, never a traceback;
* ``ExecutionError`` (the run could not produce or persist evidence): one line, exit 3;
* anything else (a bug): one line, exit 4;

with the traceback appended for exit 3 and 4 only when ``--verbose`` is set (PRD
AC-28.1; the Error-shape convention). A command that runs to completion exits 0; the
commands that evaluate something will exit with ``cli.exit_codes`` (AD-6) in later
stories. The numbers come from ``cli.exit_codes`` and appear nowhere else.

The two global options of AD-20, ``--verbose`` and ``--no-color``, belong to the root
command, so they must precede the command name: ``agentproof --verbose version`` works
and ``agentproof version --verbose`` is a usage error (exit 2), as in any Typer or Click
group. The root callback stores them as a ``GlobalOptions`` on ``ctx.obj``; the handler
reads them from the context, so no state outlives one invocation.

Every line the handler prints goes through ``io.console``, which replaces the declared
secret values (story 3.5); the root callback installs the console scrubber and the
logging filter.
"""

import functools
import inspect
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, cast

import typer

from agentproof.cli.commands.version import version
from agentproof.cli.exit_codes import (
    EXIT_EXECUTION_ERROR,
    EXIT_INPUT_ERROR,
    EXIT_INTERNAL_ERROR,
)
from agentproof.errors import ExecutionError, InputError, Violation
from agentproof.io import console

__all__ = ["GlobalOptions", "app", "main"]

VERBOSE_HINT = "(re-run with --verbose for the traceback)"

_CONTEXT_PARAMETER = "agentproof_context"
"""The keyword-only parameter ``_handled`` adds so Typer injects the click context."""


@dataclass(frozen=True)
class GlobalOptions:
    """The AD-20 global options as the root callback read them; held on ``ctx.obj``."""

    verbose: bool = False
    """Append the traceback to the one-line message for exit 3 and 4."""

    no_color: bool = False
    """Write no escape sequences, whatever the terminal supports."""


def _echo_error(text: str, options: GlobalOptions) -> None:
    """Write ``text`` and a newline to stderr, scrubbed of secrets (plain under ``--no-color``)."""
    console.echo(text, err=True, no_color=options.no_color)


def _violation_line(kind: str, violation: Violation) -> str:
    """``<kind>: <message> (<source>:<field>)``; ``(<source>)`` when the field is empty."""
    where = f"{violation.source}:{violation.field}" if violation.field else violation.source
    return f"{kind}: {violation.message} ({where})"


def _one_line(exc: BaseException) -> str:
    """``<ExceptionType>: <message>``, or the type alone when the message is empty."""
    kind = type(exc).__name__
    message = str(exc)
    return f"{kind}: {message}" if message else kind


def _echo_traceback_if_verbose(exc: BaseException, options: GlobalOptions) -> None:
    if options.verbose:
        _echo_error("".join(traceback.format_exception(exc)).rstrip("\n"), options)


def _handled(command: Callable[..., None]) -> Callable[..., None]:
    """Wrap a command so every escaped exception becomes a message and an exit code.

    The wrapper's signature is the command's plus one keyword-only ``typer.Context``
    parameter, which Typer injects by annotation; the wrapper reads the global options
    from it and does not pass it on.
    """
    signature = inspect.signature(command)

    @functools.wraps(command)
    def run(*args: object, **kwargs: object) -> None:
        # Typer injects the click base Context (typer.Context subclasses it), which has
        # the same ``find_object``; the cast is for the type checker only.
        context = cast(typer.Context, kwargs.pop(_CONTEXT_PARAMETER))
        options = context.find_object(GlobalOptions) or GlobalOptions()
        try:
            command(*args, **kwargs)
        except (typer.Exit, typer.Abort):
            raise
        except typer.TyperException:
            # Typer vendors click internally (0.27 declares no dependency on the real
            # click package) and exposes its usage-error hierarchy as the public,
            # stable ``typer.exceptions.TyperException`` (``typer.Exit``/``typer.Abort``
            # are not part of it, handled above). A callback's BadParameter and similar
            # keep their own rendering and exit code; they are not an internal error.
            raise
        except InputError as exc:
            kind = type(exc).__name__
            if exc.violations:
                for violation in exc.violations:
                    _echo_error(_violation_line(kind, violation), options)
            else:
                # errors.py allows an empty list; the user still gets one line.
                _echo_error(_one_line(exc), options)
            raise typer.Exit(EXIT_INPUT_ERROR) from None
        except ExecutionError as exc:
            _echo_error(_one_line(exc), options)
            _echo_traceback_if_verbose(exc, options)
            raise typer.Exit(EXIT_EXECUTION_ERROR) from None
        except Exception as exc:
            line = f"internal error: {_one_line(exc)}"
            if not options.verbose:
                line = f"{line} {VERBOSE_HINT}"
            _echo_error(line, options)
            _echo_traceback_if_verbose(exc, options)
            raise typer.Exit(EXIT_INTERNAL_ERROR) from None

    context_parameter = inspect.Parameter(
        _CONTEXT_PARAMETER, inspect.Parameter.KEYWORD_ONLY, annotation=typer.Context
    )
    run.__signature__ = signature.replace(  # type: ignore[attr-defined]
        parameters=[*signature.parameters.values(), context_parameter]
    )
    run.__annotations__ = {
        **getattr(command, "__annotations__", {}),
        _CONTEXT_PARAMETER: typer.Context,
    }
    return run


app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    # The handler above decides what an escaped exception prints; Typer's Rich traceback
    # rendering would otherwise take over for anything that still got past it.
    pretty_exceptions_enable=False,
)


@app.callback()
def _root(
    context: typer.Context,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            help="Append the traceback to execution (exit 3) and internal (exit 4) errors.",
        ),
    ] = False,
    no_color: Annotated[
        bool,
        typer.Option("--no-color", help="Write plain text with no color or styling."),
    ] = False,
) -> None:
    """Test and regression-check tool-using AI agents from saved traces.

    Put --verbose and --no-color before the command. Exit codes: 0 success; 1 an
    assertion failed or errored, or nothing was evaluated; 2 invalid input or usage;
    3 execution error; 4 internal error.
    """
    # Also keeps ``app`` a command group: without a callback Typer collapses a
    # single-command app into that command.
    context.obj = GlobalOptions(verbose=verbose, no_color=no_color)
    # Installs the scrubber and logging filter before any command reads a Trace. The secret
    # set is EMPTY here, so in the shipped CLI scrubbing is a no-op until epic 5's runner
    # calls ``console.set_secret_values``; only the wiring is live today.
    console.install((), verbose=verbose)


app.command("version")(_handled(version))


def main() -> None:
    """Console-script entry point declared in ``pyproject.toml``."""
    app()
