---
title: 'validate command end to end'
type: 'feature'
ticket: '4'
created: '2026-10-23'
status: in-progress
baseline_revision: 'ec8fbb6b5fd85438398a16ec25ec02134c8dc29b'
route: 'full'
route_source: 'pinned'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Stories 1 to 3 built the error handler, the safe YAML loader, and `load_suite`, but no command uses them. The first command a user runs on their own file proves the three together (epic 3 R3, R4; PRD FR-2, AC-2.4, AC-28.1, AC-28.3; spine AD-20).

**Approach:** `agentproof validate SUITE_PATH` is a plain function in `cli/commands/validate.py` registered with `app.command("validate")(_handled(validate))`, the same one-line pattern as `version`. It calls `runner.load_suite` and prints one line on stdout. It catches nothing: `SuiteError` (malformed Suite, YAML-safety fault) and `PathError` (missing, unreadable, escaping, oversize, non-UTF-8 file) are both `InputError` subclasses (checked in `errors.py`), so the existing `_handled` branch prints one `<kind>: <message> (<source>:<field>)` line per violation and exits 2 with no traceback. The error shape of story 1 is untouched.

**Decisions taken by the implementer (2026-10-23):**

1. Success line, exact: `suite <id>: <n> scenarios, <m> assertions` on stdout, newline-terminated, nothing on stderr. Neither the spine nor the PRD fixes a string (AD-20 only says Suite id and counts; story criterion 1 names the three values). Nouns always plural (`1 scenarios`) so a script matches one pattern, as `version` does for its fixed text. `<m>` counts Assertions across all Scenarios, skipped ones included, because `validate` evaluates nothing. Nothing is printed on stdout on failure.
2. Argument: `SUITE_PATH` (AD-20 spelling), `typer.Argument(metavar="SUITE_PATH")`, type `Path`, no `exists=True` (that would make Typer print its own usage error with a different shape; the missing file must reach `load_suite` so `PathError` names the path in the shared shape).
3. Help: the docstring has a summary, a paragraph on the output, and an `Exit codes:` block with one short line per code (0, 2, 4). Probed: Typer's help keeps single newlines in a docstring as hard breaks (it does not rejoin wrapped source lines), so lines are kept under about 56 characters and each code sits on its own line; the help then reads cleanly at 60 and 200 columns and no `noqa` is needed (revised after review).
4. No fault-injection point in `validate`: `test_fault_hook_reach.py` allows exactly `version.py` to name the hook, and exit 4 is already covered by `version`'s fault test through the same `_handled` wrapper. Exit 4 appears in the help because AD-6 applies to every command.
5. `app.py` change is two lines (an import and the registration line after `version`); story 3.5 edits the same file concurrently.
6. Existing test `test_an_unknown_command_is_a_usage_error_with_exit_2_and_no_traceback` used `validate` as its example of an unknown command. It now uses `frobnicate`; its assertions are otherwise unchanged.
7. Tests are subprocess-only for the command (the story names it); the in-process error-handler behavior is already pinned by `tests/unit/cli/test_error_handler.py`, so no new CliRunner test was added.

## Boundaries & Constraints

**Always:** `cli/commands/validate.py` raises no exit and prints no error itself; LF files; `mypy --strict`; `uv run check` green.

**Never:** no change to the error shape, `_handled`, `exit_codes.py`, `errors.py`, or `loading/*`; no new runtime dependency; no output file written.

</frozen-after-approval>

## Code Map

- `packages/python/src/agentproof/cli/commands/validate.py` -- new; `validate`, `format_summary`.
- `packages/python/src/agentproof/cli/app.py` -- import plus `app.command("validate")(_handled(validate))` after `version`.
- `packages/python/tests/integration/cli/test_validate.py` -- new; criteria 1 to 4.
- `packages/python/tests/integration/cli/test_version_and_errors.py` -- the unknown-command example renamed (decision 6).

## Tasks & Acceptance

