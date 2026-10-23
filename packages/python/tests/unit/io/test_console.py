"""``io.console``: the scrubbing print path and the logging filter (story 3.5 criteria 2
and 3; AD-10; Conventions, Logging; PRD AC-28.2)."""

import logging
from collections.abc import Iterator
from typing import Any

import pytest
from rich.table import Table
from rich.text import Text

from agentproof.constants import REDACTED
from agentproof.io import console
from agentproof.loading import yaml_safe
from agentproof.models import canonical

SECRET = "sk-live-planted-secret-value"


@pytest.fixture(autouse=True)
def _clean_console() -> Iterator[None]:
    console.uninstall()
    yield
    console.uninstall()


def printed(capsys: pytest.CaptureFixture[str], renderable: Any, **kwargs: Any) -> str:
    console.echo(renderable, **kwargs)
    captured = capsys.readouterr()
    return captured.out + captured.err


def test_a_plain_line_is_scrubbed(capsys: pytest.CaptureFixture[str]) -> None:
    console.set_secret_values([SECRET])
    out = printed(capsys, f"token={SECRET}", no_color=True)
    assert out == f"token={REDACTED}\n"


def test_stderr_is_scrubbed_too(capsys: pytest.CaptureFixture[str]) -> None:
    console.set_secret_values([SECRET])
    console.echo(f"bad {SECRET}", err=True, no_color=True)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"bad {REDACTED}\n"


def test_a_table_cell_is_scrubbed(capsys: pytest.CaptureFixture[str]) -> None:
    console.set_secret_values([SECRET])
    table = Table("name", "value")
    table.add_row("api", SECRET)
    out = printed(capsys, table, no_color=True)
    assert SECRET not in out
    assert REDACTED in out


