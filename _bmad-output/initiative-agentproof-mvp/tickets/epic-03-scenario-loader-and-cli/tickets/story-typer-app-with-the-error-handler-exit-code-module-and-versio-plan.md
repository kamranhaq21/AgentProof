---
title: 'Typer app with the error handler, exit-code module, and version command'
type: 'feature'
ticket: '1'
created: '2026-10-23'
status: done
baseline_revision: 'fca6286427e55f823cb7560090bf0c6a491eecc5'
route: 'full'
route_source: 'pinned'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Story 1.1 left `cli/app.py` as a Typer app with a bare `version` command and no error handling: an `InputError` escaping a command would print a traceback, an unexpected exception would exit 1, and nothing turns a `SuiteOutcome` or a `Comparison` into an exit code. Every later command needs the same three things once: the one exit site, the one error handler that maps the AD-7 taxonomy to the AD-6 codes, and the one exit-code module. `agentproof version` must also print the supported Schema Versions (PRD AC-30.2), and exit 4 must be reachable from a test through a fault-injection hook that is unreachable in normal use (PRD AC-27.1; AD-17).

**Approach:** `cli/app.py` is the only module that raises `typer.Exit`. A root callback holds the two AD-20 global options on `ctx.obj` as a `GlobalOptions`; a `_handled` decorator applied to every registered command maps `InputError` to one stderr line per `Violation` (`<kind>: <message> (<source>:<field>)`; one `<kind>: invalid input` line when the list is empty) and exit 2, `ExecutionError` to one line and exit 3, any other exception to one line and exit 4, with the traceback only under `--verbose` for 3 and 4. `cli/exit_codes.py` defines the five codes once as named constants and exposes `from_outcome` and `from_comparison` per AD-6. `version` lives in `cli/commands/version.py` and calls `cli.commands.inject_fault("cli.version")`, which raises `RuntimeError` only when `AGENTPROOF_TESTING=1` and `AGENTPROOF_FAULT_INJECT=cli.version`. The `.importlinter` `cli` contract is relaxed by exactly `errors`, `constants`, `models` (AD-2/AD-15 make them public API; epic 1 retrospective A5.2).

**Decisions delegated by the orchestrator (2026-10-23):** the contract relaxation; the version output format; violation `kind` = exception class name; review findings 1 to 10 of the rebuild (see Plan Change Log).

## Boundaries & Constraints

**Always:** `typer.Exit`, `sys.exit`, `os._exit`, `SystemExit` and any aliased or `click.exceptions.Exit` form appear only in `cli/app.py` (AST test); exit-code numbers are defined once in `cli/exit_codes.py` and `app.py` holds no literal 0 to 4; `cli` stays a shell package; no new exception class; the fault hook is one function in `cli/commands/__init__.py`, referenced only from `cli/commands/`; no core package reads the environment; every CLI test asserts the exit code; `mypy --strict` and `uv run check` green.

**Never:** no `validate`, `init`, `run`, `trace`, `compare`, `report` command; no changes to `constants.py`, `errors.py`, `models/*`, `agentproof/__init__.py`, devtools; no `io.console` or scrubber (story 3.5); no JSON from `version`; no `__init__.py` files under `tests/unit` or `tests/integration`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Single exit site (1) | AST of every `.py` under `src/agentproof` | exit calls/raises (`Exit`, `_exit`, `exit`, `quit`, `SystemExit`, aliases followed) only in `cli/app.py`; `app.py` raises `typer.Exit` in code | test names the offender |
| Two violations (2) | `SuiteError` with two violations | two stderr lines `SuiteError: <message> (<source>:<field>)`; exit 2; no traceback | `--verbose` adds nothing |
| Empty violations (2) | `InputError([])` | one line `InputError: invalid input`; exit 2 | none |
| Execution error (2) | `TraceMissingError("x")` | `TraceMissingError: x`; exit 3 | `--verbose` appends traceback |
| Unexpected (2) | `RuntimeError("boom")` | `internal error: RuntimeError: boom (re-run with --verbose for the traceback)`; exit 4 | `--verbose`: no hint, traceback follows |
| Secret in exception text | planted value in an exit 3/4 message, traceback, or violation | today printed as is (story 3.5 scrubs) | strict `xfail` tests pin the gap |
| `from_outcome` (3) | `execution_failed` → 3; `failed`/`error`/`evaluated_assertions == 0` → 1; else 0 | per AD-6 | pure |
| `from_comparison` (3) | `regressed` → 1, else 0 | per AD-6 | pure |
| `version` (4) | `agentproof version` | `agentproof <v>`, `suite schema versions: 1`, `trace schema versions: 1`, `report schema versions: 1`; exit 0 | none |
| Option placement | `agentproof version --verbose` | click usage error, exit 2 | pinned |
| Fault injection (5) | `AGENTPROOF_TESTING=1` + `AGENTPROOF_FAULT_INJECT=cli.version` | one line, exit 4 | without `AGENTPROOF_TESTING=1` (or any value but `1`) ignored |

