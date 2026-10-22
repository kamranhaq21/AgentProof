"""Build the wheel, install it into a fresh venv, and drive ``agentproof`` as a subprocess.

This is the install path the README will promise: ``uv build`` produces the wheel,
``uv venv`` creates an empty environment, and ``uv pip install <wheel path>`` installs
it. Nothing here installs the package by name from an index.
"""

import os
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Sequence
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
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
    return subprocess.run(
        list(argv),
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
        check=check,
    )


def _pyproject_version() -> str:
    with (PACKAGE_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


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
    for line in lines[start + 1 :]:
        if _is_panel_border(line):
            break
        body = line.strip().strip("│|").strip()
        if not body:
            if names:
                break
            continue
        names.append(body.split()[0])
    return names


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


def test_version_prints_pyproject_version_and_exits_zero(installed_cli: Path) -> None:
    result = _run([str(installed_cli), "version"], check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [_pyproject_version()]


def test_help_lists_only_version(installed_cli: Path) -> None:
    result = _run([str(installed_cli), "--help"], check=False)
    assert result.returncode == 0, result.stderr
    assert _commands_listed_in_help(result.stdout) == ["version"]


def test_unknown_command_exits_nonzero(installed_cli: Path) -> None:
    result = _run([str(installed_cli), "validate", "x.yaml"], check=False)
    assert result.returncode != 0
