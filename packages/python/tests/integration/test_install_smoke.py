"""Build the wheel, install it into a fresh venv, and drive ``agentproof`` as a subprocess.

This is the install path the README will promise: ``uv build`` produces the wheel,
``uv venv`` creates an empty environment, and ``uv pip install <wheel path>`` installs
it. Nothing here installs the package by name from an index.
"""

import os
import re
import shutil
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from collections.abc import Sequence
from pathlib import Path

import pytest

from testsupport import PACKAGE_ROOT, run_captured

SUBPROCESS_TIMEOUT_SECONDS = 600


def _uv() -> str:
    """Locate uv: ``uv run`` exports ``UV``; otherwise fall back to PATH."""
    found = os.environ.get("UV") or shutil.which("uv")
    if not found:
        pytest.fail("uv is required to build and install the wheel but was not found")
    return found


def _run(
    argv: Sequence[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "NO_COLOR": "1",
        "TERM": "dumb",
        # Wide enough that no command description wraps; a wrapped continuation
        # line would otherwise be read as a command by _commands_listed_in_help.
        "COLUMNS": "400",
        "PYTHONIOENCODING": "utf-8",
    }
    return run_captured(argv, cwd=cwd, env=env, timeout=SUBPROCESS_TIMEOUT_SECONDS, check=check)


def _pyproject_version() -> str:
    with (PACKAGE_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


_ANSI = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def _strip_ansi(text: str) -> str:
    """Remove ANSI escapes: CI sets GITHUB_ACTIONS, which makes Rich style even piped output."""
    return _ANSI.sub("", text)


# Characters Rich and click use to draw help panels: rounded, square, or ASCII borders.
_BORDER_CHARS = frozenset("─│╭╮╯╰┌┐└┘├┤+-| ")


def _is_panel_border(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and set(stripped) <= _BORDER_CHARS


def _commands_listed_in_help(help_text: str) -> list[str]:
    """Return the command names under the ``Commands`` section of ``--help`` output.

    Tolerates Typer's Rich panel in any border style (rounded, square, ASCII) and
    click's plain ``Commands:`` layout, where the section ends at a blank line.
    """
    lines = help_text.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if "Commands" in line)
    except StopIteration:
        pytest.fail(f"no Commands section in --help output:\n{help_text}")
    names: list[str] = []
    name_indent: int | None = None
    for line in lines[start + 1 :]:
        if _is_panel_border(line):
            break
        stripped = line.strip()
        # Drop the panel's side border but keep the indent inside it; click's plain
        # layout has no border, so its own indent is kept.
        inner = stripped.strip("│|") if stripped[:1] in ("│", "|") else line.rstrip()
        body = inner.strip()
        if not body:
            if names:
                break
            continue
        indent = len(inner) - len(inner.lstrip())
        if name_indent is None:
            name_indent = indent
        if indent > name_indent:
            continue  # a wrapped description continues under the description column
        names.append(body.split()[0])
    return names


def test_commands_listed_skips_wrapped_description_lines() -> None:
    """A description that wraps onto a second line must not add a bogus command name."""
    rich_panel = (
        "╭─ Commands ───────────────────────────────╮\n"
        "│ version   Print the version and the      │\n"
        "│           supported Report schema.       │\n"
        "│ other     Does something.                │\n"
        "╰──────────────────────────────────────────╯\n"
    )
    assert _commands_listed_in_help(rich_panel) == ["version", "other"]
    plain = "Commands:\n  version  Print the version and the\n           supported Report schema.\n"
    assert _commands_listed_in_help(plain) == ["version"]


@pytest.fixture(scope="module")
def installed_cli(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the wheel, install it into a fresh venv, and return the console script path."""
    uv = _uv()
    workdir = tmp_path_factory.mktemp("install-smoke")
    dist_dir = workdir / "dist"
    _run([uv, "build", "--wheel", "--out-dir", str(dist_dir)], cwd=PACKAGE_ROOT)
    wheels = sorted(dist_dir.glob("agentproof-*.whl"))
    assert len(wheels) == 1, f"expected exactly one wheel, found {wheels}"
    wheel = wheels[0]
    assert wheel.name == f"agentproof-{_pyproject_version()}-py3-none-any.whl"

    venv_dir = workdir / "venv"
    _run([uv, "venv", "--python", sys.executable, str(venv_dir)])
    if sys.platform == "win32":
        scripts_dir = venv_dir / "Scripts"
        python = scripts_dir / "python.exe"
        script = scripts_dir / "agentproof.exe"
    else:
        scripts_dir = venv_dir / "bin"
        python = scripts_dir / "python"
        script = scripts_dir / "agentproof"
    _run([uv, "pip", "install", "--python", str(python), str(wheel)])
    assert script.is_file(), f"console script missing after install: {script}"
    return script


def test_wheel_contains_only_the_agentproof_package(installed_cli: Path) -> None:
    """Criterion 4: the shipped wheel never carries the devtools workspace member."""
    wheel = next(installed_cli.parents[1].parent.glob("dist/agentproof-*.whl"))
    members = zipfile.ZipFile(wheel).namelist()
    allowed = ("agentproof/", f"agentproof-{_pyproject_version()}.dist-info/")
    assert all(member.startswith(allowed) for member in members), members
    assert not any("agentproof_devtools" in member for member in members), members


def test_sdist_carries_the_project_but_not_devtools_or_tests(tmp_path: Path) -> None:
    """Story 1.7: the source archive, a release asset since story 1.6, ships neither the
    devtools workspace member nor the test suite (``[tool.hatch.build.targets.sdist]``)."""
    dist_dir = tmp_path / "dist"
    _run([_uv(), "build", "--sdist", "--out-dir", str(dist_dir)], cwd=PACKAGE_ROOT)
    archives = sorted(dist_dir.glob("agentproof-*.tar.gz"))
    assert len(archives) == 1, f"expected exactly one sdist, found {archives}"
    assert archives[0].name == f"agentproof-{_pyproject_version()}.tar.gz"
    with tarfile.open(archives[0]) as archive:
        members = archive.getnames()
    root = f"agentproof-{_pyproject_version()}"
    assert all(member == root or member.startswith(f"{root}/") for member in members), members
    inside = {member.removeprefix(f"{root}/") for member in members}
    assert {"pyproject.toml", "PKG-INFO", "src/agentproof/__init__.py"} <= inside, sorted(inside)
    excluded = [m for m in inside if m == "devtools" or m.startswith(("devtools/", "tests/"))]
    assert excluded == [] and "tests" not in inside, excluded


def test_version_prints_pyproject_version_and_schema_versions_and_exits_zero(
    installed_cli: Path,
) -> None:
    """Story 3.1 criterion 4 (PRD AC-30.2) against the installed wheel, not the source tree."""
    result = _run([str(installed_cli), "version"], check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        f"agentproof {_pyproject_version()}",
        "suite schema versions: 1",
        "trace schema versions: 1",
        "report schema versions: 1",
    ]
    assert result.stderr == ""


def test_help_lists_only_version_and_the_global_options(installed_cli: Path) -> None:
    result = _run([str(installed_cli), "--help"], check=False)
    assert result.returncode == 0, result.stderr
    help_text = _strip_ansi(result.stdout)
    assert _commands_listed_in_help(help_text) == ["version"]
    assert "--verbose" in help_text
    assert "--no-color" in help_text


def test_unknown_command_exits_nonzero(installed_cli: Path) -> None:
    result = _run([str(installed_cli), "validate", "x.yaml"], check=False)
    assert result.returncode != 0
