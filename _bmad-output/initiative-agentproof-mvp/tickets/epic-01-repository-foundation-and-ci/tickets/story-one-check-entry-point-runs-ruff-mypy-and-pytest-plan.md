---
title: 'One check entry point runs ruff, mypy, and pytest'
type: 'feature'
ticket: '2'
created: '2026-10-22'
status: 'built'
baseline_revision: 'f12115c3b08b575ec14247bf88b0d5bb7981dbe9'
route: 'full'
route_source: 'pinned'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** There is no single command that decides whether a change is acceptable; every later story and the CI job need one ordered gate (story 1.2, epic 1 R3, spine AD-17).

**Approach:** Provide `uv run check` as a console script that runs `ruff check`, `ruff format --check`, `mypy --strict`, `lint-imports`, and `pytest` in that order, printing each step's name and stopping at the first failure; configure ruff, mypy (strict, pydantic plugin, `src` only), and pytest in `pyproject.toml`; report the `lint-imports` step as skipped with a reason until `.importlinter` exists (story 1.3).

**Decision delegated by the maintainer (2026-10-22, "approve all, you are the owner"; ARCH-4):** the `check` console script is provided by a uv workspace member `packages/python/devtools` (distribution `agentproof-devtools`, module `agentproof_devtools.check`) declared as a dev dependency with a workspace source, so it is never part of the shipped `agentproof` wheel and `uv run check` resolves inside the project environment. ARCH-1: mypy with the pydantic plugin.

## Boundaries & Constraints

**Always:** Step order and names exactly `ruff check`, `ruff format --check`, `mypy --strict`, `lint-imports`, `pytest`; stop on the first non-zero exit and exit with that step's code; `pyproject.toml` remains the single version source and its `[project]` table keeps exactly the four runtime dependencies; mypy targets `src` only; the `agentproof` wheel contents stay identical to story 1.1 (verified by the existing smoke test).

**Never:** No `.importlinter` or banned-API rules (story 1.3); no CI workflow (story 1.4); no hygiene files or CONTRIBUTING (story 1.5); no new runtime dependency; no command beyond `version` in the app; no edits to `AGENTS.md` or `PROJECT_SPEC.md`; the check script never shells through a string, it runs argv lists.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Clean tree | `uv run check` on the current scaffold | five step names printed in order, `lint-imports` marked skipped with the reason, exit 0 | No error expected |
| Failing step stops the run | a step list where step 2 exits 1 | step 1 ran, step 2 reported failed, steps 3 to 5 not run, exit 1 | exit code of the failing step |
| `.importlinter` present | file exists at the repository root | `lint-imports` runs instead of being skipped | its own exit code |
| mypy strictness | `pyproject.toml` `[tool.mypy]` | `strict = true`, `plugins = ["pydantic.mypy"]`, `files = ["src"]` | No error expected |
| Real failures | an unused import, a type error, a failing test each introduced on a scratch copy | `uv run check` exits non-zero at `ruff check`, `mypy --strict`, `pytest` respectively | documented in Implementation Notes |

</frozen-after-approval>

## Code Map

- `packages/python/pyproject.toml` -- edit; add `[tool.ruff]` (line-length 100), `[tool.ruff.lint]` (`select = ["E", "F", "I", "UP", "B"]`), `[tool.mypy]` (`strict = true`, `plugins = ["pydantic.mypy"]`, `files = ["src"]`), keep `[tool.pytest.ini_options]`; add dev dependencies `ruff>=0.17`, `mypy>=2.4`, `import-linter>=2.15`, `agentproof-devtools`; add `[tool.uv.workspace] members = ["devtools"]` and `[tool.uv.sources] agentproof-devtools = { workspace = true }`.
- `packages/python/devtools/pyproject.toml` -- new; hatchling; `name = "agentproof-devtools"`, `version = "0.0.0"`, `requires-python = ">=3.12,<4"`, no dependencies; `[project.scripts] check = "agentproof_devtools.check:main"`; wheel `packages = ["src/agentproof_devtools"]`.
- `packages/python/devtools/src/agentproof_devtools/__init__.py`, `check.py` -- new; `STEPS: list[Step]` with name and argv; `run_steps(steps, *, cwd, runner=subprocess.run) -> int` runs sequentially, prints `==> <name>`, prints `skipped: <reason>` for a step whose `skip_reason` callable returns text, stops at the first non-zero return code and returns it; `main()` calls `run_steps(STEPS, cwd=<package root>)` and `sys.exit`s with the result; the `lint-imports` step's skip reason is "no .importlinter yet (story 1.3)" when the file is absent from the repository root.
- `packages/python/tests/unit/test_check_entry_point.py` -- new; injected runner tests: order and names, stop at first failure with its exit code, skip reason when `.importlinter` is absent, step runs when present (use `tmp_path` and monkeypatched root).
- Existing `packages/python/src/agentproof/cli/app.py` and `__init__.py` must pass `mypy --strict`; typer and importlib.metadata are typed, so no changes are expected.
- Reuse: `uv run pytest` config from story 1.1; nothing else exists.

