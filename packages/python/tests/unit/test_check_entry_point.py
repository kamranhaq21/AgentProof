"""``run_steps`` with an injected runner: order, stop-on-failure, and the skip rule."""

import subprocess
from pathlib import Path
from typing import Any

import pytest

from agentproof_devtools import check
from agentproof_devtools.check import Step, build_steps, run_steps

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
    return [Step(f"step {n}", (f"tool{n}",)) for n in (1, 2, 3)]


def test_steps_are_the_five_gate_commands_in_order(tmp_path: Path) -> None:
    steps = build_steps(tmp_path)
    assert [step.name for step in steps] == EXPECTED_STEP_NAMES
    assert [step.argv[0] for step in steps] == ["ruff", "ruff", "mypy", "lint-imports", "pytest"]
    assert all(isinstance(step.argv, tuple) for step in steps)


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
        ["lint-imports", "--config", str(tmp_path / ".importlinter")]
    ]
    assert "skipped" not in capsys.readouterr().out


def test_main_exits_with_run_steps_result(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check, "run_steps", lambda steps, *, cwd, runner=None: 7)
    with pytest.raises(SystemExit) as excinfo:
        check.main()
    assert excinfo.value.code == 7
