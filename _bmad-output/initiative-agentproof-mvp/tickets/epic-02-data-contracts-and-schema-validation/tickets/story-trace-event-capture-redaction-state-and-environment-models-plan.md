---
title: 'Trace, event, capture, redaction-state, and environment models'
type: 'feature'
ticket: '3'
created: '2026-10-23'
status: done
baseline_revision: '05ed167eb483c088cb22a7f48c4bf75e750d4d57'
route: 'full'
route_source: 'pinned'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nothing can validate a Trace yet. Every adapter, the Fixture Agent, `trace validate`, Replay, and the Report embed or produce a Trace, and the rules that make one trustworthy (integer schema version, contiguous 0-based `seq`, the eleven event types, RFC 3339 timestamps with an offset, the Capture default, the redaction state, the environment allowlist) have no implementation, so stories in epics 3 to 6 have no model to import (story 2.3; epic 2 R1 and R5; PRD FR-5, AC-5.1 to AC-5.6, AC-7.2, AC-31.2).

**Approach:** Add `agentproof.models.trace` with the frozen, forbid-unknown Pydantic v2 models the spine seeds (AD-3, AD-5, AD-9, AD-10): `Trace`, `TraceEvent`, `ToolRef`, `EventError`, `AgentInfo`, `AdapterInfo`, `ModelInfo`, `Capture`, `RedactionState`, `Environment`. Validation lives on the models, not in a loader, so every path into a `Trace` object enforces the same rules (epic decision 2026-10-22). Timestamps are `str` validated by `constants.RFC3339_WITH_OFFSET` and stored unchanged; `version` is an exact integer in `SUPPORTED_VERSIONS["trace"]`; `seq` contiguity is a `Trace`-level validator whose error carries the location `events.<index>.seq`. Tests cover one passing and one failing case per rule, the spine's Trace JSON seed, and frozen and forbid behaviour.

