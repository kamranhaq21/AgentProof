---
title: 'Constants, errors, common types, and the Canonical serializer'
type: 'feature'
ticket: '1'
created: '2026-10-23'
status: 'built'
baseline_revision: '037860bff77ad0fedf08d0a08b3707002d3cafdb'
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

**Problem:** The bottom of the core is empty: no shared constants, no error taxonomy, no JSON value or status types, and no serializer, so nothing above them can be built and the byte-identity promise (PRD NFR-1) has no implementation to test (story 2.1, epic 2 R4 and R6).

**Approach:** Fill `agentproof.constants`, `agentproof.errors`, `agentproof.models.common`, and `agentproof.models.canonical` exactly as the architecture spine specifies (AD-3, AD-7, AD-10, AD-11, AD-14, AD-19, AD-20), commit the first golden file, and add tests for every rule, including a test that no module outside `errors.py` defines an exception class and a byte-identity golden test that runs on both CI platforms.

**Decisions delegated by the maintainer (2026-10-22, "approve all, you are the owner"):** `STATEMENTS` is a frozen dataclass instance with named string fields (not a dict) so references are attribute lookups mypy can check; `JsonValue` is declared with the Python 3.12 `type` statement; size limits are the PRD's 5 MB per file (OQ-12); `VOLATILE_PATHS` is a tuple of path-pattern strings exactly as the spine lists them.

## Boundaries & Constraints

**Always:** These four modules import only the standard library and each other in the direction `errors` → `constants` → `models.common` → `models.canonical` (AD-2); they use none of the names AD-1 bans (the purity checker and TID251 apply to them); `dumps` output is `json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"`; `dumps_compact` uses `separators=(",", ":")`, sorted keys, `ensure_ascii=False`, `allow_nan=False`; files written by tests use explicit UTF-8 and LF; every public name has a docstring; `mypy --strict` passes on `src`.

