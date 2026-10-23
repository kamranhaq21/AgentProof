---
title: 'Size-limited reading and parse_suite with every violation'
type: 'feature'
ticket: '3'
created: '2026-10-23'
status: done
baseline_revision: '39307b3b9675020011ab62dc231c05b36c6babd3'
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

**Problem:** The package can turn Suite text into a dict (story 3.2) and validate a dict into a `Suite` (epic 2), but nothing joins them, nothing reads a file with a size limit and a symlink policy, and `Violation.field` means `line:column` from the YAML loader and a dotted path everywhere else (deferred-work entry routed to this story). A user must see every fault in a Suite in one pass (epic 3 R1; PRD FR-1 to FR-3, AC-1.2, AC-2.1 to AC-2.4, AC-3.1 to AC-3.3, AC-28.1; spine AD-14, AD-15, AD-19).

**Approach:** `io.read_limited(path, max_bytes, *, base_dir)` (shell) resolves the path, refuses one whose real path is outside `base_dir`'s real path (`PathError` naming the escape), checks `stat` size and refuses an oversize file before any content is read (`PathError` naming the limit; the read itself is capped at `max_bytes + 1`), and decodes strict UTF-8 (`PathError` naming the byte offset). `loading.suite.parse_suite(text, *, source)` (core) runs `yaml_safe.load`, lets its `SuiteError` propagate unchanged, then `Suite.model_validate`, converting every Pydantic error into a `Violation` in one `SuiteError`. `load_suite(path, *, base_dir=None)` (shell) is `read_limited` with `MAX_SUITE_BYTES` then `parse_suite(text, source=str(path))`.

**Decisions taken by the implementer (2026-10-23):**

1. `Violation.field` convention: a field that fully matches `\d+:\d+` is a 1-based `line:column` text position (YAML loader only); any other non-empty field is the dotted model path (`scenarios.1.id`, 0-based indexes, from validation only); empty is the whole document. The two never mix in one `SuiteError` because validation runs only on text that loaded cleanly. Comment-only update of the `Violation` docstring in `errors.py` (no behavior change). Known edge: an unknown top-level key literally spelled like `1:2` renders as a path that matches the position pattern; accepted, documented.
2. Violation order: sorted by path, element by element; list indexes numerically, names as strings, a name sorts after an index; ties keep Pydantic's order. Independent of Pydantic's traversal order.
3. `load_suite` lives in `runner/suite_file.py`, not `loading/suite.py`: `loading` is core and `.importlinter` (`core-imports-no-shell`) forbids it importing `io`; AD-15 says `load_*` are shell. Runner may import `io` and sits above `loading` (AD-2).
4. `base_dir` default: the Suite file's own parent directory (AD-14: no symlink following outside the Suite directory); callers may pass a wider one.
5. `__all__` placement: AD-15 says the public API is exactly `agentproof.__all__` and lists `parse_suite` and `load_suite`, so both are exported at the top level, which changes the pin in `test_version.py` (moved to `tests/unit/test_public_api.py`). `read_limited` is not in AD-15's list; it is exported from `agentproof.io.__all__` only (internal before 1.0). `PathError` is reached through the public `errors` module.
6. A JSON value nested too deeply for Pydantic (deferred F3: about 500 union-branch errors) collapses to one violation `a value is nested too deeply to validate` at the value's path; a bare `RecursionError` from validation becomes one violation with an empty field.
7. `cli/app.py` is not changed: `_handled` already prints `SuiteError: <message> (<source>:<field>)` per violation (kind = class name); a CliRunner test confirms it for a three-violation SuiteError.
8. `tests/unit/io/` has no `__init__.py`: a package named `io` on the test path would shadow the stdlib `io` (pytest runs in importlib mode and the epic forbids `__init__.py` files under `tests/unit` where avoidable).

## Boundaries & Constraints

**Always:** `loading` stays pure (no I/O, no shell imports); `io` imports only `errors`, `constants`, `redaction`; YAML only through `yaml_safe.load`; no file content in any message; LF files; `mypy --strict`; `uv run check` green.

**Never:** no change to `models/*`, `constants.py`, `.importlinter`, `yaml_safe.py`, or `cli/app.py`; no command wiring (story 4); no new runtime dependency.

</frozen-after-approval>

## Code Map