**Decisions delegated by the maintainer (2026-10-22, "approve all, you are the owner"):** the event model is named `TraceEvent` as the spine (AD-5) and epic R1 spell it; sub-models carry explicit names (`ToolRef`, `EventError`, `AgentInfo`, `AdapterInfo`, `ModelInfo`) so none collides with the adapter Protocol or the Pydantic namespace; `version`, `seq`, and `duration_ms` require an exact `int` (no `"1"`, `True`, or `1.0` coercion; AD-3's "strings are rejected" extended to the other integer fields of a JSON contract); NaN and infinity are rejected inside `arguments`, `result`, `output`, and `metadata` (epic R4, Consistency Conventions) by a pure walk, because Pydantic's `allow_inf_nan` cannot be applied to the recursive `JsonValue` alias.

## Boundaries & Constraints

**Always:** `models/trace.py` imports only the standard library, Pydantic, `agentproof.constants`, and `agentproof.models.common` (AD-2); it uses none of the names AD-1 bans (purity checker and TID251 apply); every model is `BaseModel` with `model_config = ConfigDict(frozen=True, extra="forbid")` and no `strict`; models are validated through `model_validate(dict)` in tests exactly as `loading.parse_trace` will do; every validation error names the field path through the `ValidationError` location; timestamps are stored as given (`Z` is not rewritten); every public name has a docstring; `mypy --strict` with the pydantic plugin passes on `src`; no `from __future__ import annotations`.

**Never:** No file reading, no YAML or JSON text parsing (epic 3), no redaction logic (epic 5), no evaluation; no changes to `constants.py`, `errors.py`, `models/common.py`, `models/canonical.py`, or `models/__init__.py` (story 2.2 runs in parallel and the re-export decision belongs to a later story); no changes to `pyproject.toml`, `uv.lock`, `.importlinter`, the check entry point, or any shell package; no custom exception class (only `errors.py` defines them; the models raise Pydantic `ValidationError`); the orchestrator commits and pushes, the implementer does not.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Spine seed validates (criterion 1) | the spine's Trace JSON seed as a dict (events 1 to 3 completed to the full key set, `timestamp` filled) | `Trace` with `version == 1`, `run_id`, `scenario_id`, `started_at`, `ended_at`, `agent`, `adapter`, `model`, `capture`, `environment`, `redaction`, four `events` | No error expected |
| Trace without `model` values (criterion 1, AC-5.1) | `model` key absent; `model: {}`; `model: {"provider": null, "name": null}` | validates; `trace.model is None` when absent, `ModelInfo(provider=None, name=None)` otherwise | No error expected |
| Unsupported or non-integer version (criterion 1, AD-3) | `version: 2`, `"1"`, `1.0`, `true`, missing | rejected | `ValidationError` at `version`; message names the given version and the supported ones |
| Eleven event types (criterion 2, AC-5.2) | one event of each documented type | all accepted | No error expected |
| Unknown event type (criterion 2, AC-5.2) | `{"seq": 1, "type": "bogus"}` at list index 1 | rejected | `ValidationError` at `events.1.type`; message names `bogus` |
| Contiguous `seq` (criterion 2, AD-5) | `seq` 0, 1, 2, 3 | accepted; empty `events` also accepted | No error expected |
| Gap, duplicate, disorder, negative, non-integer `seq` (criterion 2, AC-7.2) | `0, 2`; `0, 0`; `1, 0`; `-1`; `"0"`; `0.0`; `true` | rejected naming the first offending index | `ValidationError` at `events.<index>.seq`; message states the actual and expected value |
| Optional event fields (criterion 2) | `tool`, `arguments`, `result`, `status`, `error`, `output`, `timestamp`, `duration_ms` absent | all `None`; `redacted is False`; `metadata == {}` | No error expected |
| `tool` and `error` shapes (criterion 2) | `tool: {"name": "x"}`; `error: {"type": "ValueError", "message": "m", "unhandled": true}`; `tool: {}`; `error` missing `unhandled` | first two accepted (`call_id is None`); last two rejected | `ValidationError` at `events.0.tool.name` / `events.0.error.unhandled` |
| Timestamps (criterion 3, AC-5.3) | `2026-10-22T13:05:00+00:00`, `2026-10-22T13:05:00Z`, `2026-10-22T13:05:00.123456-05:00` on `started_at`, `ended_at`, `events[].timestamp` | accepted and stored byte-for-byte as given | No error expected |
| Naive or non-string timestamp (criterion 3) | `2026-10-22T13:05:00`, `2026-10-22 13:05:00Z`, `1761138300` (int), a `datetime` object, `"x2026-10-22T13:05:00Zy"` | rejected | `ValidationError` at `started_at` / `ended_at` / `events.<i>.timestamp` |
| Capture default (criterion 4, AC-5.6) | `capture` absent; `{"tool_calls": "complete"}`; `{"tool_calls": "partial"}`; `{"tool_calls": "all"}` | `Capture(tool_calls="unknown")`; `complete`; `partial`; rejected | `ValidationError` at `capture.tool_calls` |
| Redaction state default (criterion 4, AC-31.2) | `redaction` absent; `{"applied": true, "paths": ["arguments.api_key"], "env_names": ["OPENAI_API_KEY"]}`; `{"applied": true, "values": [...]}` | `RedactionState(applied=False, paths=[], env_names=[])`; the given state; rejected | `ValidationError` at `redaction.values` |
| Environment allowlist (criterion 4, AC-5.5) | the four keys; `environment` absent; `{"hostname": "ci-1"}`; `{"HOME": "/root"}` | `Environment` with the four values; all `None` when absent; rejected naming the key | `ValidationError` at `environment.hostname` (`extra_forbidden`) |
| Unknown field anywhere (AD-3) | an extra key on the Trace, an event, `tool`, `error`, `agent`, `adapter`, `model`, `capture`, `redaction` | rejected | `ValidationError` at the key's path, type `extra_forbidden` |
| Frozen (AD-3) | assigning `trace.run_id`, `event.seq` after validation | rejected; the value is unchanged | `ValidationError` type `frozen_instance` |
| Non-finite number (epic R4) | `math.nan` or `math.inf` nested anywhere in `arguments`, `result`, `output`, `metadata` | rejected | `ValidationError` at the field; message names the offending value's path inside it |

</frozen-after-approval>

## Code Map

- `packages/python/src/agentproof/models/trace.py` -- new; `EVENT_TYPES` (the eleven-value tuple) and `EventType` literal; `Timestamp` (`Annotated[str, BeforeValidator(_require_timestamp)]`); `TraceSchemaVersion` (exact `int` in `SUPPORTED_VERSIONS["trace"]`, exported with a JSON Schema `enum`); `_NonNegativeInt` (`Annotated[int, Field(ge=0), BeforeValidator(_require_integer)]`, exports `minimum: 0`); `_null_means_absent(model, data)` used as a before-validator on `Trace` and `TraceEvent`; `ToolRef(name: str, call_id: str | None = None)`; `EventError(type: str, message: str, unhandled: bool)`; `AgentInfo(name: str, version: str | None = None)`; `AdapterInfo(name: str, version: str)`; `ModelInfo(provider: str | None = None, name: str | None = None)`; `Capture(tool_calls: Literal["complete", "partial", "unknown"] = "unknown")`; `RedactionState(applied: bool = False, paths: tuple[str, ...] = (), env_names: tuple[str, ...] = ())`; `Environment(package_version, python_version, os, source_revision: str | None = None)`; `TraceEvent(seq, type, timestamp, duration_ms, tool, arguments, result, status, error, output, redacted=False, metadata={})`; `Trace(version, run_id, scenario_id, started_at, ended_at, agent, adapter, model=None, capture=Capture(), environment=Environment(), redaction=RedactionState(), events: tuple[TraceEvent, ...])` with the `events` validator that raises a `ValidationError` located at `events.<index>.seq`; every one of the 43 fields carries `Field(description=...)`; `__all__`.
- `packages/python/tests/unit/models/test_trace.py` -- new; `SEED` (the spine's Trace JSON seed completed to the full key set) and a `_trace(**overrides)` helper; one test per matrix row, parametrized over the eleven types and the timestamp forms; `_locs`, `_errors`, `_types` helpers asserting every error's `loc`, message, and stable type code; `_schema_properties` walking `Trace.model_json_schema()` for the bounds, enum, array, and description assertions.
- Existing to respect: `.importlinter` layers (`models` above `constants` and `errors`), the purity checker, ruff TID251, `mypy --strict` with the pydantic plugin, `models/canonical.VOLATILE_PATHS` (`run_id`, `started_at`, `ended_at`, `environment`, `events[*].timestamp`, `events[*].duration_ms` must be the field names used here).

## Tasks & Acceptance

**Execution:**
- [x] `packages/python/src/agentproof/models/trace.py` -- the ten models, the two annotated types, the `events` validator, the finite-number walk -- criteria 1 to 4
- [x] `packages/python/tests/unit/models/test_trace.py` -- every matrix row, the spine seed, the eleven types, the `Z` timestamp, frozen and forbid -- criteria 1 to 4
- [x] local verification -- `uv run check` green; caches removed; `git status` shows only the Code Map paths plus this plan

**Acceptance Criteria:**
- Given the spine's Trace JSON seed, when validated, then it yields a `Trace` with `version == 1` and every field of criterion 1, and a Trace without `model` values validates.
- Given an events list, when validated, then each event has `seq`, a `type` from the eleven-value literal, the optional fields with `redacted` default `False` and `metadata` default `{}`, and a gap, duplicate, disorder, or unknown type raises naming the index.
- Given a timestamp, when validated, then an RFC 3339 string with an offset or `Z` is accepted and stored unchanged, and a naive timestamp or a non-string is rejected.
- Given a Trace dict, when validated, then `capture` defaults to `Capture(tool_calls="unknown")`, `redaction` defaults to not applied with empty lists, and `environment` accepts only the four named keys, rejecting any other key naming it.

## Implementation Notes

**2026-10-23, implementer (worktree `D:\AgentProof-wt-2-3`, branch `story/2-3-trace-models`, baseline `05ed167`).**

Decisions taken where the plan left room:

- Probed Pydantic 2.14.1 before designing: (a) a `ValidationError` built with `ValidationError.from_exception_data` and raised inside a `field_validator("events")` is re-raised with the outer location prepended, so the contiguity error lands at `events.<index>.seq` (not merely `events`); (b) lax `int` accepts `"1"`, `True` and `1.0`, hence the `_require_integer` before-validator on `version`, `seq` and `duration_ms`; (c) `Field(allow_inf_nan=False)` on the recursive `JsonValue` alias raises `TypeError` for lists (Pydantic applies the check to the whole value), hence the `_first_non_finite` walk as an after-validator on `arguments`, `result`, `output` and `metadata`.
- Validation failures are Pydantic `ValidationError`s with custom error types (`integer_required`, `unsupported_version`, `timestamp_type`, `timestamp_format`, `seq_not_contiguous`, `finite_number`); no exception class is defined (the taxonomy scan keeps `errors.py` the only one). `loading.parse_trace` (epic 3) maps `error["loc"]` to `Violation.field`.
- Field names follow the spine seed exactly; `VOLATILE_PATHS` names (`run_id`, `started_at`, `ended_at`, `environment`, `events[*].timestamp`, `events[*].duration_ms`) all resolve to real fields, which `test_volatile_trace_paths_name_real_trace_and_event_fields` asserts.
- `TraceEvent.status` is a free `str | None` (the spine seeds `"ok"` and names no literal); `EventError` requires all three of `type`, `message`, `unhandled` as the seed's `{"type": str, "message": str, "unhandled": bool}` says; `seq` and `duration_ms` carry `ge=0`; `Trace.model` is `ModelInfo | None` defaulting to `None` so an adapter may omit the key entirely (AC-5.1), while the seed's `{"provider": null, "name": null}` form also validates.
- `capture`, `environment` and `redaction` use `Field(default_factory=...)` so each Trace gets its own default instance (`RedactionState` holds lists); `Environment()` with all four fields `None` is the default when the key is absent, since the runner fills it (AD-9).
- Public names: `Trace`, `TraceEvent`, `ToolRef`, `EventError`, `AgentInfo`, `AdapterInfo`, `ModelInfo`, `Capture`, `RedactionState`, `Environment`, plus `EventType`, `EVENT_TYPES`, `CaptureLevel`, `SchemaVersion`, `Timestamp`. `models/__init__.py` is untouched (story 2.2 in parallel).
- `_require_finite` is a PEP 695 generic function (`[T: JsonValue]`) so the same validator types both `JsonValue` and `dict[str, JsonValue]` fields under `mypy --strict`.

Observed:

- `uv sync` (uv 0.13.5) created this worktree's `.venv` on CPython 3.13.16 with pydantic 2.14.1.
- `uv run check`: `ruff check` "All checks passed!" with the purity checker silent; `ruff format --check` "38 files already formatted"; `mypy --strict` "Success: no issues found in 19 source files"; `lint-imports` "Contracts: 7 kept, 0 broken."; `pytest` 394 passed (was 250 before this story; +144, all in `tests/unit/models/test_trace.py`). Exit 0. Run twice with the same result.
- `uv run --python 3.12 --locked --isolated pytest tests/unit/models/test_trace.py -q` → 144 passed under CPython 3.12.15 (lowest CI matrix version; exercises the PEP 695 generic validator). 3.14 and 3.15 are not installed locally; CI covers them.
- `git status --short` shows exactly three untracked paths: this plan, `packages/python/src/agentproof/models/trace.py`, `packages/python/tests/unit/models/test_trace.py`.
- Caches created by the runs (`.ruff_cache`, `.mypy_cache`, `.pytest_cache`, every `__pycache__` outside `.venv`) were removed; `.venv` kept.
- Not done: no commit, no push (orchestrator's job).

Risks and open points:

- The spine's Trace seed abbreviates events 1 to 3 and writes `"timestamp": "..."`; `SEED` in the test completes the key set and uses real timestamps, so "the seed validates" is proven on that completed form, not on the literal text.
- `Field(ge=0)` on `seq` and `duration_ms`, the exact-integer rule, and the finite-number walk are stricter than the story's wording; each is a one-line removal if the maintainer prefers the looser reading. The JSON Schema (story on `export_schemas`) will show `minimum: 0` for them and plain `string` for timestamps (no `pattern`; adding one anchored for ECMA regex is a later decision).
- `TraceEvent.status` and `run_id`/`scenario_id` are unconstrained strings here; the Suite model (story 2.2) owns the id charset, and whether the runner cross-checks `trace.scenario_id` against the Scenario is epic 4's call.

**2026-10-23, review-pass-1 fixes (implementer, same worktree).** Six coordinator patches, the sixth changed from "record" to "apply" by the addendum:

- `_NonNegativeInt = Annotated[int, Field(ge=0), BeforeValidator(_require_integer)]` replaces `Annotated[_ExactInt, Field(ge=0)]`; the schema now carries `minimum: 0` (no `ge` key) for `seq` and the integer branch of `duration_ms`, and both validators still fire (`integer_required` for `"0"`/`1.5`/`True`, `greater_than_equal` for `-1`).
- `_null_means_absent(model, data)`: a documented helper used as `model_validator(mode="before")` on `Trace` and `TraceEvent`; drops a `None` only when the key names a field that has a default, so `capture`/`environment`/`redaction`/`metadata`/`redacted: null` read as their defaults, while `run_id: null` (`string_type`), `events: null` (`tuple_type`), `type: null` (`literal_error`), `started_at: null` (`timestamp_type`) and `result_summary: null` (`extra_forbidden`) keep their errors. Story 2.2 may hoist it.
- Error type codes asserted throughout (`_types` helper). A v2 Trace with an extra key yields both `unsupported_version` and `extra_forbidden`: **the loader must prefer `unsupported_version` when both appear**, raising `UnsupportedVersionError` rather than `TraceFormatError`, since an unknown field in an unsupported version is expected, not a second fault.
- `Field(description=...)` on all 43 fields of the ten models (verified by iterating `model_fields`; `test_every_serialized_field_has_a_description` walks the generated schema's root and `$defs`).
- `version` exported with `json_schema_extra={"enum": list(SUPPORTED_VERSIONS["trace"])}` (shows `enum: [1]`); alias renamed `SchemaVersion` -> `TraceSchemaVersion`, `__all__` updated and tested.
- Sequence fields are tuples: `Trace.events: tuple[TraceEvent, ...]`, `RedactionState.paths`/`env_names: tuple[str, ...]` with `default_factory=tuple`. JSON lists validate into them; `model_dump(mode="json")` emits arrays and round-trips `SEED` exactly; `model_json_schema()` exports `type: array`; the seq-contiguity validator runs on the tuple. `metadata`, `arguments`, `result`, `output` unchanged; the module docstring states they are not deep-frozen.
- Did not fit: `hash(trace)` works only for a Trace with no events. Every `TraceEvent.metadata` is a dict (default `{}`), and the addendum keeps `metadata` a mapping, so Pydantic's frozen `__hash__` raises `TypeError` for any Trace with an event. Asserted as it is (`hash` of an event-less Trace and of `RedactionState` works; `hash` of a Trace with one event raises) and stated in the docstring. Making it hashable would need an immutable mapping type for `metadata`, a 2.4/2.5 decision.

Verified after the fixes: `uv run check` exit 0 with `ruff check` "All checks passed!" (purity silent), `ruff format --check` "38 files already formatted", `mypy --strict` "Success: no issues found in 19 source files", `lint-imports` "Contracts: 7 kept, 0 broken.", `pytest` 411 passed (was 394; `test_trace.py` now 161 tests). `uv run --python 3.12 --locked --isolated pytest tests/unit/models/test_trace.py -q` -> 161 passed on CPython 3.12.15. Caches removed again (0 remaining outside `.venv`); `git status --short` still shows exactly the three paths.

## Plan Change Log

- 2026-10-23, review pass 1: rules added beyond the frozen matrix, by the coordinator's triage: `null` equals absent for fields with a default (AD-19); stable error type codes asserted; `Field(description=...)` on every serialized field; `version` exported with an `enum`; `minimum: 0` exported for `seq` and `duration_ms`; sequence fields (`events`, `redaction.paths`, `redaction.env_names`) are tuples (shallow-frozen decision taken for stories 2.2 and 2.3 together). The matrix row "Redaction state default" reads `paths=[]`, `env_names=[]` as JSON input; the model holds `()`.

## Review Triage Log

### Review pass 1 (coordinator triage), 2026-10-23

Eight findings; five patched, one changed from "record" to "apply" by the addendum, two recorded.

| # | Finding | Disposition | Evidence |
| --- | --- | --- | --- |
| 1 | `Annotated[_ExactInt, Field(ge=0)]` exported `"ge": 0`, not `minimum: 0`, because the validator wrapped the int schema before the constraint applied | patched | `_NonNegativeInt = Annotated[int, Field(ge=0), BeforeValidator(_require_integer)]`; both validators still fire; `test_seq_and_duration_ms_export_minimum_zero` asserts `minimum: 0` and no `ge` key for `seq` and for the integer branch of `duration_ms` |
| 2 | `capture: null`, `environment: null`, `redaction: null`, `events[].metadata: null`, `events[].redacted: null` were rejected while absent was accepted (AD-19 writes absent fields as `null`) | patched | `_null_means_absent` as `model_validator(mode="before")` on `Trace` and `TraceEvent`; tests `test_null_capture_environment_and_redaction_read_as_their_defaults`, `test_null_event_metadata_and_redacted_read_as_their_defaults`, `test_null_model_reads_as_none_like_an_absent_key`; `null` for required fields keeps its error (`test_null_for_a_required_trace_field_keeps_its_normal_error`, `test_null_for_a_required_event_field_keeps_its_normal_error`, `test_null_started_at_is_rejected_because_the_field_is_required`) and `null` for an unknown key is still `extra_forbidden` (`test_null_for_an_unknown_key_is_still_an_unknown_key`) |
| 3 | Tests did not assert the custom `error["type"]` codes the loader keys on | patched | `_types` helper; `unsupported_version`, `integer_required`, `timestamp_type`/`timestamp_format`, `seq_not_contiguous`, `finite_number`, `greater_than_equal` asserted; `test_unsupported_version_with_an_unknown_field_reports_both_codes` proves a v2 Trace with an extra field yields both `unsupported_version` and `extra_forbidden`; loader rule recorded in Implementation Notes: prefer `unsupported_version` |
| 4 | No field descriptions; story 2.4 needs one per serialized field and forbids model changes there | patched | `Field(description=...)` on all 43 fields of the ten models; `test_every_serialized_field_has_a_description` walks the root and every `$defs` entry of `Trace.model_json_schema()` |
| 5 | `version` exported as a bare integer; alias name `SchemaVersion` would collide with the Suite version rule | patched | `json_schema_extra={"enum": list(SUPPORTED_VERSIONS["trace"])}`; alias renamed `TraceSchemaVersion`, `__all__` updated; `test_version_exports_an_enum_of_the_supported_trace_versions`, `test_public_names_are_exported_and_the_version_alias_is_trace_specific` |
| 6 | Shallow frozen: list fields mutable after construction, `hash(trace)` raises | applied (addendum) | `events`, `redaction.paths`, `redaction.env_names` are tuples; JSON lists validate (`test_sequence_fields_validate_from_json_lists_into_tuples`), `model_dump(mode="json")` emits arrays (`test_seed_round_trips_through_model_dump_in_json_mode`), schema shows `type: array` (`test_sequence_fields_export_as_json_schema_arrays`), contiguity validator runs on the tuple (all seq tests). Did not fit: `hash(trace)` works only for a Trace with no events because every `TraceEvent.metadata` is a dict and `metadata` stays a mapping; asserted as such in `test_trace_without_events_is_hashable_and_tuples_block_mutation` and `test_payload_fields_are_not_deep_frozen`, stated in the module docstring |
| 7 | `duration_ms` rejects floats; `ge=0` on `seq` | recorded, kept | Consistency Conventions: durations are integer milliseconds; `seq` is a 0-based index |
| 8 | The seed test uses the completed form of the spine seed | recorded | the spine abbreviates events 1 to 3 and writes `"timestamp": "..."`; `SEED` completes the key set with real timestamps (first Implementation Notes entry) |

## Verification

**Commands:**
- `cd packages/python && uv run check` -- expected: gate green, `lint-imports` 7 kept, purity clean on `models`
- `cd packages/python && uv run pytest tests/unit/models/test_trace.py -q` -- expected: every test passes
- `git status --short` -- expected: only `models/trace.py`, `tests/unit/models/test_trace.py`, and this plan

**Manual checks (if no CLI):**
- `git status` shows only the Code Map paths.