def test_a_secret_split_across_styled_spans_is_still_scrubbed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The probe for the risk note: markup splits the value into two escape-delimited runs
    when color is on, so scrubbing the rendered ANSI (or the markup source) would miss it."""
    console.set_secret_values([SECRET])
    markup = "token [bold]sk-live-[/bold][red]planted-secret-value[/red] end"
    # The naive approaches really do miss it:
    assert SECRET not in markup
    from agentproof.redaction import scrub_text

    assert scrub_text(markup, [SECRET]) == markup  # source scrub misses
    for color in (False, True):
        rendered = console.render(markup, no_color=not color, markup=True, color=color)
        assert SECRET not in rendered
        assert REDACTED in rendered
        assert rendered.startswith("token ")
    # Even the colored rendering leaks nothing: a hit falls back to scrubbed plain text.
    assert "\x1b" not in console.render(markup, no_color=False, markup=True, color=True)


def test_a_secret_inside_markup_tags_attributes_and_text(
    capsys: pytest.CaptureFixture[str],
) -> None:
    console.set_secret_values([SECRET])
    out = printed(capsys, f"[link=https://x/{SECRET}]{SECRET}[/link]", no_color=True, markup=True)
    assert SECRET not in out


def test_a_secret_only_in_link_metadata_is_scrubbed_from_styled_output() -> None:
    """``[link=...]`` puts the target in an OSC-8 escape that the plain text never shows."""
    console.set_secret_values([SECRET])
    markup = f"[link=https://example.test/?t={SECRET}]docs[/link]"
    # Without a secret set, the styled path really does carry the target:
    console.set_secret_values(())
    assert SECRET in console.render(markup, no_color=False, markup=True, color=True)
    console.set_secret_values([SECRET])
    rendered = console.render(markup, no_color=False, markup=True, color=True)
    assert SECRET not in rendered
    assert "docs" in rendered
    assert "\x1b" not in rendered  # fell back to the unstyled rendering


def test_a_secret_that_wrapping_would_break_is_still_scrubbed() -> None:
    padding = "word " * 15  # pushes the value across the 80-column wrap point
    text = Text(padding + SECRET + " tail")  # a Text wraps at the console width, a str does not
    wrapped = console.render(text, no_color=True, markup=False)
    assert "\n" in wrapped.rstrip("\n")  # without a secret it really does wrap
    console.set_secret_values([SECRET])
    rendered = console.render(text, no_color=True, markup=False)
    assert SECRET not in rendered
    assert REDACTED in rendered
    assert "sk-live-" not in rendered


def test_plain_text_prints_literally_without_markup(
    capsys: pytest.CaptureFixture[str],
) -> None:
    out = printed(capsys, "list [bold] stays [/bold]", no_color=True)
    assert out == "list [bold] stays [/bold]\n"


def test_no_color_output_has_no_escape_sequences(capsys: pytest.CaptureFixture[str]) -> None:
    out = printed(capsys, "[bold red]loud[/bold red]", no_color=True, markup=True)
    assert "\x1b" not in out
    assert out == "loud\n"


def test_values_reset_between_installs() -> None:
    console.install([SECRET])
    assert console.scrub(SECRET) == REDACTED
    console.install(())
    assert console.secret_values() == ()
    assert console.scrub(SECRET) == SECRET


# --- logging filter -------------------------------------------------------------------


class Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.formatter = logging.Formatter("%(levelname)s %(message)s")
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(self.format(record))


@pytest.fixture
def root_capture() -> Iterator[Capture]:
    root = logging.getLogger()
    previous = root.level
    handler = Capture()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)
    yield handler
    root.removeHandler(handler)
    root.setLevel(previous)


def test_install_filters_a_record_emitted_through_an_existing_handler(
    root_capture: Capture,
) -> None:
    console.install([SECRET])
    logging.getLogger("agentproof.shell").warning("calling with %s", SECRET)
    assert root_capture.lines == [f"WARNING calling with {REDACTED}"]


def test_the_filter_scrubs_message_exception_and_args(root_capture: Capture) -> None:
    console.install([SECRET])
    log = logging.getLogger("agentproof.shell")
    try:
        raise RuntimeError(f"boom {SECRET}")
    except RuntimeError:
        log.error("failed: %s", {"token": SECRET}, exc_info=True)
    (line,) = root_capture.lines
    assert SECRET not in line
    assert REDACTED in line
    assert "Traceback" in line


def test_the_handler_install_owns_writes_scrubbed_lines_to_stderr(
    capsys: pytest.CaptureFixture[str],
) -> None:
    console.install([SECRET], verbose=True)
    logging.getLogger("agentproof.shell").debug("detail %s", SECRET)
    captured = capsys.readouterr()
    assert captured.err == f"DEBUG: detail {REDACTED}\n"
    assert captured.out == ""
    logging.getLogger().setLevel(logging.WARNING)


def test_install_twice_leaves_one_owned_handler() -> None:
    root = logging.getLogger()
    before = len(root.handlers)
    console.install([SECRET])
    console.install([SECRET])
    assert len(root.handlers) == before + 1
    console.uninstall()
    assert len(root.handlers) == before


def test_the_filter_class_is_a_logging_filter() -> None:
    assert issubclass(console.ScrubFilter, logging.Filter)


def test_the_core_emits_no_log_records(root_capture: Capture) -> None:
    """Sampled evidence only: with a handler on the root logger at DEBUG, ``canonical.dumps``
    and ``yaml_safe.load`` (success and error paths) produce zero records. The general
    guarantee is the static test below: no core module imports ``logging``."""
    records: list[logging.LogRecord] = []

    class Recorder(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            records.append(record)
            return True

    root_capture.addFilter(Recorder())
    canonical.dumps({"b": [1, 2], "a": {"k": "v"}})
    yaml_safe.load("a: 1\nb: [1, 2]\n", source="x.yaml")
    with pytest.raises(Exception):  # noqa: B017, PT011 - any InputError: the error path too
        yaml_safe.load("a: &x 1\nb: *x\n", source="x.yaml")
    assert records == []
    assert root_capture.lines == []


def test_no_core_module_imports_logging() -> None:
    """The stronger form of "core never logs" (Conventions, Logging): no module in a core
    package, or the package top level, imports ``logging`` at all."""
    import ast
    from pathlib import Path

    from agentproof_devtools.purity import CORE_PACKAGES

    root = Path(console.__file__).resolve().parents[1]  # src/agentproof
    files = [root / "__init__.py"]
    for name in CORE_PACKAGES:
        single = root / f"{name}.py"
        files += [single] if single.exists() else sorted((root / name).rglob("*.py"))
    assert len(files) > 10
    offenders: list[str] = []
    for path in files:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            if any(n == "logging" or n.startswith("logging.") for n in names):
                offenders.append(str(path.relative_to(root)))
    assert offenders == []