**Execution:**
- [x] `cli/commands/validate.py` -- command and summary format -- criteria 1, 4
- [x] `cli/app.py` -- one-line registration -- criteria 1 to 4
- [x] `tests/integration/cli/test_validate.py` -- subprocess tests over the 14 malformed fixtures, a valid seed, a missing file, help -- criteria 1 to 4
- [x] `test_version_and_errors.py` -- unknown-command example
- [ ] orchestrator: commit, review, PR; merge with story 3.5's `app.py` edit

**Acceptance Criteria:** the four criteria of the story.

## Implementation Notes

See the dated entry appended below by the implementer.

**2026-10-23, implementer (worktree `D:\AgentProof-wt-3-4`, branch `story/3-4-validate-command`, baseline `ec8fbb6`).** Decisions 1 to 7 above are the decisions taken.

Additional decisions:
- Adding `validate` broke two tests that pinned "only `version`": `tests/unit/test_cli_version.py` (renamed `test_help_lists_the_registered_commands`, expects `["version", "validate"]`) and `tests/integration/test_install_smoke.py` (renamed `test_help_lists_the_registered_commands_and_the_global_options`, expects `["validate", "version"]` sorted). The smoke test `test_unknown_command_exits_nonzero` also used `validate` and now uses `frobnicate`. Story 3.5 may touch none of these; if the merge conflicts on them, keep both commands.
- `SuiteError` and `PathError` are both `InputError` subclasses (errors.py); `load_suite` raises `PathError` for a missing file (`the file does not exist (<path>)`) and `SuiteError` for YAML-safety and validation faults.

Fixtures tested (all exit 2, exactly one stderr line, no traceback): `tests/fixtures/schema/v1/invalid/suite__*.json` (6: duplicate_assertion_id, duplicate_scenario_id, extra_forbidden, literal_error, missing, too_short) and `tests/fixtures/yaml/*.yaml` except the seed (8: anchor-alias, billion-laughs, custom-tag, duplicate-key-nested, duplicate-key-top-level, multi-document, python-object-tag, scalar-top-level). Inline: a three-violation Suite (3 lines, in path order), an unknown assertion type, an unclosed flow sequence, an empty file, a directory path.

Observed:
- `uv run check` from `packages/python`, exit 0: `1231 passed, 3 skipped, 14 xfailed` after the review fixes (first run 1230; ruff, format, mypy --strict, lint-imports 7 kept). An earlier run failed the two pinned tests above, fixed.
- `uv run --python 3.12 --locked --isolated pytest tests/integration/cli/test_validate.py tests/unit/cli -q -p no:cacheprovider` -> `71 passed, 5 xfailed` after the review fixes.
- Manual: seed -> `suite expense-agent: 1 scenarios, 3 assertions`, exit 0.
- The full check took very long wall-clock while other worktrees ran hypothesis tests concurrently; not a defect of this change.

Risks: the plural-always wording (`1 scenarios`) may read oddly; documented as deliberate.

## Review Triage Log

Review (coordinator, 2026-10-23) returned 8 findings.

| # | Finding | Disposition |
| --- | --- | --- |
| 1 | `# noqa: E501` on the help docstring hid a wrapping problem; tests only ran at COLUMNS=200. | Patched: docstring rewritten as short lines, one per exit code, noqa removed. Probe showed Typer does NOT rejoin wrapped source lines (hard breaks), so the lines were shaped to read well at any width. New test `test_help_at_a_narrow_width_still_pairs_each_exit_code_with_its_meaning` (COLUMNS=60). |
| 2 | The help assertion matched any digit near "Exit codes:". | Patched: `_assert_exit_codes_paired` requires `0 the Suite is valid.`, `2 the file is missing, unreadable, or not a valid Suite` and `4 internal error.` in order, on whitespace-normalised text. |
| 3 | Windows reserved-device-name wording. | No action: out of scope (confirmed by coordinator). |
| 4 | Untested PathError branches for criterion 3. | No action: covered below the CLI in `tests/unit/io/test_read_limited.py` (confirmed). |
| 5 | Confirmed correct. | No action. |
| 6 | `test_cli_version.py` command-set assertion depended on registration order. | Patched: `sorted(get_command(app).commands) == ["validate", "version"]`, matching the smoke test. |
| 7 | Confirmed correct. | No action. |
| 8 | Confirmed correct. | No action. |
