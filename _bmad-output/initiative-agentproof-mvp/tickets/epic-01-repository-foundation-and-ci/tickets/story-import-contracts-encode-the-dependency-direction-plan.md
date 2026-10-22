---
title: 'Import contracts encode the dependency direction'
type: 'feature'
ticket: '3'
created: '2026-10-23'
status: 'built'
baseline_revision: '8afabe2973e7192a607bd1fb423d3bf36020efef'
route: 'full'
route_source: 'pinned'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The architecture's dependency direction (AD-2) and pure-core rule (AD-1) exist only as prose; nothing fails when a module imports upward or when core code touches the clock, the environment, or the filesystem (story 1.3, epic 1 R4).

**Approach:** Add `.importlinter` at the repository root with the AD-2 layer contract and the four forbidden contracts, make the `lint-imports` step of `uv run check` run for real, ban the importable stdlib names in core packages through ruff's `flake8-tidy-imports` banned-API list scoped by per-file ignores, and add a small AST purity checker in the devtools package for the two things ruff cannot see (bare `open(` and `pathlib.Path` I/O methods), run inside the existing `ruff check` step so the step order from story 1.2 is unchanged. Prove with a test on a temporary copy that both guards fail on injected violations.

**Decisions delegated by the maintainer (2026-10-22, "approve all, you are the owner"):** the purity checker is part of the `ruff check` step (same name, two commands) rather than a sixth step; the `cli` forbidden contract allows indirect imports because `cli` may import the package's top level, which will itself import core modules once the public API exists (AD-15).

## Boundaries & Constraints

**Always:** Step names and order from story 1.2 stay `ruff check`, `ruff format --check`, `mypy --strict`, `lint-imports`, `pytest`; `.importlinter` lives at the repository root and names `agentproof` as the root package; banned names apply only to `agentproof.constants`, `errors`, `models`, `loading`, `redaction`, `assertions`, `engine`, `reports`, `compare`; the shell packages `adapters`, `runner`, `io`, `cli`, `testing`, plus `devtools` and `tests`, are exempt; every contract passes on the current empty packages; the `agentproof` wheel contents stay identical to story 1.1.

**Never:** No real module code in any core package; no CI (story 1.4); no hygiene files (story 1.5); no new runtime dependency; no change to the `lint-imports` skip rule beyond it now finding the file; no edits to `AGENTS.md` or `PROJECT_SPEC.md`; the purity checker never executes or imports the files it checks, it parses them with `ast`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Clean tree | `uv run check` on the scaffold with `.importlinter` present | `lint-imports` runs (not skipped) and passes; all five steps exit 0 | No error expected |
| Upward import | temporary copy where `agentproof/models/__init__.py` contains `import agentproof.cli` | `lint-imports` exits non-zero naming `agentproof.models` and `agentproof.cli` | contract violation |
| Core file I/O | temporary copy where `agentproof/engine/__init__.py` contains `open("x")` and a `Path("x").read_text()` call | the `ruff check` step exits non-zero; the purity checker names `agentproof/engine/__init__.py` and the call | TID251 or purity violation |
| Core environment or clock | temporary copy where a core module contains `import subprocess`, `os.environ`, or `datetime.datetime.now()` | `ruff check` reports TID251 naming the banned name | lint violation |
| Shell package | `agentproof/io/__init__.py` containing `open("x")` and `import socket` | no TID251 and no purity finding (exempt) | No error expected |
| `cli` reaches core directly | temporary copy where `agentproof/cli/app.py` imports `agentproof.models` | `lint-imports` exits non-zero naming the forbidden import | contract violation |

</frozen-after-approval>

## Code Map

