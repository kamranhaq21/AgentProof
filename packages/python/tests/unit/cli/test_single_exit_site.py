"""``cli/app.py`` is the only module that exits (architecture AD-6; story 3.1 criterion 1).

Every ``.py`` file under ``src/agentproof`` is parsed with ``ast`` (never imported) and
searched for the ways a module can end the process: a call or raise naming ``Exit``
(``typer.Exit``, ``click.exceptions.Exit``, a bare ``Exit`` from ``from typer import
Exit``), ``_exit`` (``os._exit``), ``exit`` (``sys.exit``, ``ctx.exit``, the builtin), or
``SystemExit``; names imported under an alias (``from typer import Exit as Leave``) are
followed. Docstrings and comments cannot trip it or satisfy it. Only ``cli/app.py`` may
contain a finding.
"""

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = PACKAGE_ROOT / "src" / "agentproof"
THE_ONE_EXIT_SITE = SOURCE_ROOT / "cli" / "app.py"

EXIT_NAMES = frozenset({"Exit", "_exit", "exit", "quit", "SystemExit"})


def _last_name(node: ast.expr) -> str | None:
    """The final identifier of ``typer.Exit``, ``os._exit``, or ``Exit``."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def exit_sites(source: str) -> list[tuple[int, str]]:
    """``(line, name)`` of every call or raise that names an exit, aliases followed."""
    tree = ast.parse(source)
    names = set(EXIT_NAMES)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom | ast.Import):
            for alias in node.names:
                if alias.name.rsplit(".", 1)[-1] in EXIT_NAMES and alias.asname:
                    names.add(alias.asname)
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc is not None:
            target = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
        elif isinstance(node, ast.Call):
            target = node.func
        else:
            continue
        name = _last_name(target)
        if name in names:
            found.append((node.lineno, name))
    return sorted(found)


def _source_files() -> list[Path]:
    files = sorted(SOURCE_ROOT.rglob("*.py"))
    assert files, f"no Python files under {SOURCE_ROOT}"
    return files


def test_only_cli_app_contains_an_exit_site() -> None:
    offenders = {
        str(path.relative_to(SOURCE_ROOT)): exit_sites(path.read_text(encoding="utf-8"))
        for path in _source_files()
        if path != THE_ONE_EXIT_SITE and exit_sites(path.read_text(encoding="utf-8"))
    }
    assert offenders == {}, f"exit sites outside cli/app.py: {offenders}"


def test_cli_app_raises_typer_exit_in_code_and_never_calls_sys_exit() -> None:
    """By AST, so the module docstring (which names ``Exit``) cannot satisfy the check."""
    tree = ast.parse(THE_ONE_EXIT_SITE.read_text(encoding="utf-8"))
    raised = [
        ast.unparse(node.exc.func if isinstance(node.exc, ast.Call) else node.exc)
        for node in ast.walk(tree)
        if isinstance(node, ast.Raise) and node.exc is not None
    ]
    assert "typer.Exit" in raised
    called = {ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    assert not {"sys.exit", "exit", "quit", "os._exit"} & called
    assert not any(
        isinstance(node, ast.Raise) and "SystemExit" in ast.unparse(node) for node in ast.walk(tree)
    )


def test_the_scan_catches_each_way_of_exiting() -> None:
    for snippet in (
        "import typer\nraise typer.Exit(2)",
        "import typer\nraise typer.Exit",
        "import sys\nsys.exit(4)",
        "import os\nos._exit(1)",
        "raise SystemExit(1)",
        "exit(0)",
        "from typer import Exit\nraise Exit(2)",
        "from typer import Exit as Leave\nraise Leave(2)",
        "import click\nraise click.exceptions.Exit(2)",
        "def f(ctx):\n    ctx.exit(1)",
        "import sys as s\ns.exit(1)",
    ):
        assert exit_sites(snippet), snippet


def test_the_scan_ignores_docstrings_and_lookalike_names() -> None:
    for snippet in (
        '"""Raises typer.Exit and calls sys.exit and os._exit."""',
        "from agentproof.cli import exit_codes\nexit_codes.from_outcome(o)",
        "EXIT_INPUT_ERROR = 2\nself.exit_code",
    ):
        assert exit_sites(snippet) == [], snippet
