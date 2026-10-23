"""Console output and logging that never carry a declared secret (AD-10, AD-20; PRD AC-28.2).

The shell prints through this module and logs through ``logging`` with the filter that
``install`` attaches; the core prints and logs nothing. Both paths call the one
``redaction.scrub_text`` with the current secret values.

Secret values come from ``set_secret_values``. v0.1 has no secret source before the
runner exists (epic 5 resolves ``redact.env`` names), so the CLI root callback installs
an empty set and the runner will call ``set_secret_values`` once it has resolved the
values, before it reads any Trace. The state is module-level on purpose (a logging filter
and the error handler both need it without a context) and ``install`` resets it, so one
invocation's values never reach the next.

Rich markup can split a secret across styled spans (``[b]sk-[/b]live`` renders as two
escape-delimited runs), so scrubbing the markup source or the ANSI output would miss it.
``render`` therefore renders the renderable to plain text first, scrubs that final text,
and only emits the styled rendering when the plain text held no secret; when it did, the
scrubbed plain text is emitted instead (styling is lost for that one print, never the
redaction). The plain check uses a very wide, unwrapped rendering, so a secret that
word-wrap or a table border would break across lines is still found.
"""

import io
import logging
import sys
import traceback
from collections.abc import Iterable

import typer
from rich.console import Console, RenderableType

from agentproof.redaction import scrub_text

__all__ = [
    "ScrubFilter",
    "echo",
    "install",
    "render",
    "scrub",
    "secret_values",
    "set_secret_values",
    "uninstall",
]

_WIDE = 100_000
"""Width of the unwrapped rendering the secret check runs on."""

_DEFAULT_WIDTH = 80

_secrets: tuple[str, ...] = ()
_handler: logging.Handler | None = None
_filter: "ScrubFilter | None" = None
_hooked: list[logging.Handler] = []


def set_secret_values(values: Iterable[str]) -> None:
    """Replace the secret values every later print and log record is scrubbed of."""
    global _secrets
    _secrets = tuple(value for value in values if value)


def secret_values() -> tuple[str, ...]:
    """The secret values currently in force (a copy; tuples are immutable)."""
    return _secrets


def scrub(text: str) -> str:
    """``scrub_text`` with the current secret values."""
    return scrub_text(text, _secrets)


def _console(*, width: int, color: bool) -> Console:
    return Console(
        file=io.StringIO(),
        record=True,
        width=width,
        force_terminal=color,
        color_system="standard" if color else None,
        no_color=not color,
        legacy_windows=False,
    )


def render(
    renderable: RenderableType,
    *,
    no_color: bool,
    markup: bool = True,
    color: bool = False,
) -> str:
    """Render to the final text to write, with every secret value replaced.

    ``color`` says whether the destination takes escape sequences; it is ignored under
    ``no_color``. Plain strings with ``markup=False`` print literally (error lines).
    """
    use_color = color and not no_color

    def draw(width: int, styled: bool) -> str:
        console = _console(width=width, color=styled)
        # A plain string is a log or error line: never re-wrapped, so greps and CI logs
        # see one line per message. Tables and panels wrap to the console width.
        console.print(
            renderable, markup=markup, highlight=False, soft_wrap=isinstance(renderable, str)
        )
        return console.export_text(styles=styled)

    plain = draw(_WIDE, styled=False)
    scrubbed = scrub(plain)
    if scrubbed != plain:
        return scrubbed
    if not use_color:
        return draw(_DEFAULT_WIDTH, styled=False)
    # The styled path carries data the plain text does not (OSC-8 hyperlink targets from
    # ``[link=...]``), so a value that appears only there would pass the plain check. Scrub
    # the styled string too, and on any hit fall back to the unstyled rendering, which the
    # plain check above already cleared.
    styled = draw(_DEFAULT_WIDTH, styled=True)
    if scrub(styled) != styled:
        return draw(_DEFAULT_WIDTH, styled=False)
    return styled


def echo(
    renderable: RenderableType,
    *,
    err: bool = False,
    no_color: bool = False,
    markup: bool = False,
) -> None:
    """Print through the scrubber to stdout, or to stderr when ``err``."""
    stream = sys.stderr if err else sys.stdout
    text = render(renderable, no_color=no_color, markup=markup, color=stream.isatty())
    typer.echo(text, err=err, nl=False, color=False if no_color else None)


class ScrubFilter(logging.Filter):
    """Replace secret values in a record's message, traceback, and stack with the marker.

    Pure: it reads and rewrites the record only. It formats the message once (``msg`` with
    ``args``) and clears ``args``, so what every handler's formatter sees is scrubbed.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = scrub(record.getMessage())
        record.args = None
        if record.exc_info and not record.exc_text:
            record.exc_text = "".join(traceback.format_exception(*record.exc_info)).rstrip("\n")
        if record.exc_text:
            record.exc_text = scrub(record.exc_text)
        if record.stack_info:
            record.stack_info = scrub(record.stack_info)
        return True


def install(secret_values: Iterable[str] = (), *, verbose: bool = False) -> None:
    """Make scrubbing live: set the secret values and filter the root logger's handlers.

    Idempotent: a second call replaces the first's state. The filter is attached to every
    handler already on the root logger and to a stderr handler this function owns (a
    filter on a logger does not apply to records from its children, a filter on a
    handler applies to everything the handler emits). ``verbose`` lowers the root level
    to DEBUG; otherwise the level is left alone.
    """
    global _handler, _filter
    uninstall()
    set_secret_values(secret_values)
    root = logging.getLogger()
    _filter = ScrubFilter()
    for existing in root.handlers:
        existing.addFilter(_filter)
        _hooked.append(existing)
    _handler = logging.StreamHandler(sys.stderr)
    _handler.addFilter(_filter)
    _handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    root.addHandler(_handler)
    if verbose:
        root.setLevel(logging.DEBUG)


def uninstall() -> None:
    """Remove what ``install`` attached and clear the secret values (for tests and reuse)."""
    global _handler, _filter
    root = logging.getLogger()
    if _handler is not None:
        root.removeHandler(_handler)
        _handler = None
    if _filter is not None:
        for hooked in _hooked:
            hooked.removeFilter(_filter)
        _filter = None
    _hooked.clear()
    set_secret_values(())