## Tasks & Acceptance

**Execution:**
- [x] `packages/python/devtools/**` -- create the workspace member with the `check` console script -- ARCH-4 decision; keeps dev tooling out of the shipped wheel
- [x] `packages/python/devtools/src/agentproof_devtools/check.py` -- implement `STEPS`, `run_steps`, `main` -- AD-17 ordered gate with stop-on-failure
- [x] `packages/python/pyproject.toml` -- ruff, mypy, dev dependencies, workspace, sources -- criterion 3 and the dev environment
- [x] `packages/python/uv.lock` -- `uv lock` then `uv sync` -- environment carries ruff, mypy, import-linter, devtools
- [x] `packages/python/tests/unit/test_check_entry_point.py` -- cover matrix rows 2 to 4 with an injected runner -- criteria 1, 2, 4
- [x] verification -- run `uv run check` clean, then prove each real failure class stops the run on a scratch copy and record it -- criterion 2, matrix row 5

**Acceptance Criteria:**
- Given the scaffold, when `uv run check` runs, then it prints the five step names in order, marks `lint-imports` skipped with the reason, and exits 0.
- Given an injected failing second step, when `run_steps` runs, then it returns that step's exit code and the later steps never execute.
- Given `pyproject.toml`, when the mypy section is read, then strict mode, the pydantic plugin, and `src` as the only target are set.
- Given the built `agentproof` wheel, when its file list is compared with story 1.1, then it is identical (no devtools inside).

## Implementation Notes

- 2026-10-23, orchestrator (matrix test audit): added `packages/python/tests/unit/test_tooling_config.py` (mypy strict, pydantic plugin, `src` only; runtime dependencies unchanged) so matrix row 4 has a test; `uv run check` then ran all five steps with `lint-imports` skipped and `pytest` reporting `16 passed in 50.94s`, exit 0. The file belongs in the Code Map as a second new test module.

