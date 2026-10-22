"""The single ``check`` entry point (architecture AD-17).

``uv run check`` runs the quality gate as an ordered list of steps, prints each
step's name, and stops at the first failure, exiting with that step's code. CI calls
the same entry point (story 1.4), so the gate is defined exactly once, here.

A step is one or more argv lists handed to ``subprocess.run`` in order; nothing is
ever passed through a shell string. The ``ruff check`` step is two commands under one
name: ruff itself, then the AST purity checker for the core packages (story 1.3), so
the five step names and their order from story 1.2 are unchanged.
"""

import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentproof_devtools.purity import CORE_PACKAGES

# ``packages/python``: the directory holding ``pyproject.toml`` and ``uv.lock``. This
# only holds for an editable install of devtools (uv's default for workspace
# members); story 1.4's CI must keep it editable or set the root explicitly.
PACKAGE_ROOT = Path(__file__).resolve().parents[3]
# The git repository root, where ``.importlinter`` lives (story 1.3).
REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]

# Core package targets for the purity checker, relative to ``PACKAGE_ROOT``; the package
# top level is core too (TID251 applies to it), so it is scanned as well.
PURITY_TARGETS: tuple[str, ...] = (
    "src/agentproof/__init__.py",
    *(f"src/agentproof/{name}" for name in CORE_PACKAGES),
)

Runner = Callable[..., "subprocess.CompletedProcess[Any]"]


@dataclass(frozen=True)
class Step:
    """One gate step: a display name, the argv lists to run in order, an optional skip test."""

    name: str
    commands: tuple[tuple[str, ...], ...]
    skip_reason: Callable[[], str | None] | None = None


def build_steps(repository_root: Path) -> list[Step]:
    """Return the five gate steps; ``lint-imports`` is skipped until ``.importlinter`` exists."""
    import_linter_config = repository_root / ".importlinter"

    def import_linter_skip_reason() -> str | None:
        if import_linter_config.is_file():
            return None
        return "no .importlinter yet (story 1.3)"

    return [
        Step(
            "ruff check",
            (
                ("ruff", "check", "."),
                (sys.executable, "-m", "agentproof_devtools.purity", *PURITY_TARGETS),
            ),
        ),
        Step("ruff format --check", (("ruff", "format", "--check", "."),)),
        Step("mypy --strict", (("mypy", "--strict"),)),
        Step(
            "lint-imports",
            (("lint-imports", "--config", str(import_linter_config), "--no-cache"),),
            skip_reason=import_linter_skip_reason,
        ),
        Step("pytest", (("pytest",),)),
    ]


def run_steps(
    steps: Sequence[Step],
    *,
    cwd: Path,
    runner: Runner = subprocess.run,
) -> int:
    """Run ``steps`` in order inside ``cwd``; return the first non-zero exit code, else 0.

    A step whose ``skip_reason`` returns text is reported as skipped and not run. A
    step's commands run in order and the step fails at its first non-zero command.
    Each command's own output goes straight to the inherited stdout and stderr.
    """
    for step in steps:
        print(f"==> {step.name}", flush=True)
        reason = step.skip_reason() if step.skip_reason is not None else None
        if reason is not None:
            print(f"skipped: {reason}", flush=True)
            continue
        for argv in step.commands:
            completed = runner(list(argv), cwd=cwd)
            if completed.returncode != 0:
                print(f"failed: {step.name} exited {completed.returncode}", flush=True)
                return int(completed.returncode)
    return 0


def main() -> None:
    """Console-script entry point declared in ``devtools/pyproject.toml``."""
    if not (PACKAGE_ROOT / "pyproject.toml").is_file():
        print(
            f"check: no pyproject.toml at {PACKAGE_ROOT}; install devtools editable",
            file=sys.stderr,
        )
        sys.exit(2)
    sys.exit(run_steps(build_steps(REPOSITORY_ROOT), cwd=PACKAGE_ROOT))
