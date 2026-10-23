---
title: 'Property tests for round trips, null versus absent, and non-finite numbers'
type: 'feature'
ticket: '6'
created: '2026-10-23'
status: done
baseline_revision: 'fca6286427e55f823cb7560090bf0c6a491eecc5'
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

**Problem:** Example-based tests (stories 2.1 to 2.4) pin the shapes their authors thought of; the byte-identity and robustness claims (PRD NFR-1, NFR-5; spine AD-11, AD-19) also have to hold for the shapes users will actually send: deeply nested payloads, empty strings and containers, combining characters, newlines, non-BMP text, absent versus `null` optional fields, and non-finite numbers hidden at any depth (story 2.6; epic 2 R1, R3, R4).

**Approach:** Add `hypothesis` to the dev group and generate valid Suites, Traces, and Reports as JSON-shaped dicts (never model instances, so the input is what a file holds and the only way in is `model_validate(dict)`, AD-3). Four criteria become properties: the round trip through `canonical.dumps` and `json.loads` is the identity (at least 200 examples per model); a Trace with optional fields omitted serializes with every field present and reads back equal, and explicit `null`s validate to an equal object; NaN and infinity anywhere in a tool argument, event payload, Suite input, Final Output, result detail, cost, or Comparison value raise a `ValidationError` whose location names the path; generated Unicode strings survive exactly and `dumps` is byte-identical across calls and under key-order shuffles. The models are not changed: a property that exposes a defect is `xfail(strict=True)` and recorded as a finding.

## Boundaries & Constraints

**Always:** tests only (plus the dev dependency and the Hypothesis profile); every property sets `max_examples` explicitly; the Hypothesis profile is derandomized with no example database; strategies live in `tests/unit/models/strategies.py`, properties in `tests/unit/models/test_properties.py`; generated inputs respect every model rule so a failure is a model finding, not a strategy bug; the file runs in about a minute.

**Never:** no change to any model, `canonical.py`, `constants.py`, or `errors.py`; no runtime dependency (hypothesis is dev-only); no new exception class; no `.hypothesis/` committed.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Round trip (criterion 1) | generated `JsonValue`, Trace, Report, Suite (every Scenario skipped), 200 examples each | `model_validate(json.loads(dumps(model_dump(mode="json")))) == original`; a second `dumps` is byte-equal | none expected |
| Suite with an unskipped Scenario (criterion 1) | the same, Scenarios without `skip` | equal | finding F1: `ValidationError` at `scenarios.<i>.skip`; `xfail(strict=True)` |
| Null versus absent (criterion 2) | Trace with every optional key omitted | dump has every field of every model; `null` where the default is `None`; defaults filled (`capture.tool_calls == "unknown"`, `redaction` empty, `metadata == {}`, `redacted is False`); reads back equal | none expected |
| Explicit nulls (criterion 2) | the same Trace with `null` for every optional key | equals the omitted-keys Trace | none expected |
| Nested null for a field with a non-null default (criterion 2, AD-19) | `capture: {tool_calls: null}`, `redaction: {applied/paths/env_names: null}` | equals the omitted-keys Trace | finding F2: `ValidationError`; `xfail(strict=True)` |
| Non-finite in Trace payloads (criterion 3) | NaN, inf, -inf at a generated depth inside `arguments`, `result`, `output`, `metadata` | rejected | exactly one `finite_number` at `events.0.<field>`; the message names the dotted path inside the value |
| Non-finite elsewhere (criterion 3) | the same in Suite `input`, `tool_arguments_match.arguments`, result `detail`, Comparison `argument_changes`, an embedded Trace's Final Output; `cost` | rejected | `finite_number` whose location contains the path in order (union branch labels interleave for plain `JsonValue` fields); `cost` is one clean error at `scenarios.0.cost` |
| Serializer refuses (criterion 3) | non-finite anywhere in a value | `dumps` raises | `ValueError` |
| Unicode (criterion 4) | generated strings with non-ASCII, combining marks, newlines, empty strings used as ids, keys, and values | preserved code point for code point; non-ASCII written literally | none expected |
| Byte identity (criterion 4) | `dumps` twice; the same value with every object's key order permuted | identical bytes; LF only; one trailing newline | none expected |

</frozen-after-approval>

## Code Map