</frozen-after-approval>

## Code Map

- `packages/python/src/agentproof/cli/app.py` -- rewritten: `GlobalOptions` on `ctx.obj`, `_root(context, verbose, no_color)`, `_handled` (adds a keyword-only `typer.Context` parameter to the wrapper signature so Typer injects the context), registration, `main()`.
- `packages/python/src/agentproof/cli/exit_codes.py` -- new: `EXIT_OK/FAILED/INPUT_ERROR/EXECUTION_ERROR/INTERNAL_ERROR`, `from_outcome`, `from_comparison`; `__all__` is the two functions.
- `packages/python/src/agentproof/cli/commands/__init__.py` (`inject_fault`), `commands/version.py` (`format_version`, `version`) -- new.
- `packages/python/tests/unit/cli/test_exit_codes.py`, `test_single_exit_site.py`, `test_error_handler.py`, `test_fault_hook_reach.py`; `tests/integration/cli/test_version_and_errors.py` -- new (no `__init__.py`).
- `packages/python/tests/unit/test_cli_version.py`, `tests/integration/test_install_smoke.py` -- updated to the new surface, not weakened.
- `packages/python/pyproject.toml` -- `addopts = ["--import-mode=importlib"]` and the `allow_subprocess` marker.
- **Code Map exception (contract):** `.importlinter` (`cli` contract: `errors`, `constants`, `models` removed from `forbidden_modules`, renamed) and `tests/unit/test_import_contracts.py` (negative test now injects `engine`; new test reads the contract).
- **Code Map exception (CI):** `.github/workflows/ci.yml` smoke step compares `head -n1` of `agentproof version` with `agentproof $expected`; `tests/unit/test_workflow_pins.py` asserts it.
- **Code Map exception (deferred work):** `_bmad-output/initiative-agentproof-mvp/deferred-work.md` gains one entry routing exit-3/4 and violation-message scrubbing to story 3.5.

**Decisions for review:** (1) violation `kind` is the exception class name; (2) empty `field` drops `:<field>`; (3) exit-4 hint text; (4) `version` first line is `agentproof <version>`; (5) the exit constants are module attributes of `exit_codes` outside `__all__`, so the module still exposes exactly the two functions as its API; (6) `pretty_exceptions_enable=False`.

## Tasks & Acceptance

**Execution:**
- [x] `.importlinter` + `test_import_contracts.py` -- relax the `cli` contract
- [x] `cli/exit_codes.py` + `test_exit_codes.py` -- criterion 3
- [x] `cli/commands/` + `cli/app.py` -- criteria 2, 4, 5
- [x] `test_single_exit_site.py`, `test_error_handler.py`, `test_fault_hook_reach.py`, `test_cli_version.py` -- criteria 1, 2, 4, 5
- [x] `tests/integration/cli/test_version_and_errors.py`, `test_install_smoke.py`, `ci.yml`, `test_workflow_pins.py`, `pyproject.toml`
- [x] `deferred-work.md` entry
- [x] local verification

**Acceptance Criteria:** the five criteria of the story (single exit site; error handler; exit-code module; `version` and `--help`; fault injection).

## Implementation Notes