- `.importlinter` -- new, repository root; a seventh `forbidden` contract "core imports no shell package" (source: the nine core packages; forbidden: `io`, `adapters`, `runner`, `cli`, `testing`) added after review pass 1; `[importlinter] root_packages = agentproof`; contract `layers`: `agentproof.cli`, `agentproof.runner`, `agentproof.reports | agentproof.compare`, `agentproof.engine`, `agentproof.loading | agentproof.redaction | agentproof.assertions`, `agentproof.models`, `agentproof.constants`, `agentproof.errors`; contract `forbidden` "io imports only errors, constants, redaction" (source `agentproof.io`, forbidden: every other subpackage); "adapters imports only errors, constants, models, loading, io"; "testing imports only models, loading, adapters, errors"; "cli imports only runner and io" with `allow_indirect_imports = True`; "nothing imports cli" (source: every subpackage except `cli`, forbidden `agentproof.cli`).
- `packages/python/pyproject.toml` -- edit; add `"TID"` to `[tool.ruff.lint] select`; `[tool.ruff.lint.flake8-tidy-imports.banned-api]` entries for `os.environ`, `os.getenv`, `os.getcwd`, `time`, `datetime.datetime.now`, `datetime.datetime.today`, `uuid`, `random`, `socket`, `subprocess`, `threading`, `asyncio`, each with a message pointing at AD-1; `[tool.ruff.lint.per-file-ignores]` exempting `src/agentproof/{adapters,runner,io,cli,testing}/**`, `devtools/**`, and `tests/**` from `TID251`.
- `packages/python/devtools/src/agentproof_devtools/purity.py` -- new; `find_violations(path: Path) -> list[Violation]` parses one file with `ast` and reports calls to bare `open`, and attribute calls named `read_text`, `read_bytes`, `write_text`, `write_bytes`, `open`, `mkdir`, `unlink`, `rename`, `replace`, `touch`, `exists`, `is_file`, `is_dir`, `iterdir`, `glob`, `rglob`, `stat` on any receiver; `main(argv)` walks the core package directories given as arguments, prints `path:line:col: purity: <name>` per finding, exits 1 when any; `CORE_PACKAGES` tuple names the nine core packages.
- `packages/python/devtools/src/agentproof_devtools/check.py` -- edit; the `ruff check` step becomes two argv runs under one name: `ruff check .` then `python -m agentproof_devtools.purity src/agentproof/<core...>`; `Step` gains `argv` as a tuple of argv tuples, or a second field; keep `build_steps(repository_root)`; `lint-imports` argv and skip rule unchanged.
- `packages/python/tests/unit/test_check_entry_point.py` -- update for the two-command step if `Step` changes shape.
- `packages/python/tests/unit/test_purity.py` -- new; unit tests of `find_violations` on inline source strings: bare open, Path method, exempt names (`str.replace` is an attribute call named `replace` on a string: the checker must not flag calls whose receiver is a string literal or whose name is `replace` on a non-Path; keep the rule simple and document the known false-positive surface in a comment: receivers are not type-resolved, so `s.replace(...)` in core must be written as `str.replace(s, ...)` or the finding suppressed with `# purity: ok`).
- `packages/python/tests/unit/test_import_contracts.py` -- new; copies `src/agentproof` and `.importlinter` to `tmp_path`, injects each matrix violation, runs `lint-imports --config <copy>/.importlinter` with `PYTHONPATH=<copy>/src` and `ruff check --config <pyproject>` plus the purity module as subprocesses, asserts non-zero exit and that stdout or stderr names the offending module or call; asserts the clean copy passes both.
- Existing: `cli/app.py` imports `from agentproof import __version__` (top level, allowed by the indirect rule) and `typer`; no core module imports anything today.

## Tasks & Acceptance

**Execution:**
- [x] `.importlinter` -- write the layer and forbidden contracts -- AD-2 as a tool-checked rule
- [x] `packages/python/pyproject.toml` -- TID select, banned-api list, per-file ignores -- AD-1 importable names
- [x] `packages/python/devtools/src/agentproof_devtools/purity.py` -- AST checker for `open` and Path I/O methods -- AD-1 names ruff cannot see
- [x] `packages/python/devtools/src/agentproof_devtools/check.py` -- run purity inside the `ruff check` step -- order unchanged (story 1.2 boundary)
- [x] `packages/python/tests/unit/test_purity.py`, `test_check_entry_point.py` -- unit coverage for the checker and the two-command step
- [x] `packages/python/tests/unit/test_import_contracts.py` -- temporary-copy negative tests for every matrix row -- criterion 4
- [x] verification -- `uv run check` shows `lint-imports` running and passing; record output