- 2026-10-22 (implementation, Claude): built as planned. Files: `packages/python/devtools/pyproject.toml`, `packages/python/devtools/src/agentproof_devtools/{__init__,check}.py`, `packages/python/tests/unit/test_check_entry_point.py` (new); `packages/python/pyproject.toml`, `packages/python/uv.lock` (edited). `uv lock` resolved ruff 0.17.2, mypy 2.4.0, import-linter 2.15, agentproof-devtools 0.0.0 (workspace); `uv sync` installed them plus click, grimp, librt, ast-serialize, pathspec, mypy-extensions as transitive dev deps. The `[project]` table is untouched (same four runtime deps, same version).
- Step argv (all argv lists, no shell): `ruff check .`, `ruff format --check .`, `mypy --strict` (targets come from `[tool.mypy] files = ["src"]`), `lint-imports --config <repo root>/.importlinter`, `pytest`; all run with `cwd = packages/python` (`PACKAGE_ROOT = Path(__file__).resolve().parents[3]`). `REPOSITORY_ROOT = PACKAGE_ROOT.parents[1]` is a module attribute so the tests monkeypatch it to `tmp_path` for the absent/present `.importlinter` rows. Beyond the required `==> <name>` and `skipped: <reason>` lines, a failing step also prints `failed: <name> exited <code>` before the run stops; the exit code returned is the step's own.
- Code Map addition: `[tool.ruff] src = [".", "src", "devtools/src"]`. Without it ruff's isort treats `agentproof_devtools` as third-party (the first `uv run check` failed with I001 in the new test file for exactly this). Listing both source roots is the principled fix over a `known-first-party` list. `[tool.ruff.lint] select` is exactly the planned `E, F, I, UP, B`.
- Verification (all from `packages/python`): `uv run check` -> `==> ruff check` All checks passed; `==> ruff format --check` 22 files already formatted; `==> mypy --strict` Success: no issues found in 16 source files; `==> lint-imports` `skipped: no .importlinter yet (story 1.3)`; `==> pytest` 14 passed (story 1.1's 8 plus 6 new); exit 0. `uv run pytest -q` -> 14 passed, exit 0. `uv run mypy --strict` -> Success, 16 source files, exit 0 (typer and importlib.metadata needed no changes, as predicted). `uv build` -> wheel `agentproof-0.1.0.dev0-py3-none-any.whl` holds the identical 16 `agentproof/` source files from story 1.1 and no `agentproof_devtools`; dist removed afterwards.
- Scratch-copy failure proofs (copy of `packages/python` without `.venv` in the session scratchpad, own `uv sync`, baseline `uv run check` exit 0 there): (A) `import os` appended to `src/agentproof/constants.py` -> stopped at `ruff check`, `F401 os imported but unused`, exit 1; nothing after it ran. (B) `INJECTED_TYPE_ERROR: int = "not an int"` appended to the same file -> stopped at `mypy --strict`, `constants.py:3: error: Incompatible types in assignment ... [assignment]`, exit 1. (C) `tests/unit/test_injected_failure.py` with `assert 1 == 2` -> `ruff check`, `ruff format --check`, `mypy --strict` passed, `lint-imports` skipped, stopped at `pytest`, `FAILED ...::test_injected_failure`, exit 1. After reverting each, `uv run check` returned to exit 0. Scratch copy deleted.
- Observation from proof B's first two attempts: appending the type error without a blank line after the module docstring, and then with LF endings into a CRLF-checked-out file, both stopped the gate at `ruff format --check` (exit 1) before mypy ran. That is the ordered gate behaving correctly, and it shows the working copy is CRLF under git autocrlf; git warns that the LF files written here (`pyproject.toml`, `uv.lock`, new sources) will be normalised on the next touch. Harmless, and `.gitattributes` is story 1.5's job.
- Risk noted, outside this story's boundary: the sdist (`agentproof-0.1.0.dev0.tar.gz`) includes `devtools/` and `tests/` because hatchling's default sdist takes the whole project directory and there is no `.gitignore`/sdist include list yet. The acceptance criterion is about the wheel, which is clean; an sdist `include`/`exclude` list or the hygiene files from story 1.5 can tighten this.
- `uv run` rebuilds the editable `agentproof` on the first run after a `pyproject.toml` edit (one-off, a few seconds); ruff/mypy/pytest caches (`.ruff_cache`, `.mypy_cache`, `.pytest_cache`, `__pycache__`) were removed before finishing. No `.importlinter`, CI workflow, or hygiene files were created; no git state touched.

- 2026-10-23 (review fixes, Claude): `check.py` replaces the module-level `STEPS` with `build_steps(repository_root: Path) -> list[Step]`, so the `lint-imports` `--config` path and its skip reason derive from one argument (no `STEPS` constant kept; nothing needed it); `main()` calls `build_steps(REPOSITORY_ROOT)` and first fails fast with a one-line stderr message and exit 2 when `PACKAGE_ROOT / "pyproject.toml"` is missing (the `parents[3]` root only holds for an editable install; comment added for story 1.4). Unit tests call `build_steps(tmp_path)` instead of monkeypatching the global and assert the full lint-imports argv `["lint-imports", "--config", str(tmp_path / ".importlinter")]` in the runs-when-present case. `test_install_smoke.py` gains `test_wheel_contains_only_the_agentproof_package` (zipfile: every member under `agentproof/` or `agentproof-<version>.dist-info/`, none containing `agentproof_devtools`) for criterion 4. Verified: `ruff format` + `ruff check` on the three edited files clean; `uv run pytest -q tests/unit/test_check_entry_point.py tests/integration/test_install_smoke.py` -> 10 passed, exit 0. Caches removed.

## Plan Change Log

## Review Triage Log

### Review pass 1 (quick lens), 2026-10-23

Verdicts: high 0, medium 3, low 2, false 0, maybe-false 0.

| Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| Implementation Notes record 14 tests and 22 formatted files; the tree has 16 and 23 after the orchestrator's audit test | low | patch (notes) | True; the audit addition and its 16-test run are now recorded above. |
| Criterion 4 (wheel identical, no devtools) attributed to the smoke test, which does not list wheel members | medium | patch | True; a `zipfile` member assertion is added to the smoke test. |
| `lint-imports` argv bakes the config path at import time while the skip rule reads the global at call time; the test asserts only argv[0] | medium | patch | True; `build_steps(repository_root)` derives both from one argument and the test asserts the full argv. |
| `PACKAGE_ROOT` from `parents[3]` is wrong under a non-editable install | medium | patch | True and plausible for story 1.4; `main()` now fails fast when `pyproject.toml` is absent at the computed root. |
| Execution checkboxes unticked though the work is recorded | low | patch (plan bookkeeping) | True; ticked below. |

## Verification

**Commands:**
- `cd packages/python && uv lock && uv sync` -- expected: devtools, ruff, mypy, import-linter installed
- `cd packages/python && uv run check` -- expected: five steps, `lint-imports` skipped, exit 0
- `cd packages/python && uv run pytest -q` -- expected: all tests pass (story 1.1's 8 plus the new ones)
- `cd packages/python && uv run mypy --strict` -- expected: no errors in `src`
- `cd packages/python && uv build && unzip -l dist/agentproof-*.whl` -- expected: same 16 source files as story 1.1, no `agentproof_devtools`
- scratch copy: add an unused import, then a type error, then a failing test, running `uv run check` after each -- expected: non-zero at `ruff check`, `mypy --strict`, `pytest` respectively; revert each

**Manual checks (if no CLI):**
- `git status` shows only the Code Map paths plus `uv.lock`.
