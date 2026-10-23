---
title: 'Console scrubber and logging filter'
type: 'feature'
ticket: '5'
created: '2026-10-23'
status: in-progress
baseline_revision: 'ec8fbb6b5fd85438398a16ec25ec02134c8dc29b'
route: 'full'
route_source: 'pinned'
risk: 'medium'
context: []
---

## Intent

**Problem:** Nothing the CLI prints may contain a declared secret (PRD AC-28.2; AGENTS.md policy), but story 3.1's error handler prints exception text, tracebacks, and violation messages as they are, pinned by strict `xfail` tests and a `deferred-work.md` entry owned by this story.

**Approach:** `redaction.scrub_text` (AD-10, the one scrubber, shared with epic 5's `redact`) plus `io.console`: a print path that renders to final text and scrubs that, a `logging.Filter` installed by `io.console.install()`, wired into the root callback and the handler's `_echo_error`.

## Boundaries & Constraints

**Always:** `redaction` stays core (pure, imports `constants` only); `io` may import `redaction` (`.importlinter` `io` contract); `cli` reaches `redaction` only through `io.console` (the `cli` contract forbids a direct import); no new runtime dependency (`rich` is already one); `app.py` edits are additive.

**Never:** no `redact` for Traces (epic 5); no change to the single-exit-site rule or the exit codes; no new exception class.

## Code Map

- `src/agentproof/redaction/apply.py` (new: `scrub_text`), `redaction/__init__.py` (exports it).
- `src/agentproof/io/console.py` (new: `set_secret_values`, `secret_values`, `scrub`, `render`, `echo`, `ScrubFilter`, `install`, `uninstall`).
- `src/agentproof/cli/app.py`: three additive edits (import, `_echo_error` body, one `console.install(...)` line in `_root`) and a docstring paragraph.
- `tests/unit/redaction/test_scrub_text.py`, `tests/unit/io/test_console.py`, `tests/integration/cli/test_no_color.py` (new); `tests/unit/cli/test_error_handler.py` (the strict `xfail` on `test_a_planted_secret_never_reaches_the_output` removed; the leaking commands call `console.set_secret_values`).
- `_bmad-output/initiative-agentproof-mvp/deferred-work.md`: the story 3.1 entry marked closed.

## Tasks & Acceptance

- [x] `scrub_text` + tests (criterion 1)
- [x] `io.console` print path, render-then-scrub, tests including the styled-span probe (criterion 2)
- [x] `ScrubFilter` + `install`, core-emits-no-records test (criterion 3)
- [x] `app.py` wiring; `--no-color` and `--verbose` end to end (criterion 4)
- [x] flip the 3.1 xfail tests; close the deferred-work entry
- [x] `uv run check` green; 3.12 isolated run

## Implementation Notes

**2026-10-23, implementer.**

Decisions:

- **Secret-value source.** v0.1 has no real source before epic 5's runner resolves `redact.env`. `io.console` holds a module-level tuple set by `set_secret_values(values)`; `install(secret_values=(), *, verbose=False)` resets it, and the root callback calls `console.install((), verbose=verbose)`. The runner will call `set_secret_values` after resolving values and before reading any Trace. Module state is deliberate (a logging filter and the error handler both need it without a context) and `install` resets it so values never survive into the next in-process invocation. The 3.1 tests plant their secret by calling `set_secret_values` inside the leaking command, which is what the runner will do.
- **Render, then scrub.** Rich markup splits a value across spans (`[bold]sk-live-[/bold][red]planted-secret-value[/red]`), and word wrap or table borders can break it across lines, so neither the markup source nor the ANSI output can be scrubbed reliably. `render` first draws the renderable as plain text on a 100,000-column console (no wrapping, no styles) and scrubs that. If the scrub changed anything, that scrubbed plain text is the output (styling lost for that print, redaction never). Otherwise the normal rendering (80 columns, styled only when the stream is a tty and `--no-color` is off) is emitted; a rendering with no contiguous secret in the unwrapped plain text cannot have one in the wrapped one (wrapping only inserts characters). The probe test asserts the source scrub misses the value (`scrub_text(markup) == markup`) and `render` does not, with color on and off.
- **Plain strings never wrap** (`soft_wrap` for `str`): the handler's lines stay one line per message, as story 3.1's tests require. Strings print with `markup=False` by default.
- **Logging.** `ScrubFilter(logging.Filter)` formats the message (`getMessage()`), clears `args`, and scrubs `exc_text` (formatted from `exc_info` first, since the formatter would otherwise format the unscrubbed traceback later) and `stack_info`. A filter on a handler applies to every record that handler emits; a filter on a logger does not apply to child loggers, so `install` adds the filter to each handler already on the root logger and to one stderr `StreamHandler` it owns, and `uninstall` removes only what it added. The class lives in the shell (`io.console`); `logging` is not banned anywhere (TID251 lists no `logging`).
- **`scrub_text` uses `split`/`join`, not `str.replace`**: the devtools purity checker bans the name `replace` (it cannot tell `str.replace` from `Path.replace`). Empty values are skipped; values are deduplicated and applied longest first.
- **Closing the 3.1 deferred item.** `_echo_error` is the single place the handler prints, so routing it through `console.echo` scrubs exit 3 and 4 lines, tracebacks (one string, scrubbed whole, so a secret in a chained exception is covered), and violation lines. The five strict-xfail cases now pass as plain tests (also asserting the exit code is nonzero and the marker appears).
- **Scope not covered:** typer/click's own usage-error rendering (`BadParameter` etc.) does not pass through `_echo_error` and is not scrubbed; it prints what the user typed on the command line. Noted in the report, not changed (it would need a custom click exception hook and a story of its own).

Observed (from `packages/python`, uv 0.13.5, CPython 3.13):

- `uv run check`: ruff "All checks passed!", format "77 files already formatted", mypy "Success: no issues found in 33 source files", lint-imports "Contracts: 7 kept, 0 broken.", pytest "1234 passed, 3 skipped, 9 xfailed in 144.03s".
- `uv run --python 3.12 --locked --isolated pytest tests/unit/redaction tests/unit/io tests/integration/cli/test_no_color.py tests/unit/cli -q -p no:cacheprovider`: "86 passed, 2 skipped in 13.55s".

Risks: module-level secret state is process-global (one CLI invocation per process in practice); `FORCE_COLOR`/`CLICOLOR_FORCE` are ignored on purpose (color only on a tty, never under `--no-color`).

**2026-10-23, implementer, review follow-up.** Superseding notes: `scrub_text` no longer applies values sequentially (the "applied longest first" sentence above is replaced by the span-merge rule of finding 1). The shipped CLI's scrubber is currently a no-op: `_root` installs an empty secret set, so only the wiring is live until epic 5's runner calls `set_secret_values` (finding 6; also a comment at the call site).

Observed after the follow-up (`packages/python`, CPython 3.13): `uv run check` green (ruff, format "77 files already formatted", mypy "no issues found in 33 source files", lint-imports "7 kept, 0 broken", pytest "1239 passed, 3 skipped, 9 xfailed in 160.52s"); 3.12 isolated run "91 passed, 2 skipped".

## Review Triage Log

| # | Finding | Disposition |
| - | ------- | ----------- |
| 1 | `scrub_text` leaked a fragment when two values overlap without containment (`abcXY`/`XYdef`), and the result depended on set iteration order | Fixed. All occurrences of all values are located in the original text (overlapping occurrences included), overlapping or touching spans merge, each merged span becomes one marker. Tests: `test_overlapping_values_leave_no_fragment_of_either_in_any_order`, `test_overlap_result_does_not_depend_on_the_hash_seed` (subprocess with `PYTHONHASHSEED` 0 to 3 and random), `test_touching_spans_merge_and_a_chain_of_overlaps_collapses`. Side effect: two touching occurrences print one marker, not two. |
| 2 | Secret only in styled-path data (OSC-8 `[link=...]` target) passes the plain check | Fixed by scrubbing the styled string too; on any hit `render` falls back to the unstyled rendering (already cleared by the plain check). Test: `test_a_secret_only_in_link_metadata_is_scrubbed_from_styled_output` (shows the target is present without a secret set, absent with one). |
| 3 | Escaped or encoded forms (repr, json, unicode-escape) are not matched | Deferred, `deferred-work.md`. |
| 4 | Logging filter misses later handlers, `propagate=False` loggers with own handlers, and `extra={}` | Deferred, `deferred-work.md`. |
| 5 | `test_the_core_emits_no_log_records` overclaims | Fixed. Docstring says it is sampled evidence for `canonical.dumps` and `yaml_safe.load`; added `test_no_core_module_imports_logging`, an AST scan of every core package module and the top level. |
| 6 | Scrubber is a no-op in the shipped CLI | Documented here and by a comment at the `console.install((), ...)` call site in `_root`. |
| 7 | Typer/click usage-error rendering bypasses `_echo_error` | Deferred, `deferred-work.md` (unreachable today). |
| 8 | Tests could leak secret state or the owned stderr handler into later tests | Fixed. Autouse fixture in `tests/unit/cli/test_error_handler.py` calls `console.uninstall()` and asserts `console.secret_values() == ()` (`uninstall` clears the tuple via `set_secret_values(())`); `test_console.py` already had one. |

## Verification

**Commands:**
- `cd packages/python && uv run check`
- `cd packages/python && uv run --python 3.12 --locked --isolated pytest tests/unit/redaction tests/unit/io tests/integration/cli/test_no_color.py tests/unit/cli -q -p no:cacheprovider`