**Acceptance Criteria:**
- Given `.importlinter`, when `uv run check` runs, then the `lint-imports` step runs and passes on the empty packages and the whole gate exits 0.
- Given a temporary copy with `import agentproof.cli` in `agentproof/models/__init__.py`, when `lint-imports` runs on it, then it fails naming both modules.
- Given a temporary copy with `open("x")` in `agentproof/engine/__init__.py`, when the `ruff check` step runs on it, then it fails naming the file and the call.
- Given `agentproof/io/__init__.py` with `open("x")` and `import socket` in a temporary copy, when both guards run, then neither reports it.

## Implementation Notes

Implemented 2026-10-23 on branch `story/1-3-import-contracts` (uv 0.13.5, Python 3.12.15, ruff 0.17.2, import-linter 2.15, mypy 2.4.0). Nothing committed.

**Empirical result the plan asked for (ruff banned-api and bare `open(`):** a `"builtins.open"` banned-api entry flags only an explicit `builtins.open(...)` call; the bare `open("x")` on the previous line of the same file was not reported, a bare `"open"` entry reports nothing, and `Path("z").read_text()` is likewise invisible to TID251 (instance method calls are not qualified import names). So the purity checker covers both shapes as planned. It also reports any attribute call named `open` (so `builtins.open(...)`, `io.open(...)`, and `Path(...).open(...)` are caught without a banned-api entry).