**Never:** No Pydantic models yet (stories 2.2 to 2.4); no file I/O in these modules (reading the golden file happens in the test); no changes to `pyproject.toml`, `uv.lock`, the check entry point, `.importlinter`, or any shell package; no edits to `AGENTS.md` or `PROJECT_SPEC.md`; the orchestrator commits and pushes, the implementer does not.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Canonical dump | the golden input object (nested dict with unicode, ints, floats, bools, null, lists) | bytes equal to `tests/golden/canonical-1.json`, LF, trailing newline, non-ASCII preserved | No error expected |
| Compact dump | `{"b": [1, {"d": 2, "c": 3}], "a": "x"}` | `{"a":"x","b":[1,{"c":3,"d":2}]}` on one line | No error expected |
| Non-finite number | a float NaN or infinity anywhere | `ValueError` from both serializers | raised, never written |
| Stable order | the same object serialized twice, and its dict keys inserted in a different order | identical bytes | No error expected |
| Exception taxonomy | AST scan of every module under `src/agentproof` | only `errors.py` defines classes deriving from `BaseException` | test failure otherwise |
| Scenario id rule | `reject-over-limit`, `Reject`, `a.b_c`, 64 chars | match; `-bad`, `has space`, 65 chars, `con` (case-insensitive device name check is the model's job, the regex alone matches `con`) | regex fullmatch result |
| RFC 3339 rule | `2026-10-22T13:05:00+00:00`, `2026-10-22T13:05:00Z`, `2026-10-22T13:05:00.123456-05:00` | match; `2026-10-22T13:05:00` (naive), `2026-10-22 13:05:00Z` (space) do not | regex fullmatch result |

</frozen-after-approval>

## Code Map

- `packages/python/src/agentproof/constants.py` -- replace the docstring-only module; `SUPPORTED_VERSIONS: Final[dict[str, tuple[int, ...]]] = {"suite": (1,), "trace": (1,), "report": (1,)}`; `SCENARIO_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")`; `WINDOWS_DEVICE_NAMES: frozenset[str]` (`CON`, `PRN`, `AUX`, `NUL`, `COM0`–`COM9`, `LPT0`–`LPT9`, `CONIN$`, `CONOUT$`, upper case; callers compare upper-cased); `RFC3339_WITH_OFFSET = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,9})?(Z|[+-]\d{2}:\d{2})")`; `REDACTED: Final = "[REDACTED]"`; `MAX_SUITE_BYTES = MAX_TRACE_BYTES = MAX_REPORT_BYTES = 5 * 1024 * 1024`; `@dataclass(frozen=True) class Statements` with fields `compare_is_saved_data`, `redaction_limits`, `capture_limited`, `limits_v01`, `artifacts_visible_to_readers`, and `STATEMENTS = Statements(...)` with the sentences from PRD AC-26.6, AC-31.4, AC-12.4, AC-33.3 (§5 limits: no reproducibility of stochastic runs, no runtime enforcement, key- and declared-value-based redaction), AC-32.3.
- `packages/python/src/agentproof/errors.py` -- replace; `@dataclass(frozen=True) class Violation(source: str, field: str, message: str)`; `class AgentProofError(Exception)`; `class InputError(AgentProofError)` with `violations: list[Violation]` (constructor takes the list, message is the first violation's text or a summary); `SuiteError`, `TraceFormatError`, `PathError`, `UnsupportedVersionError` deriving from `InputError`; `class ExecutionError(AgentProofError)`; `AdapterLoadError`, `AdapterRunError`, `TraceMissingError`, `ArtifactWriteError` deriving from it; `__all__` listing them.
- `packages/python/src/agentproof/models/common.py` -- new; `type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]`; `Status = Literal["passed", "failed", "error", "skipped"]`; `STATUSES: tuple[Status, ...]`.
- `packages/python/src/agentproof/models/canonical.py` -- new; `dumps(obj: JsonValue) -> str`, `dumps_compact(obj: JsonValue) -> str`, `VOLATILE_PATHS: Final[tuple[str, ...]] = ("run_id", "created_at", "package_version", "scenarios[*].trace.run_id", "scenarios[*].trace.started_at", "scenarios[*].trace.ended_at", "scenarios[*].trace.environment", "scenarios[*].trace.events[*].timestamp", "scenarios[*].trace.events[*].duration_ms", "scenarios[*].cost")`.
- `packages/python/src/agentproof/models/__init__.py` -- keep the docstring; add nothing else (no re-exports yet).
- `packages/python/tests/golden/canonical-1.json` -- new; produced once by `dumps` of the golden input defined in the test module, committed with LF (`.gitattributes` enforces it).
- `packages/python/tests/unit/test_constants.py`, `test_errors_taxonomy.py` (AST scan with `ast` over `src/agentproof/**/*.py`), `tests/unit/models/__init__.py`, `tests/unit/models/test_common.py`, `tests/unit/models/test_canonical.py` -- new; cover every matrix row; the golden test reads the file as bytes and compares with `dumps(...).encode("utf-8")`.
- Existing to respect: `.importlinter` layers (`errors` below `constants` below `models`), the purity checker (no `open`, `Path` I/O, clock, env in these modules), `ruff` TID251 banned names, `mypy --strict` on `src`.

## Tasks & Acceptance

**Execution:**
- [x] `packages/python/src/agentproof/constants.py` -- write the constants and `STATEMENTS` -- criterion 1
- [x] `packages/python/src/agentproof/errors.py` -- write the taxonomy and `Violation` -- criterion 2
- [x] `packages/python/src/agentproof/models/common.py` -- `JsonValue`, `Status`, `STATUSES` -- criterion 3
- [x] `packages/python/src/agentproof/models/canonical.py` -- `dumps`, `dumps_compact`, `VOLATILE_PATHS` -- criterion 4
- [x] `packages/python/tests/golden/canonical-1.json` and the five test modules -- every matrix row, the golden byte comparison, the exception-taxonomy scan -- all criteria
- [x] local verification -- `uv run check` green; golden file is LF in the index after `git add -N` dry check (`git check-attr`)

**Acceptance Criteria:**
- Given `agentproof.constants`, when imported, then every name in criterion 1 exists with the specified value and `STATEMENTS` carries the five sentences.
- Given `agentproof.errors`, when imported and the source tree is scanned, then the hierarchy in criterion 2 exists and no other module defines an exception class.
- Given the golden input, when `dumps` runs, then the bytes equal the committed golden file, and `dumps_compact` of the matrix example equals its expected string.
- Given NaN or infinity, when either serializer runs, then `ValueError` is raised.

## Implementation Notes

**2026-10-23, implementer (worktree `D:\AgentProof-wt-2-1`, branch `story/2-1-constants-canonical`, baseline `037860b`).**

Decisions taken where the plan left room:

- `STATEMENTS` sentences, one plain paraphrase each (PRD read directly): `compare_is_saved_data` (AC-26.6) "This is an exact comparison of two saved reports; it says nothing about whether the agent would behave the same way if run again."; `redaction_limits` (AC-31.4) "Redaction replaces only the configured keys and the declared environment values, assertions evaluate the redacted trace, and you must inspect artifacts before sharing them."; `capture_limited` (AC-12.4) "The trace does not declare complete capture, so proof that a tool was not called is limited to what the adapter observed."; `limits_v01` (AC-33.3 via §5) "AgentProof does not reproduce stochastic agent runs, does not enforce policy at runtime, and redacts only configured keys and declared environment values."; `artifacts_visible_to_readers` (AC-32.3) "Artifacts uploaded from a CI run are visible to anyone with read access to the repository's Actions."
- `capture_limited` carries no `{capture}` placeholder: AC-12.4 asks the result message to state the Capture declaration *and* say the proof is limited; the engine (epic 4) states the label itself and appends this sentence. Documented on the field's docstring.
- `MAX_SUITE_BYTES`, `MAX_TRACE_BYTES`, `MAX_REPORT_BYTES` are three separate `Final` assignments (a chained assignment cannot carry the `Final` annotations the typing convention wants); each is `5 * 1024 * 1024` and the test asserts all three equal that value.
- Regexes are typed `Final[re.Pattern[str]]`; `SUPPORTED_VERSIONS` is `Final[dict[str, tuple[int, ...]]]` exactly as the Code Map says. `WINDOWS_DEVICE_NAMES` has 26 members (`CON PRN AUX NUL CONIN$ CONOUT$`, `COM0`–`COM9`, `LPT0`–`LPT9`) per the Code Map's `COM0`/`LPT0` inclusion.
- `InputError(violations)` stores `list(violations)` (an owned copy) and its message is: the sole violation's text; `"<n> violations; first: <text>"` for several; `"invalid input"` for an empty list. `Violation` is included in `errors.__all__` (sorted) alongside the eleven exception classes.
- `Status` is a plain `Literal[...]` assignment (not a `type` statement) so `typing.get_args(Status)` works at runtime; `JsonValue` uses the 3.12 `type` statement as delegated. `STATUSES` is spelled out as a literal tuple (mypy cannot derive `tuple[Status, ...]` from `get_args`); a test asserts it equals `get_args(Status)`.
- Module-level constants carry attribute docstrings (string literal after the assignment) so "every public name has a docstring" holds for non-callables too; ruff's selected rules accept them.
- Exception-taxonomy scan (`tests/unit/test_errors_taxonomy.py`): AST only, files parsed never imported; a class counts as an exception class when any base's final identifier is `BaseException`, ends in `Error`/`Exception`/`Warning`, or is one of the exception names `agentproof.errors` exports. Seven planted-source cases prove the scanner is not vacuous; one parametrized test per source file asserts zero findings outside `errors.py`.
- Golden input (`GOLDEN_INPUT` in `tests/unit/models/test_canonical.py`): keys out of order including an upper-case key, non-Latin-1 and non-BMP text, `\n`/`\t`/`"`/`\\` escapes, `2**53+1`, floats with repr stable across CPython minors (`0.1 2.5 -3.75 1e-7 10.0`), bools, null, empty list and dict. Golden file produced once with `dumps(...).encode("utf-8")` written as bytes: 511 bytes, 36 LF, 0 CR, no BOM.
- `tests/unit/models/__init__.py` created as the plan lists (one-line docstring); pytest collects `tests/unit/models/*` as package `models` with `tests/unit` on `sys.path`, which collides with nothing.

Observed:

- `uv sync` (uv 0.13.5) created this worktree's `.venv` on CPython 3.13.16.
- `uv run check`: `ruff check` "All checks passed!" and the purity checker silent; `ruff format --check` 36 files already formatted; `mypy --strict` "Success: no issues found in 18 source files"; `lint-imports` "Contracts: 7 kept, 0 broken."; `pytest` 231 passed in 32.48s (was 94 before this story; +137: constants 48, errors taxonomy 64, canonical 22, common 3). Exit 0.
- `uv run python -c "from agentproof.models.canonical import dumps; print(repr(dumps({'b':1,'a':'é'})))"` → `'{\n  "a": "é",\n  "b": 1\n}\n'` (needed `PYTHONIOENCODING=utf-8` on this cp1252 console to print; the value itself is as expected).
- `git check-attr -a packages/python/tests/golden/canonical-1.json` → `text: set`, `eol: lf`. Instead of `git add -N` (index-modifying; the implementer runs read-only git only) the normalization was checked with `git hash-object --path=<f> <f>` vs `git hash-object --no-filters <f>`: both `321cd68d3ca9073f4d521ef790293ef3b5013f39`, so the index blob is byte-identical to the working-tree file.
- `uv run --python 3.12 --locked --isolated pytest tests/unit/models tests/unit/test_constants.py tests/unit/test_errors_taxonomy.py tests/unit/test_repo_hygiene.py` → 148 passed under CPython 3.12.15 (the lowest CI matrix version; exercises the `type` statement and `TypeAliasType`). 3.14 and 3.15 are not installed locally; CI covers them.
- `git status` shows only the Code Map paths plus this plan file; the `ruff format` warnings "LF will be replaced by CRLF" refer to `core.autocrlf` on source files and are unrelated to the golden file, which is pinned `eol=lf`.
- Not done: no commit, no push (orchestrator's job). Caches created by the runs (`.ruff_cache`, `.mypy_cache`, `.pytest_cache`, `__pycache__`) were removed; `.venv` was kept as the worktree's environment.

**2026-10-23, review-pass-1 fixes (implementer, same worktree).** Seven findings, each fixed with the smallest change:

- `STATEMENTS.compare_is_saved_data` now uses the fixed phrase: "This is an exact comparison of saved data; it says nothing about whether the agent would behave the same way if run again."; the test asserts the substring "exact comparison of saved data".
- `STATEMENTS.capture_limited` made generic for `tool_not_called` and `tool_call_count` with `less_than`: "The trace does not declare complete capture, so this absence proof is limited to what the adapter observed."
- New field `Statements.capture_declaration = "capture: {tool_calls}"` (sixth field, after `capture_limited`); its docstring says the engine's result messages and the Report format it with the Trace's `capture.tool_calls`. Tests: six fields asserted in order; a `.format(tool_calls="partial")` test; the one-sentence test now runs over the five sentence fields only (the label is not a sentence).
- `RFC3339_WITH_OFFSET`: every `\d` replaced by `[0-9]`; "２０２６-１０-２２T１３:０５:００Z" (fullwidth digits) added to the reject cases and confirmed rejected.
- `InputError.__init__` now calls `super().__init__(self.violations)` so `args` lets `copy`, `deepcopy` and `pickle` rebuild the exception; `__str__` returns the summary. New test: `copy.deepcopy` and `pickle.loads(pickle.dumps(...))` of a `SuiteError` with two violations keep type, violations and message.
- `errors.py` module docstring: exit codes live in `cli.exit_codes` and are applied by `cli/app.py` (AD-6).
- Taxonomy scanner accepts the builtin `BaseException` subclasses whose names carry no Error/Exception/Warning suffix (`BaseExceptionGroup`, `ExceptionGroup`, `GeneratorExit`, `KeyboardInterrupt`, `StopAsyncIteration`, `StopIteration`, `SystemExit`); planted `class Oops(SystemExit)` case added.

Verified, limited to what covers the edited files as the reviewer asked: `ruff format` on the four files (unchanged), `ruff check --no-cache` on them "All checks passed!", purity checker clean on `constants` and `errors`, `mypy --strict` "Success: no issues found in 18 source files", `pytest tests/unit/test_constants.py tests/unit/test_errors_taxonomy.py` 116 passed. Caches removed again; `git status` unchanged in shape.

## Plan Change Log

## Review Triage Log

### Review pass 1 (quick lens), 2026-10-23

Verdicts: high 0, medium 5, low 2, false 0, maybe-false 0.

| Finding | Verdict | Route | Evidence |
| --- | --- | --- | --- |
| `compare_is_saved_data` says "two saved reports", not the PRD's "saved data" | medium | patch | True; the constant exists to freeze the PRD phrase. |
| `capture_limited` narrowed to "not called"; AC-12.4 reuses it for `less_than` | medium | patch | True; made generic. |
| Capture label wording absent from `STATEMENTS` though AD-20 places it there | medium | patch | True; `capture_declaration` format string added. |
| `RFC3339_WITH_OFFSET` uses `\d`, accepting Unicode digits | medium | patch | True; `[0-9]` with a fullwidth reject case. |
| `InputError` not copyable or picklable (`args` holds the summary, constructor wants a list) | medium | patch | True; `args` now carries the violations and `__str__` renders the summary, with a round-trip test. |
| `errors.py` docstring attributes exit codes to `engine` | low | patch | True; AD-6 puts them in `cli.exit_codes` and `cli/app.py`. |
| Taxonomy scanner misses builtin `BaseException` subclasses with other names | low | patch | True; names added with a planted case. |

## Verification

**Commands:**
- `cd packages/python && uv run check` -- expected: gate green, `lint-imports` 7 kept, purity clean on the new core modules
- `cd packages/python && uv run python -c "from agentproof.models.canonical import dumps; print(repr(dumps({'b':1,'a':'é'})))"` -- expected: `'{\n  "a": "é",\n  "b": 1\n}\n'`
- `git check-attr -a packages/python/tests/golden/canonical-1.json` -- expected: `eol: lf`

**Manual checks (if no CLI):**
- `git status` shows only the Code Map paths.
