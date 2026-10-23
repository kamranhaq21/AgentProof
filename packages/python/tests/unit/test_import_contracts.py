"""Both guards fail on injected violations in a temporary copy of ``src/agentproof``.

Each test copies the package tree and ``.importlinter`` to ``tmp_path``, injects one
matrix violation, and runs the real tools as subprocesses: ``lint-imports`` against the
copied config with ``PYTHONPATH`` pointing at the copy, ``ruff check`` with the
repository ``pyproject.toml`` (its ``per-file-ignores`` patterns resolve against the
working directory, so the copy keeps the ``src/agentproof`` layout), and the purity
checker on the copied core packages. The repository tree itself is never modified.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from agentproof_devtools.purity import CORE_PACKAGES

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]
PYPROJECT = PACKAGE_ROOT / "pyproject.toml"
IMPORTLINTER = REPOSITORY_ROOT / ".importlinter"
SUBPROCESS_TIMEOUT_SECONDS = 300


def _tool(name: str) -> str:
    """Locate a console script next to the running interpreter, then on PATH."""
    search_path = os.pathsep.join([str(Path(sys.executable).parent), os.environ.get("PATH", "")])
    found = shutil.which(name, path=search_path)
    if not found:
        pytest.fail(f"{name} is required but was not found next to {sys.executable} or on PATH")
    return found


def _run(argv: list[str], *, cwd: Path, extra_env: dict[str, str] | None = None) -> str:
    """Run argv; return combined stdout and stderr (the caller checks ``_exit`` separately)."""
    result = _completed(argv, cwd=cwd, extra_env=extra_env)
    return result.stdout + result.stderr


def _completed(
    argv: list[str], *, cwd: Path, extra_env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "NO_COLOR": "1", "PYTHONIOENCODING": "utf-8", **(extra_env or {})}
    return subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
        check=False,
    )


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A copy of ``src/agentproof`` and ``.importlinter`` under ``tmp_path``."""
    shutil.copytree(
        PACKAGE_ROOT / "src" / "agentproof",
        tmp_path / "src" / "agentproof",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copy(IMPORTLINTER, tmp_path / ".importlinter")
    return tmp_path


def lint_imports(tree: Path) -> subprocess.CompletedProcess[str]:
    """``lint-imports`` on the copy; ``--no-cache`` so no graph from another copy is reused."""
    return _completed(
        [_tool("lint-imports"), "--config", str(tree / ".importlinter"), "--no-cache"],
        cwd=tree,
        extra_env={"PYTHONPATH": str(tree / "src")},
    )


def ruff_check(tree: Path) -> subprocess.CompletedProcess[str]:
    return _completed(
        [
            _tool("ruff"),
            "check",
            "--no-cache",
            "--config",
            str(PYPROJECT),
            "--output-format",
            "concise",
            "src",
        ],
        cwd=tree,
    )


def purity(tree: Path) -> subprocess.CompletedProcess[str]:
    targets = [str(Path("src", "agentproof", name)) for name in CORE_PACKAGES]
    return _completed(
        [sys.executable, "-m", "agentproof_devtools.purity", *targets],
        cwd=tree,
    )


def _write(tree: Path, relative: str, source: str) -> None:
    (tree / "src" / "agentproof" / relative).write_text(source, encoding="utf-8")


def _append(tree: Path, relative: str, source: str) -> None:
    path = tree / "src" / "agentproof" / relative
    path.write_text(path.read_text(encoding="utf-8") + source, encoding="utf-8")


def test_clean_copy_passes_every_guard(tree: Path) -> None:
    linted = lint_imports(tree)
    assert linted.returncode == 0, linted.stdout + linted.stderr
    assert "Contracts: 7 kept, 0 broken." in linted.stdout
    ruffed = ruff_check(tree)
    assert ruffed.returncode == 0, ruffed.stdout + ruffed.stderr
    pure = purity(tree)
    assert pure.returncode == 0, pure.stdout + pure.stderr
    assert pure.stdout == ""


def test_upward_import_from_models_to_cli_breaks_the_contracts(tree: Path) -> None:
    _append(tree, "models/__init__.py", "\nimport agentproof.cli\n")
    linted = lint_imports(tree)
    assert linted.returncode != 0
    assert "agentproof.models" in linted.stdout
    assert "agentproof.cli" in linted.stdout
    assert "broken" in linted.stdout
    assert "Contracts: 7 kept, 0 broken." not in linted.stdout


def test_cli_importing_engine_directly_breaks_the_cli_contract(tree: Path) -> None:
    """The layers allow cli -> engine; the forbidden cli contract is what must catch it."""
    _append(tree, "cli/app.py", "\nimport agentproof.engine\n")
    linted = lint_imports(tree)
    assert linted.returncode != 0
    assert "cli imports only runner, io, errors, constants, models BROKEN" in linted.stdout
    assert "agentproof.cli.app" in linted.stdout
    assert "agentproof.engine" in linted.stdout


def test_cli_may_import_the_public_api_modules_directly() -> None:
    """Story 3.1: AD-2 lets cli import the public API (AD-15), so `errors`, `constants`,
    and `models` are not forbidden; the clean-copy test above proves the live imports in
    `cli/app.py`, `cli/exit_codes.py`, and `cli/commands/version.py` keep every contract."""
    forbidden = _cli_forbidden_modules(IMPORTLINTER.read_text(encoding="utf-8"))
    assert {"agentproof.errors", "agentproof.constants", "agentproof.models"}.isdisjoint(forbidden)
    assert {"agentproof.engine", "agentproof.loading", "agentproof.testing"} <= forbidden


def _cli_forbidden_modules(config: str) -> set[str]:
    """The `forbidden_modules` of the `cli` contract, read from the config text."""
    section = config.split("[importlinter:contract:cli]", 1)[1].split("[importlinter:", 1)[0]
    body = section.split("forbidden_modules =", 1)[1]
    modules: set[str] = set()
    for line in body.splitlines()[1:]:
        if not line.startswith(" "):
            break
        modules.add(line.strip())
    return modules


@pytest.mark.parametrize(
    ("relative", "statement", "contract"),
    [
        (
            "io/__init__.py",
            "import agentproof.engine",
            "io imports only errors, constants, redaction",
        ),
        (
            "adapters/__init__.py",
            "import agentproof.engine",
            "adapters imports only errors, constants, models, loading, io",
        ),
        (
            "testing/__init__.py",
            "import agentproof.runner",
            "testing imports only models, loading, adapters, errors",
        ),
        ("io/__init__.py", "import agentproof.cli", "nothing imports cli"),
        ("errors.py", "import agentproof.constants", "AD-2 dependency direction (layers)"),
    ],
)
def test_each_forbidden_or_layer_contract_catches_its_violation(
    tree: Path, relative: str, statement: str, contract: str
) -> None:
    _append(tree, relative, f"\n{statement}\n")
    linted = lint_imports(tree)
    assert linted.returncode != 0
    assert f"{contract} BROKEN" in linted.stdout
    assert statement.removeprefix("import ") in linted.stdout


def test_core_importing_a_shell_package_breaks_the_core_contract(tree: Path) -> None:
    _append(tree, "engine/__init__.py", "\nimport agentproof.io  # noqa: F401\n")
    linted = lint_imports(tree)
    assert linted.returncode != 0
    assert "core imports no shell package BROKEN" in linted.stdout
    assert "agentproof.engine" in linted.stdout
    assert "agentproof.io" in linted.stdout


def test_core_file_io_fails_the_ruff_check_step_through_the_purity_checker(tree: Path) -> None:
    _write(
        tree,
        "engine/__init__.py",
        'from pathlib import Path\n\nopen("x")\nPath("x").read_text()\n',
    )
    ruffed = ruff_check(tree)
    pure = purity(tree)
    # The step is both commands under one name; it fails when either exits non-zero.
    assert ruffed.returncode != 0 or pure.returncode != 0
    assert pure.returncode == 1
    lines = pure.stdout.splitlines()
    assert any(
        line.startswith(str(Path("src", "agentproof", "engine", "__init__.py"))) for line in lines
    )
    assert any("purity: open" in line for line in lines)
    assert any("read_text" in line for line in lines)


@pytest.mark.parametrize(
    ("source", "banned"),
    [
        ("import subprocess\n\nsubprocess.run(['x'])\n", "subprocess"),
        ("import os\n\nos.environ['A']\n", "os.environ"),
        ("import datetime\n\ndatetime.datetime.now()\n", "datetime.datetime.now"),
        ("import time\n\ntime.time()\n", "time"),
        ("import uuid\n\nuuid.uuid4()\n", "uuid"),
    ],
)
def test_core_environment_or_clock_use_is_a_tid251_finding(
    tree: Path, source: str, banned: str
) -> None:
    _write(tree, "loading/__init__.py", source)
    ruffed = ruff_check(tree)
    assert ruffed.returncode != 0
    assert "TID251" in ruffed.stdout
    assert f"`{banned}` is banned" in ruffed.stdout
    assert str(Path("src", "agentproof", "loading", "__init__.py")) in ruffed.stdout


def test_shell_package_is_exempt_from_both_guards(tree: Path) -> None:
    _write(tree, "io/__init__.py", 'import socket\n\nsocket.socket()\nopen("x")\n')
    ruffed = ruff_check(tree)
    assert ruffed.returncode == 0, ruffed.stdout + ruffed.stderr
    assert "TID251" not in ruffed.stdout
    pure = purity(tree)
    assert pure.returncode == 0
    assert pure.stdout == ""
