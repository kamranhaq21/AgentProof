"""``run_steps`` with an injected runner: order, stop-on-failure, multi-command steps, skip rule."""

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from agentproof_devtools import check
from agentproof_devtools.check import Step, build_steps, run_steps
from agentproof_devtools.purity import CORE_PACKAGES

EXPECTED_STEP_NAMES = [
    "ruff check",
    "ruff format --check",
    "mypy --strict",
    "lint-imports",
    "pytest",
]


class RecordingRunner:
    """Stand-in for ``subprocess.run`` that records argv and returns scripted exit codes."""

    def __init__(self, exit_codes: dict[str, int] | None = None) -> None:
        self.exit_codes = exit_codes or {}
        self.calls: list[tuple[list[str], Path]] = []

    def __call__(self, argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[Any]:
        self.calls.append((argv, kwargs["cwd"]))
        return subprocess.CompletedProcess(argv, self.exit_codes.get(argv[0], 0))


def _three_steps() -> list[Step]:
    return [Step(f"step {n}", ((f"tool{n}",),)) for n in (1, 2, 3)]


def test_steps_are_the_five_gate_commands_in_order(tmp_path: Path) -> None:
    steps = build_steps(tmp_path)
    assert [step.name for step in steps] == EXPECTED_STEP_NAMES
    assert [step.commands[0][0] for step in steps] == [
        "ruff",
        "ruff",
        "mypy",
        "lint-imports",
        "pytest",
    ]
    assert all(
        isinstance(step.commands, tuple) and all(isinstance(argv, tuple) for argv in step.commands)
        for step in steps
    )


def test_ruff_check_step_runs_ruff_then_the_purity_checker_on_the_core_packages(
    tmp_path: Path,
) -> None:
    ruff_step = build_steps(tmp_path)[0]
    assert ruff_step.name == "ruff check"
    assert len(ruff_step.commands) == 2
    assert ruff_step.commands[0] == ("ruff", "check", ".")
    purity_argv = ruff_step.commands[1]
    assert purity_argv[:3] == (sys.executable, "-m", "agentproof_devtools.purity")
    assert purity_argv[3] == "src/agentproof/__init__.py"
    assert purity_argv[4:] == tuple(f"src/agentproof/{name}" for name in CORE_PACKAGES)
    assert len(purity_argv[4:]) == 9
    # Every other step is a single command, as in story 1.2.
    assert [len(step.commands) for step in build_steps(tmp_path)[1:]] == [1, 1, 1, 1]


def test_run_steps_runs_every_step_in_order_and_returns_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    runner = RecordingRunner()
    assert run_steps(_three_steps(), cwd=tmp_path, runner=runner) == 0
    assert runner.calls == [(["tool1"], tmp_path), (["tool2"], tmp_path), (["tool3"], tmp_path)]
    assert capsys.readouterr().out.splitlines() == ["==> step 1", "==> step 2", "==> step 3"]


def test_run_steps_stops_at_first_failure_with_its_exit_code(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    runner = RecordingRunner({"tool2": 3})
    assert run_steps(_three_steps(), cwd=tmp_path, runner=runner) == 3
    assert [argv for argv, _ in runner.calls] == [["tool1"], ["tool2"]]
    out = capsys.readouterr().out.splitlines()
    assert out == ["==> step 1", "==> step 2", "failed: step 2 exited 3"]


def test_two_command_step_runs_both_under_one_name(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    step = Step("ruff check", (("ruff", "check", "."), ("purity", "src")))
    runner = RecordingRunner()
    assert run_steps([step], cwd=tmp_path, runner=runner) == 0
    assert [argv for argv, _ in runner.calls] == [["ruff", "check", "."], ["purity", "src"]]
    assert capsys.readouterr().out.splitlines() == ["==> ruff check"]


def test_two_command_step_stops_at_its_first_failing_command(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    steps = [Step("ruff check", (("ruff", "check", "."), ("purity", "src"))), _three_steps()[0]]
    runner = RecordingRunner({"ruff": 1})
    assert run_steps(steps, cwd=tmp_path, runner=runner) == 1
    assert [argv for argv, _ in runner.calls] == [["ruff", "check", "."]]
    out = capsys.readouterr().out.splitlines()
    assert out == ["==> ruff check", "failed: ruff check exited 1"]


def test_second_command_failure_is_reported_under_the_step_name(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    step = Step("ruff check", (("ruff", "check", "."), ("purity", "src")))
    runner = RecordingRunner({"purity": 1})
    assert run_steps([step], cwd=tmp_path, runner=runner) == 1
    assert [argv for argv, _ in runner.calls] == [["ruff", "check", "."], ["purity", "src"]]
    assert capsys.readouterr().out.splitlines() == ["==> ruff check", "failed: ruff check exited 1"]


def test_lint_imports_is_skipped_with_reason_when_config_absent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lint_step = next(step for step in build_steps(tmp_path) if step.name == "lint-imports")
    runner = RecordingRunner()
    assert run_steps([lint_step], cwd=tmp_path, runner=runner) == 0
    assert runner.calls == []
    out = capsys.readouterr().out.splitlines()
    assert out == ["==> lint-imports", "skipped: no .importlinter yet (story 1.3)"]


def test_lint_imports_runs_when_config_present(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / ".importlinter").write_text("[importlinter]\n", encoding="utf-8")
    lint_step = next(step for step in build_steps(tmp_path) if step.name == "lint-imports")
    runner = RecordingRunner({"lint-imports": 1})
    assert run_steps([lint_step], cwd=tmp_path, runner=runner) == 1
    assert [argv for argv, _ in runner.calls] == [
        ["lint-imports", "--config", str(tmp_path / ".importlinter"), "--no-cache"]
    ]
    assert "skipped" not in capsys.readouterr().out


def test_repository_importlinter_exists_so_lint_imports_is_not_skipped() -> None:
    """Story 1.3: the real repository root has the contracts file, so the step runs."""
    lint_step = next(
        step for step in build_steps(check.REPOSITORY_ROOT) if step.name == "lint-imports"
    )
    assert lint_step.skip_reason is not None
    assert lint_step.skip_reason() is None


def test_main_exits_with_run_steps_result(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check, "run_steps", lambda steps, *, cwd, runner=None: 7)
    with pytest.raises(SystemExit) as excinfo:
        check.main()
    assert excinfo.value.code == 7