**2026-10-23, implementer, rebuild (the first worktree was destroyed by an environment restart before any commit; this is a from-scratch rebuild on `story/3-1-cli-skeleton`, baseline `fca6286`, with the coordinator's ten review findings applied).**

- Handler: `_handled` is a decorator applied at registration. Typer 0.27 vendors click (`typer._click`) and exposes no `get_current_context`; to avoid a direct `click` import the wrapper's `__signature__` and `__annotations__` gain a keyword-only `typer.Context` parameter, which Typer injects. Typer injects the base `typer._click.core.Context` (not the `typer.models.Context` subclass), so the code `cast`s rather than `isinstance`-checks (the first run failed on exactly that assertion). The root callback sets `context.obj = GlobalOptions(...)`; the handler reads it with `find_object`, so there is no module state (`test_options_live_on_the_context_and_never_leak_between_invocations` asserts `_options` is gone and alternates `--verbose` runs).
- Finding 1: `InputError([])` prints `InputError: invalid input`, exit 2 (`test_an_input_error_with_no_violations_still_prints_one_line_and_exits_2`).
- Finding 2: five strict `xfail` cases (`test_a_planted_secret_never_reaches_the_output`) cover exit 3, exit 4 with and without `--verbose`, and a violation message; the gap is stated in the `app.py` docstring and routed to story 3.5 in `deferred-work.md`.
- Finding 3: the exit-site test walks the AST (Raise and Call nodes naming `Exit`, `_exit`, `exit`, `quit`, `SystemExit`; `from x import Exit as Alias` followed); eleven bypass snippets must be caught and three lookalikes (docstring text, `exit_codes.from_outcome`, `EXIT_INPUT_ERROR`) must not; `app.py` must contain `raise typer.Exit(...)` as a Raise node and no `sys.exit`/`exit`/`quit`/`os._exit` call or `SystemExit` raise.
- Finding 4: constants live only in `exit_codes.py`; `test_the_codes_are_defined_once_and_app_py_has_no_literal_code` asserts no int constant 0 to 4 in `app.py` and no `EXIT_*` assignment elsewhere in `cli/`.
- Finding 5: the module docstring and root help say the options precede the command; `test_global_options_after_the_command_are_a_usage_error_today` (in-process) and `test_a_global_option_after_the_command_is_a_usage_error_with_exit_2` (subprocess) pin exit 2.
- Finding 7: `addopts = ["--import-mode=importlib"]` replaces `__init__.py` files; `tests/unit/models/__init__.py` (pre-existing) is untouched. Full `uv run pytest` collects and passes (below).
- Finding 8: `test_fault_hook_reach.py` scans the whole `src/agentproof` tree: the hook names appear only in `cli/commands/__init__.py` and `version.py`; strings starting `AGENTPROOF_` only in the hook module; no core package (devtools `CORE_PACKAGES` plus the top-level `__init__`) reads `environ`/`getenv`; none imports `agentproof.cli`.
- Finding 9: AD-6 mapping unchanged: `execution_failed` 3; else `failed`/`error`/`evaluated_assertions == 0` 1; else 0; `regressed` 1 else 0. `.importlinter` relaxation unchanged. Finding 10: ci.yml smoke step and its pin test as before.

Observed (from `packages/python`, uv 0.13.5, CPython 3.13.16 unless noted):

- `uv run check`: `ruff check` "All checks passed!"; `ruff format --check` "54 files already formatted"; `mypy --strict` "Success: no issues found in 26 source files"; `lint-imports` "Contracts: 7 kept, 0 broken." (`cli imports only runner, io, errors, constants, models KEPT`); `pytest` "821 passed, 5 xfailed in 64.70s"; exit 0.
- `uv run pytest -q -p no:cacheprovider` (full suite, importlib mode): "821 passed, 5 xfailed in 58.27s".
- `uv run --python 3.12 --locked --isolated pytest tests/unit/cli tests/integration -q -p no:cacheprovider`: "62 passed, 5 xfailed in 38.29s".
- Not run: Python 3.14 and 3.15, Linux (CI covers them).

Risks: the `.importlinter` relaxation is the architect's call (epic 1 retrospective A5.2); `--no-color` governs only the handler's lines until 3.5; the `allow_subprocess` marker has no conftest guard behind it yet (AD-17), and `test_install_smoke.py` and `test_import_contracts.py` also spawn processes unmarked.

## Plan Change Log

- 2026-10-23 (coordinator, rebuild): ten review findings baked in from the start: empty-violations line, scrub-gap xfail tests plus deferred-work entry, AST exit-site test, single-sourced exit constants, documented and pinned option placement, `ctx.obj` options, `importlib` import mode instead of `__init__.py` files, whole-tree fault-hook reach test, AD-6 mapping and `.importlinter` relaxation kept, ci.yml smoke change kept.

## Review Triage Log

## Verification

**Commands:**
- `cd packages/python && uv run check`
- `cd packages/python && uv run pytest`
- `cd packages/python && uv run --python 3.12 --locked --isolated pytest tests/unit/cli tests/integration -q -p no:cacheprovider`