- `packages/python/tests/unit/models/strategies.py` -- new; `texts` (UTF-8 repertoire, combining-heavy alphabet, awkward samples), `json_values` (recursive, finite, `max_leaves=6`), `json_values_with_a_hole` (builder plus path; keys non-empty and dot-free), `timestamps`, `scenario_ids` (charset and device names), `argument_paths`, and the dict builders `suite_dicts(skipped=)`, `trace_dicts(presence=)`, `report_dicts`; `presence=False` omits every optional key, `None` draws each; strategies are `functools.cache`d because building a strategy per draw dominated run time.
- `packages/python/tests/unit/models/test_properties.py` -- new; 32 test cases (26 passing, 6 strict xfails for F1 to F3), the fixed minimal Suite/Trace/Report the non-finite properties start from, and the `xfail(strict=True)` findings.
- `packages/python/tests/conftest.py` -- new; registers and loads the `agentproof` Hypothesis profile (`derandomize=True`, `database=None`, `deadline=None`).
- `packages/python/pyproject.toml`, `packages/python/uv.lock` -- `hypothesis>=6.170` in the dev group (resolved 6.170.8, plus `sortedcontainers`).
- `_bmad-output/initiative-agentproof-mvp/deferred-work.md` -- one entry for finding F2 (F1's entry is added by story 2.5's implementer).
- Existing to respect: `.gitignore` already lists `.hypothesis/`; `test_tooling_config` pins the runtime dependencies (unchanged).

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml`, `uv.lock` -- `hypothesis` in the dev group
- [x] `tests/conftest.py` -- derandomized profile, no database
- [x] `strategies.py` -- JsonValue, Suite, Trace, Report, hole, timestamp, id strategies
- [x] `test_properties.py` -- criteria 1 to 4, the shuffle property, the two findings as strict xfail
- [x] `deferred-work.md` -- finding F2 routed to story 2.7
- [x] local verification -- `uv run check` green; `uv run --python 3.12 --locked --isolated pytest tests/unit/models/test_properties.py -q -p no:cacheprovider` green; caches and `.hypothesis/` removed

**Acceptance Criteria:**
- Given generated Suites, Traces, Reports, and `JsonValue`s, when serialized with `dumps`, parsed, and validated again, then the result equals the original for 200 examples each (a Suite needs every Scenario skipped, finding F1).
- Given a Trace with optional fields omitted, when validated and dumped, then every optional field is present (`null` where the default is `None`) and re-validating gives an equal object; explicit nulls give an equal object.
- Given NaN or infinity in a tool argument or Final Output (and the other payload fields), when validated, then a `ValidationError` locates it.
- Given generated Unicode strings, when round-tripped, then they are preserved exactly and `dumps` is byte-identical across calls and key-order shuffles.

## Implementation Notes

**2026-10-23, implementer (worktree `D:\AgentProof-wt-2-6`, branch `story/2-6-property-tests`, baseline `fca6286`).** The first worktree was lost to an environment restart before anything was committed and the work was redone from the same design.

Decisions:
- Strategies emit dicts, not models, and build optional keys through one `_draw_optional(presence, ...)` helper so `presence=False` is the "every optional field omitted" input of criterion 2.
- "Taxonomy error naming the path" is a Pydantic `ValidationError` with the path in `loc`, as in stories 2.3 and 2.4; Trace payloads give exactly one `finite_number` at `events.<i>.<field>` with the inner dotted path in the message, other `JsonValue` fields give the union-branch error list with the path in order inside `loc`, so the tests assert the path as an in-order subsequence of `loc` there.
- Hole keys are non-empty and dot-free. With an empty key `_require_finite`'s `f"{path}.{key}" if path else key` degenerates (key `''` then index `0` reports `0`, the value itself reports as `the value itself`); not a defect worth a finding (an empty key is a legal JSON key, the message is merely ambiguous), recorded here only.
- The non-finite properties start from a fixed minimal artifact and generate only the hole; the round trips use the full strategies.
- Speed: generated artifacts were 0.1 s each at first (about 300 s for the file). Caching the strategy constructors with `functools.cache`, building timestamps and ids from integers and characters instead of `from_regex`, and smaller sizes (`max_leaves=6`, text up to 12, up to 3 events, 2 Scenarios) brought the file to 45 to 50 s. The two strict-xfail properties use `settings(max_examples=20, phases=(Phase.generate,))`: shrinking an expected failure cost 45 s.
- Hypothesis still creates `packages/python/.hypothesis/constants/` (its source-constant cache) with `database=None`; it is not the example database, it is covered by the existing `.gitignore` entry (and carries its own `.gitignore`), and it was deleted after the runs.
- Windows device-name and case-insensitive id rules are exercised by `scenario_ids` plus `unique_by=str.lower`; no property found a violation.

Findings against the models (models not changed):
- **F1 (AD-19, story 2.2 `models.suite.Scenario`).** `Suite.model_dump(mode="json")` writes `"skip": null` for a Scenario without `skip`; `Scenario._present_skip_is_a_reason` runs only when the key is present and rejects a non-string, so the Suite's own dump does not validate. Minimal input: `Suite.model_validate({"version": 1, "suite": "s", "scenarios": [{"id": "a", "input": {}, "assertions": [{"type": "tool_called", "tool": "t"}]}]})`, dump with `mode="json"`, `canonical.dumps`, `json.loads`, `Suite.model_validate` again: `ValidationError` at `scenarios.0.skip`, type `value_error`, "skip needs a reason string; presence means skipped, got None". A Suite whose Scenarios are all skipped round-trips. Test: `test_suite_with_an_unskipped_scenario_round_trips_through_canonical_dumps` (`xfail(strict=True)`). Routed to story 2.7/3.3 in `deferred-work.md` by story 2.5's implementer; the fix is to treat `skip: null` as absent (and decide whether `skip: ""` stays an error).
- **F2 (AD-19, stories 2.1/2.2).** `_null_means_absent` is applied to `Trace`, `TraceEvent`, and the result/report models only. Nested models with non-null defaults reject an explicit null: `Trace.capture.tool_calls` (`literal_error`), `redaction.applied` (`bool_type`), `redaction.paths` and `env_names` (`tuple_type`); probed also for every `Suite.defaults` field (`fail_on_missing_trace` `bool_type`, `fixture.deterministic` `bool_type`, `compare.include_arguments` and `redact.keys` `tuple_type`, `fixture: null` `model_type`). The serializer never writes these nulls, so round trips hold; this is input leniency. Minimal input: a valid Trace with `"capture": {"tool_calls": null}`. Test: `test_explicit_null_for_a_nested_field_with_a_default_reads_as_absent` (`xfail(strict=True)`). Entry added to `deferred-work.md`, owner story 2.7 (the property flips to xpass-fail, forcing the marker's removal, when it is fixed).

Observed:
- `uv sync` created the worktree `.venv` on CPython 3.13.16; `uv add --group dev "hypothesis>=6.170"` resolved hypothesis 6.170.8 and sortedcontainers 2.4.0.
- `uv run pytest tests/unit/models/test_properties.py -q -p no:cacheprovider` -> 20 passed, 2 xfailed in 48 s (51 s wall) on 3.13.
- `uv run check` -> exit 0 in 58 s wall: `ruff check` "All checks passed!", `ruff format --check` "49 files already formatted", `mypy --strict` "Success: no issues found in 23 source files", `lint-imports` "Contracts: 7 kept, 0 broken.", `pytest` 776 passed, 2 xfailed in 51.5 s (the 2.4 baseline was 756 passed; 20 passing properties added).
- `uv run --python 3.12 --locked --isolated pytest tests/unit/models/test_properties.py -q -p no:cacheprovider` -> 20 passed, 2 xfailed in 45.4 s (55 s wall) on CPython 3.12. 3.14 and 3.15 are not installed locally; CI covers them.
- One `E501` in `strategies.py` fixed and `ruff format` rewrote one file before the green run.
- Not verified here: Linux execution (the Windows run only); derandomized examples are the same on both platforms by construction but the Linux timing is unmeasured.

**2026-10-23, review-pass-1 fixes (implementer, same worktree).** Coordinator review of PR #12, applied as asked:

- Finding 1 (message substring check): `_assert_one_finite_error` now compares the error's structured context: exactly one error, `type == "finite_number"`, `loc` equal to the expected tuple, and `ctx == {"number": str(number), "path": <dotted hole path>}` (`PydanticCustomError`'s context, visible in `ValidationError.errors()`), replacing every `_inner_path_text(path) in msg`. For plain `JsonValue` fields (Suite input, detail, Comparison) the existing in-order `loc` check stays, now with a fixed two-hole case that also asserts the clean sibling key is absent from every location.
- Finding 2 (broad xfails): F2 is one parametrized case per field (`capture.tool_calls` `literal_error`, `redaction.applied` `bool_type`, `redaction.paths` and `redaction.env_names` `tuple_type`); each body catches the `ValidationError`, asserts the error list equals exactly that one `(loc, type)`, then re-raises, so a partial fix turns exactly the fixed cases into strict XPASS failures and a different error fails with `AssertionError` instead of hiding. F1's body asserts the errors are `value_error` at `scenarios.<i>.skip` for exactly the Scenarios generated without `skip`.
- Finding 4 (depth and two holes): fixed `test_non_finite_deep_in_a_trace_payload_names_the_exact_path` at depths 50 and 80 (dicts with a list index every tenth level), `test_non_finite_fifty_levels_deep_in_a_suite_input_is_located_by_the_path`, `test_two_holes_in_one_trace_payload_report_the_first_in_document_order`, `test_two_holes_in_different_trace_events_each_get_their_own_error`, and `test_two_holes_in_a_suite_input_are_both_located_and_the_clean_key_is_not`. Deepening exposed a new model finding, **F3**: finite, valid JSON nested about 100 levels or more is rejected (passes at 90, fails at 100) with `recursion_loop` plus one error per union branch (496 errors), while `json.loads` and `dumps` handle 150+ levels; the same for Suite input. Held as `test_finite_json_one_hundred_and_fifty_levels_deep_is_accepted` (`xfail(strict=True)`, body asserts the errors sit under `events.0.arguments` and include `recursion_loop`); `deferred-work.md` entry added, owner story 3.3 and the architect. The passing deep cases stop at 80, below the limit, so they do not depend on its exact value.
- Finding 5 (type changes and cross-wiring): `_assert_identical` compares type at every node (so `1`, `1.0`, `True` differ) and `repr` for floats (`-0.0` versus `0.0`); `_assert_models_identical` applies it to both the Python-mode and JSON-mode dumps and is used by the Trace, Report, and Suite round trips and the `JsonValue` round trip. The Unicode property draws eleven pairwise-distinct strings (`st.lists(texts(), unique=True)`), one per field (`run_id`, `scenario_id`, agent and adapter name and version, tool, argument key and value, output, status), and asserts each field holds its own value.

Verified after the fixes: `uv run check` exit 0 in 47 s wall (`ruff check` "All checks passed!", `ruff format --check` "49 files already formatted", `mypy --strict` "Success: no issues found in 23 source files", `lint-imports` "Contracts: 7 kept, 0 broken.", `pytest` 782 passed, 6 xfailed in 40 s); `uv run --python 3.12 --locked --isolated pytest tests/unit/models/test_properties.py -q -p no:cacheprovider` -> 26 passed, 6 xfailed in 48 s (55 s wall). The six xfails are F1 (1), F2 (4), F3 (1). Caches and `.hypothesis/` removed.

## Plan Change Log

- 2026-10-23, review pass 1: rules added beyond the frozen matrix: the structured `ctx` check for Trace payload errors, F2 split into four per-field cases with exact-location xfail bodies, F3 (`recursion_loop` beyond about 90 levels) as a third finding with its own strict xfail, the fixed deep and two-hole cases, strict type identity in the round trips, and distinct per-field strings in the Unicode property.

## Review Triage Log

### Review pass 1 (coordinator), 2026-10-23

Eight items; five patched in this worktree, one confirmed with no action, three confirmed fine as they are.

| # | Finding | Disposition | Evidence |
| --- | --- | --- | --- |
| 1 | "Message names the inner path" was a substring check that the message's own vocabulary could satisfy | patched: exact `loc`, `type`, and `ctx` (`number`, `path`) comparison | `_assert_one_finite_error`; the three Trace payload properties and the embedded-Trace property |
| 2 | Both xfails accepted any `ValidationError`; F2 was one case for four fields | patched: F2 per field, every xfail body asserts the exact expected `(loc, type)` and re-raises | `test_explicit_null_for_a_nested_field_with_a_default_reads_as_absent[...]` (4 cases), `test_suite_with_an_unskipped_scenario_round_trips_through_canonical_dumps` |
| 3 | F1's `deferred-work.md` entry lives on story 2.5's branch (PR #13) | no action: resolves through merge order; this PR adds only F2 and F3 entries | `deferred-work.md` |
| 4 | Nesting depth only 0 to 3; no multi-hole case | patched: fixed depth 50/80 Trace cases, a 50-level Suite case, three two-hole cases; deeper input exposed F3 | `test_non_finite_deep_in_a_trace_payload_names_the_exact_path`, the `test_two_holes_*` cases, F3 test |
| 5 | Equality could not see `1` versus `1.0` versus `True`, and shared text values hid cross-wiring | patched: `_assert_identical` / `_assert_models_identical` in every round trip; eleven distinct strings in the Unicode property | `_assert_models_identical` call sites; `test_generated_strings_survive_the_round_trip_exactly` |
| 6 | Unicode placement only in fields with no charset rule | confirmed fine, no action | strategies unchanged |
| 7 | Derandomized profile with no database | confirmed fine (known tradeoff: fixed examples, no accumulated failures), no action | `tests/conftest.py` |
| 8 | Timing margin and runtime-dependency test | confirmed fine: hypothesis and sortedcontainers are dev-only and `test_runtime_dependencies_are_unchanged` passes, no action | `pyproject.toml`; `uv run check` |

## Verification

**Commands:**
- `cd packages/python && uv run check` -- expected: gate green, 782 passed, 6 xfailed
- `cd packages/python && uv run --python 3.12 --locked --isolated pytest tests/unit/models/test_properties.py -q -p no:cacheprovider` -- expected: 26 passed, 6 xfailed
- `git status --short` -- expected: this plan, `deferred-work.md`, `pyproject.toml`, `uv.lock`, `tests/conftest.py`, `strategies.py`, `test_properties.py`

**Manual checks (if no CLI):**
- No `.hypothesis/` directory is tracked or left in the tree.