**Other facts established before writing code:**
- TID251 does ban stdlib names: `subprocess`, `time`, `random`, `os.environ` (also `from os import environ`), `os.getenv`, `datetime.datetime.now` (also through `from datetime import datetime as dt; dt.now()`), `datetime.datetime.today`. A banned module is reported once at its import line; a later `time.time()` call is not a second finding.
- `per-file-ignores` patterns with a `/` resolve against the working directory, not the directory of a `--config` file: the same config exempted `src/agentproof/io/**` when run with cwd at the project but not from another cwd with absolute paths. The temporary-copy test therefore keeps the `src/agentproof` layout under `tmp_path` and runs ruff with `cwd=tmp_path` and `--config <repository pyproject>`. Brace globs (`src/agentproof/{adapters,runner,io,cli,testing}/**`) work in ruff's per-file-ignores.
- Selecting `"TID"` also enables TID252 (parent-relative imports `from .. import x` are banned at ruff's default `parents` setting) and TID253 (a no-op without `banned-module-level-imports`). No findings today.

**Decisions:**
- `Step.argv` became `Step.commands: tuple[tuple[str, ...], ...]`; every step but `ruff check` has one command. `run_steps` runs a step's commands in order and fails the step at the first non-zero one, printing `failed: ruff check exited N` under the step name. The step list, names, and order are unchanged from story 1.2.
- The purity command is `(sys.executable, "-m", "agentproof_devtools.purity", "src/agentproof/constants", ..., "src/agentproof/compare")` (nine targets from `purity.CORE_PACKAGES`), with `sys.executable` rather than a bare `python` so the venv interpreter runs regardless of PATH. `purity.resolve_target` maps `src/agentproof/constants` to `constants.py` while it is a module and to the directory once it becomes a package, so the argv stays stable across that transition.
- Purity exemptions: a receiver that is any literal (`"a-b".replace(...)`, `b"..".replace(...)`) or the name `str`/`bytes` (`str.replace(s, ...)`); `# purity: ok` on the line where the call starts suppresses that line's findings only. Receivers are otherwise not type-resolved; `s.replace(...)` on a `str` is the documented false positive and a unit test pins that behaviour. Columns are 1-based like ruff's. Exit 1 on findings (with a one-line summary after the per-call lines), 2 for a missing target, no targets, or a file that does not parse. The checker only ever calls `ast.parse`; a unit test proves a module with a failing import and a side effect is reported without being executed.
- `.importlinter` has the six contracts from the Code Map. The layers contract's `name` is `AD-2 dependency direction (layers)` because the full ordering string wrapped in import-linter's output; the ordering is in a comment above it. The `cli` contract forbids every module except `runner` and `io` (including `errors` and `constants`, as the plan states) with `allow_indirect_imports = True`; the other forbidden contracts keep the default, which also catches indirect chains.
- `lint-imports` argv and skip rule untouched; the step now runs because the file exists. A unit test asserts the real repository root no longer yields a skip reason.

**Contract tensions observed (left as planned; for later stories to renegotiate if hit):** `testing` forbids `constants` and `io` including indirect chains, so `testing -> adapters` becomes a violation the moment `adapters` imports `io` (which the adapters contract allows). `adapters` forbids `redaction` while allowing `io`, and `io` allows `redaction`, so `adapters -> io -> redaction` would break the adapters contract. `cli` cannot import `agentproof.errors` directly; the error handler (AD-20) must take exceptions through the top-level public API (AD-15), which is the sanctioned indirect route. In the layers contract `constants` sits above `errors`, so `constants` may import `errors` but not the reverse.

**Observed on the real tree:** `cd packages/python && uv run check` exits 0 with `==> ruff check` / `All checks passed!` (purity silent), `==> ruff format --check` / `26 files already formatted`, `==> mypy --strict` / `Success: no issues found in 16 source files`, `==> lint-imports` / `Analyzed 16 files, 1 dependencies.` / all six contracts `KEPT` / `Contracts: 6 kept, 0 broken.`, `==> pytest` / `70 passed` (15 in `test_import_contracts.py`, 33 in `test_purity.py`, 11 in `test_check_entry_point.py`). `uv run lint-imports --config ../../.importlinter` alone: 6 kept, 0 broken. `uv build --wheel`: `agentproof-0.1.0.dev0-py3-none-any.whl` holds the same 16 `agentproof/` source files as story 1.1 plus the four dist-info entries, nothing from devtools. `mypy --strict devtools/src` plus the three new test files: clean (outside the gate, whose mypy covers `src` only).

**End-to-end with the real `run_steps` on a scratchpad copy of `packages/python` plus `.importlinter` (PYTHONPATH at the copy's `src`):** with `open("x")` and `Path("x").read_text()` in `engine/__init__.py` and `import agentproof.cli  # noqa: F401` in `models/__init__.py`, ruff passed and the step printed `src\agentproof\engine\__init__.py:3:1: purity: open`, `...:4:1: purity: Path('x').read_text`, `purity: 2 banned call(s) in core code (AD-1)`, `failed: ruff check exited 1`. With `engine` restored, the gate ran through ruff, format, and mypy, then `lint-imports` reported `AD-2 dependency direction (layers) BROKEN`, `nothing imports cli BROKEN`, `Contracts: 4 kept, 2 broken.`, `agentproof.models -> agentproof.cli (l.3)`, `failed: lint-imports exited 1`. A first attempt without `# noqa: F401` was stopped earlier by ruff's F401, which is why the injected statements in the test file that must get past ruff are written as used code or carry `# noqa`.

**Side effects and hygiene:** the real `lint-imports` step writes import-linter's default cache to `packages/python/.import_linter_cache/`; the temporary-copy tests pass `--no-cache`. That directory, `.ruff_cache`, `.mypy_cache`, `.pytest_cache`, `__pycache__`, and `dist` were removed after verification; story 1.5 should ignore `.import_linter_cache/`. `core.autocrlf=true` on this machine made git warn `LF will be replaced by CRLF` for the rewritten files; the index will hold LF as for every other file. The `Tasks & Acceptance` checkboxes were not ticked here; every listed task was implemented and verified as recorded above.

**Review fixes (2026-10-23, same session):** added a seventh forbidden contract `core imports no shell package` (source: the nine core packages; forbidden: `agentproof.io`, `agentproof.adapters`, `agentproof.runner`, `agentproof.cli`, `agentproof.testing`; `allow_indirect_imports = True`) and replaced the three pasted comments above the io, adapters, and testing contracts with one; `lint-imports --config ../../.importlinter --no-cache` now reports `Contracts: 7 kept, 0 broken.` and a new temp-copy test injects `import agentproof.io` into `engine/__init__.py` and asserts the contract breaks naming `agentproof.engine` and `agentproof.io`. Added the `os.stat` banned-api entry. The purity checker now splits lines on the tokenizer's newlines only (a regex for CRLF, CR, LF; `str.splitlines` also split on form feeds and shifted the suppression marker) and converts `col_offset` from UTF-8 bytes to a character column before adding 1, with a unit test covering both. The `lint-imports` argv gained `--no-cache` so the gate no longer writes `packages/python/.import_linter_cache/`, and `PURITY_TARGETS` now starts with `src/agentproof/__init__.py` (ten targets; `CORE_PACKAGES` stays the nine names); the tests asserting both argvs were updated. Verified with ruff check and format, `mypy --strict` on devtools and the three test files, and `pytest` on `test_check_entry_point.py`, `test_purity.py`, `test_import_contracts.py`: 61 passed.

## Plan Change Log

- 2026-10-23, review pass 1: the Quick lens found that no contract forbids a core package from importing `io`, `adapters`, or `testing` (AD-1 rule unenforced) and that the orchestrator's `allow_indirect_imports = True` on the `io`, `adapters`, and `testing` contracts contradicted the plan's Design Notes. Amended (non-frozen): the Code Map now lists a seventh forbidden contract "core imports no shell package"; the Design Notes now state that every forbidden contract allows indirect imports because the spine's allow-lists are direct-import rules and the layers contract governs transitive structure. Known-bad state avoided: a `.importlinter` that passes while `engine` imports `io`, and contracts that would fail on legal chains once real imports exist. KEEP: the layers contract as written, the purity checker inside the `ruff check` step, the temporary-copy test design.

## Review Triage Log

### Review pass 1 (quick lens), 2026-10-23

Verdicts: high 1, medium 3, low 3, false 0, maybe-false 0.

| Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| Core packages may import `io`, `adapters`, `testing` with every contract kept | high | patch | True: the six contracts source from the shell side only; a seventh forbidden contract from the nine core packages closes it, with a test case. Code Map amended (Plan Change Log). |
| `allow_indirect_imports = True` on `io`, `adapters`, `testing` contradicts the plan's notes | medium | patch (plan documentation) | True: the behavior is the intended one (direct-import rules; layers govern transitive structure); the Design Notes and Change Log now say so. The duplicated comment is collapsed to one. |
| `os.stat` from AD-1 is not banned | medium | patch | True: added to the banned-api table. |
| Suppression lookup uses `str.splitlines`, which disagrees with `ast` line numbers on form feeds | low | patch | True: direct correction to a newline-only split. |
| Column is a byte offset, documented as a character column | low | patch | True: converted to a character column. |
| The gate writes `.import_linter_cache` into the tree | medium | patch | True: `--no-cache` added to the step's argv; story 1.5 need not special-case it. |
| `src/agentproof/__init__.py` is covered by TID251 but not by the purity checker | low | patch | True: the top-level module is added to the purity targets. |

## Design Notes

Why a purity checker beside ruff: ruff's TID251 bans qualified import names, which covers `subprocess`, `socket`, `os.environ`, and friends, but a bare builtin call like `open(` and a method call like `Path.read_text()` are not imports. A twenty-line `ast` walk closes that gap without a new dependency and without type resolution; the cost is a known false-positive surface on attribute names like `replace` and `exists`, suppressible per line with `# purity: ok`, which the core packages are expected to hit rarely.

Why every forbidden contract sets `allow_indirect_imports`: the spine's allow-lists (AD-2) are direct-import rules, and the layers contract already governs transitive structure. With import-linter's default, legal chains such as `cli → agentproof → models` (once AD-15's public API exists), `testing → adapters → io`, and `io → redaction → models` would be reported as violations. The seventh contract, "core imports no shell package", enforces AD-1's rule that no core module imports `io`, `adapters`, `runner`, `cli`, or `testing`.

## Verification

**Commands:**
- `cd packages/python && uv run check` -- expected: `==> lint-imports` followed by import-linter's "Contracts: N kept, 0 broken", all five steps exit 0
- `cd packages/python && uv run lint-imports --config ../../.importlinter` -- expected: every contract KEPT
- `cd packages/python && uv run pytest -q tests/unit/test_import_contracts.py tests/unit/test_purity.py` -- expected: pass
- `cd packages/python && uv build && unzip -l dist/agentproof-*.whl` -- expected: same 16 source files as story 1.1

**Manual checks (if no CLI):**
- `git status` shows only the Code Map paths; no edits to `AGENTS.md` or `PROJECT_SPEC.md`.