- `packages/python/src/agentproof/io/artifacts.py` -- new; `read_limited`.
- `packages/python/src/agentproof/io/__init__.py` -- exports `read_limited`.
- `packages/python/src/agentproof/loading/suite.py` -- new; `parse_suite`.
- `packages/python/src/agentproof/runner/suite_file.py` -- new; `load_suite` (see decision 3).
- `packages/python/src/agentproof/__init__.py` -- exports `parse_suite`, `load_suite`.
- `packages/python/src/agentproof/errors.py` -- docstring-only exception: the `Violation.field` convention.
- `packages/python/tests/unit/io/test_read_limited.py`, `tests/unit/loading/test_parse_suite.py`, `tests/unit/test_public_api.py`, `tests/unit/test_version.py` (pin moved).

## Tasks & Acceptance

**Execution:**
- [x] `io/artifacts.py`, `io/__init__.py` -- `read_limited` -- criterion 1
- [x] `loading/suite.py` -- `parse_suite` with ordering and depth collapse -- criterion 2
- [x] `runner/suite_file.py`, `__init__.py` -- `load_suite`, exports -- criterion 3
- [x] `errors.py` -- docstring convention
- [x] tests for all four criteria (criterion 4 via CliRunner and the real `_handled`)
- [ ] orchestrator: commit, review, PR

**Acceptance Criteria:** the four criteria of the story.

## Implementation Notes

**2026-10-23, implementer (worktree `D:\AgentProof-wt-3-3`, branch `story/3-3-parse-suite`, baseline `39307b3`).** Decisions 1 to 8 above are the decisions taken.

Observed:
- `uv run check` from `packages/python`, exit 0: `1202 passed, 3 skipped, 14 xfailed` (ruff, format, mypy --strict, lint-imports passed; an earlier run failed ruff E402 in a test, fixed).
- `uv run --python 3.12 --locked --isolated pytest tests/unit/io tests/unit/loading tests/unit/test_public_api.py -q -p no:cacheprovider` -> `235 passed, 3 skipped`.
- The 3 skips are symlink tests: this Windows account cannot create symlinks. The `..` escape and sibling-prefix tests exercise the same containment code; symlink tests run on POSIX CI.
- `tests/unit/io/__init__.py` shadowed stdlib `io` and broke typer's import, so it was removed (decision 8).
- Deep-nesting probe (150 levels): Pydantic yields 496 errors (99 each of five scalar types plus one `recursion_loop`); collapsed to one violation (decision 6).

## Review Triage Log

Review verdict: no blocking issues; the `__all__`, `Violation.field` convention and ordering decisions confirmed correct. The coordinator passed me findings 1 to 3 and a verdict for 4 to 6; I did not receive the text of 4 to 6.

| # | Finding | Disposition |
| --- | --- | --- |
| 1 | The `max_bytes + 1` capped read in `read_limited` had no test proving it is a real second guard. | Patched: `test_a_file_that_outgrows_its_stat_size_is_still_refused` fakes `Path.stat` to report 64 bytes for a 200-byte file and asserts the "over the limit of 64 bytes" refusal (the message only the capped read produces). |
| 2 | `load_suite` tests sat in `tests/unit/loading/` though the module is `runner/suite_file.py`. | Patched: moved to `tests/unit/runner/test_suite_file.py` (no `__init__.py`). |
| 3 | TOCTOU between the containment check and the open is undocumented. | Patched: one paragraph in the `read_limited` docstring; accepted limit for a local CLI, not fixed. |
| 4 | `Violation.field` ambiguity is real: a quoted unknown key `"1:2"` yields the same shape as a yaml_safe position. | No action: the only consumer, `cli/app.py`'s formatter, just joins `source:field` and never branches on the shape, so nothing downstream is misread. Noted in the errors.py docstring already. |
| 5 | Name ordering is alphabetical, not declaration order; the "a name sorts after an index" tie-break is effectively unreachable since a real Suite never mixes ints and names at the same path position. | No action: matches the documented rule; the unreachable tie-break is harmless. |
| 6 | `_value_root` cuts the path at the first string part that is a union tag, which could coincide with a user key literally named `str`, `int`, `none`, etc. | No action: the collapse only ever fires under a `recursion_loop` root, so an unrelated coincidentally-named key is never affected. |

Risks: an unknown top-level key spelled `1:2` is ambiguous with a position (decision 1); `_value_root` relies on Pydantic's union-branch labels (`list[`, `dict[`, `bool`, ...); a rename would only lose the collapse, not correctness.
