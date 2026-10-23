---
title: 'Suite, defaults, scenario, and assertion configuration models'
type: 'feature'
ticket: '2'
created: '2026-10-23'
status: done
baseline_revision: '05ed167eb483c088cb22a7f48c4bf75e750d4d57'
route: 'full'
route_source: 'pinned'
risk: 'high'
review: 'full'
review_source: 'pinned'
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nothing yet defines the shape of what a user writes. Without `models.assertions` and `models.suite`, the loader (epic 3), the engine (epic 4), the Report (epic 5), and the public API would each have to decide what a Suite, a Scenario, a Suite default, and an Assertion configuration are, and the PRD's load-time rules (AC-2.2, AC-2.5, AC-3.1, AC-3.3, AC-13.2) would have no single home (story 2.2, epic 2 R2 and R5).

**Approach:** Add the six frozen assertion config models and the static discriminated union `AssertionConfig` in `agentproof.models.assertions` (AD-8), and `SuiteDefaults` (with `FixtureDefaults`, `CompareDefaults`, `RedactDefaults`), `Scenario`, and `Suite` in `agentproof.models.suite` (spine Suite seed, AD-3, AD-14). Every rule the story names is a Pydantic validator on the model so every path into a Suite object enforces it: default assertion ids `<type>-<index>`, duplicate assertion ids, the scenario id charset, case-insensitive scenario id uniqueness, Windows device names, and `tool_call_count` with exactly one operator. Validation is dict-in, model-out, with no I/O, clock, env, or randomness (AD-1), and the modules import only `constants`, `models.common`, and Pydantic (AD-2).

**Decisions delegated by the maintainer (2026-10-22, "approve all, you are the owner"):** `version` is `Literal[1]` with a test tying it to `constants.SUPPORTED_VERSIONS["suite"]`; the shared `ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)` is defined once in `models.assertions` and reused by `models.suite` (no new module, so the Code Map stays at four files); default assertion ids are assigned in an after-validator on `Scenario.assertions` through `model_copy(update=...)`, which respects `frozen`; the `tool_call_count` operators are non-negative `int` fields validated with field-level `strict=True` so `"1"`, `1.0`, and `true` are rejected in Python and JSON mode alike (the model-level `strict` AD-3 forbids is still unused); vacuous configurations are rejected at load time (`tool_arguments_match.arguments` and `tool_order.tools` need at least one entry, `final_output_contains.value` and every tool name are non-empty) because an assertion that cannot fail is not evidence.

## Boundaries & Constraints

**Always:** Both modules carry `model_config = ConfigDict(frozen=True, extra="forbid")` on every model with no model-level `strict` (AD-3); they import only the standard library, Pydantic, `agentproof.constants`, and `agentproof.models.common`, never `loading`, `assertions`, `engine`, `io`, or `cli` (AD-2, `.importlinter`); they use none of the names AD-1 bans (TID251 and the purity checker apply); `constants.SCENARIO_ID_RE` and `constants.WINDOWS_DEVICE_NAMES` are the only definitions of the id rule and `models.suite` the only validator of it (AD-14); every validation error names the field path (Pydantic `loc`) and, for id rules, the offending id in its message; every public name has a docstring; `mypy --strict` with the Pydantic plugin passes on `src`; no `from __future__ import annotations` (conventions).

**Never:** No YAML or JSON text parsing in these modules (dicts in only; the test parses the spine seed with `yaml.safe_load`); no file I/O; no changes to `constants.py`, `errors.py`, `models/common.py`, `models/canonical.py`, `pyproject.toml`, `uv.lock`, the check entry point, `.importlinter`, or any shell package; no Trace, result, or Report models (stories 2.3, 2.4); no evaluators or registry (epic 4); the orchestrator commits and pushes, the implementer does not.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| C1 six configs | `{"type": "tool_called", "tool": "x"}` and the other five flat mappings with their PRD fields | one model per type; `type` is the literal; `id` is `None` until the Scenario assigns it; `case_sensitive` defaults to `True` | No error expected |
| C1 unknown type | `{"type": "tool_exists", "tool": "x"}` inside a Scenario | rejected; `loc` ends at `assertions.<i>` and the message names the tag `tool_exists` | `ValidationError` (`union_tag_invalid`) |
| C1 tool_call_count operators | `equals: 1` alone, `greater_than: 0` alone, `less_than: 2` alone | each validates with the other two `None` | No error expected |
| C1 tool_call_count zero or two | none of the three; `equals: 1, less_than: 2` | rejected; message names `equals`, `greater_than`, `less_than` | `ValidationError` (`value_error`) |
| C1 tool_call_count non-integer | `equals: -1`, `equals: "1"`, `equals: 1.0`, `equals: true` | rejected with `loc` ending in `equals` | `ValidationError` |
| C2 spine seed | the Suite YAML seed from the spine, loaded with `yaml.safe_load` in the test | `Suite(version=1, suite="expense-agent", defaults=SuiteDefaults(adapter="fixture", fail_on_missing_trace=True, fixture.deterministic=True, compare.include_arguments=["approve_expense.amount"], redact.env=["OPENAI_API_KEY"]), scenarios=[Scenario(id="reject-over-limit", input={"expense_amount": 5000}, trace="traces/reject-over-limit.trace.json", assertions=[...3])])` with ids `tool_not_called-0`, `tool_call_count-1`, `says-rejected` | No error expected |
| C2 minimal suite | `version`, `suite`, one Scenario with `id`, `input`, one assertion | `defaults` is `SuiteDefaults()` with `adapter=None`, `fail_on_missing_trace=True`, `fixture.deterministic=False`, empty `compare` and `redact` lists; `description`, `skip`, `trace` are `None` | No error expected |
| C2 missing or wrong version | no `version`; `version: "1"`; `version: 2`; `version: true` | rejected; `loc == ("version",)` | `ValidationError` (`missing` / `literal_error`) |
| C2 missing required | Scenario without `assertions`; with `assertions: []`; without `input`; Suite without `scenarios`; `scenarios: []` | rejected; `loc` names `scenarios.<i>.assertions` / `scenarios.<i>.input` / `scenarios` | `ValidationError` (`missing` / `too_short`) |
| C3 default ids | three assertions, the third with `id: says-rejected` | ids `tool_not_called-0`, `tool_call_count-1`, `says-rejected`; index is the 0-based position in the Scenario list, not per type | No error expected |
| C3 duplicate assertion id | two assertions both `id: dup`; or an explicit `tool_called-0` colliding with the generated id of assertion 0 | rejected; message names `dup`, the Scenario id, and both positions; `loc == ("scenarios", i, "assertions")` | `ValidationError` (`value_error`) |
| C3 scenario id charset | `reject-over-limit`, `a.b_c`, `R1`, 64 chars pass; `-bad`, `has space`, `é`, 65 chars, `""` fail | rejected naming the id in the message; `loc == ("scenarios", i, "id")` | `ValidationError` (`value_error`) |
| C3 device names | `con`, `COM1`, `Nul`, `conin$` (any case) | rejected naming the id and "Windows device name" | `ValidationError` (`value_error`) |
| C3 case-insensitive duplicate | scenarios `reject` and `Reject` | rejected; message names both ids and positions; `loc == ("scenarios",)` | `ValidationError` (`value_error`) |
| C3 suite id | `suite: expense-agent` passes; `suite: "bad id"` and `suite: NUL` fail with `loc == ("suite",)` | same rule as scenario ids (spine seed: "same charset as scenario ids") | `ValidationError` |
| C4 unknown field | extra key at Suite, `defaults`, `defaults.redact`, Scenario, and assertion level | rejected; `loc` is the full path to the extra key | `ValidationError` (`extra_forbidden`) |
| C4 frozen | `suite.suite = "x"`, `scenario.id = "x"`, `defaults.adapter = "x"`, `config.tool = "x"` | assignment raises | `ValidationError` (`frozen_instance`) |
| NaN in input | `input: {"amount": nan}` | rejected (epic R4: models reject NaN and infinity) | `ValidationError` (`finite_number`) |

</frozen-after-approval>

## Code Map

- `packages/python/src/agentproof/models/assertions.py` -- new; `MODEL_CONFIG: Final[ConfigDict] = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)`; `ToolName = Annotated[str, Field(min_length=1)]`; `Count = Annotated[int, Field(strict=True, ge=0)]`; `ARGUMENT_PATH_PATTERN = r"^[^.\s]+(\.[^.\s]+)*$"` and `ArgumentPath = Annotated[str, Field(pattern=ARGUMENT_PATH_PATTERN)]` so Python validation and the exported JSON Schema state one grammar; `Operator = Literal["equals", "greater_than", "less_than"]` and `OPERATORS`; `class AssertionConfigBase(BaseModel)` with `model_config = MODEL_CONFIG` and `id: str | None = Field(default=None, min_length=1)`; `ToolCalled(type: Literal["tool_called"], tool: ToolName)`; `ToolNotCalled(type: Literal["tool_not_called"], tool)`; `ToolCallCount(type: Literal["tool_call_count"], tool, equals | greater_than | less_than: Count | None = None)` plus `@model_validator(mode="after")` requiring exactly one operator and the read-only property `operator -> tuple[Operator, int]`; `ToolArgumentsMatch(type: Literal["tool_arguments_match"], tool, arguments: dict[ArgumentPath, JsonValue])` with `min_length=1` (a plain dict, not deep-frozen); `ToolOrder(type: Literal["tool_order"], tools: tuple[ToolName, ...])` with `min_length=1`; `FinalOutputContains(type: Literal["final_output_contains"], value: str (min_length=1), case_sensitive: bool = True)`; `ASSERTION_MODELS` (the six classes in order); `AssertionConfig = Annotated[ToolCalled | ToolNotCalled | ToolCallCount | ToolArgumentsMatch | ToolOrder | FinalOutputContains, Field(discriminator="type")]`; `ASSERTION_TYPES: Final[tuple[str, ...]]` derived at import time from the members' `type` literals (the registry test in epic 4 compares against it).
- `packages/python/src/agentproof/models/suite.py` -- new; `FixtureDefaults(deterministic: bool = False)`; `CompareDefaults(include_arguments: tuple[CompareArgumentPath, ...] = ())` where `CompareArgumentPath` adds an `AfterValidator` requiring two or more dotted segments (`<tool>.<argument path>`); `RedactDefaults(keys: tuple[Name, ...] = (), paths: tuple[ArgumentPath, ...] = (), env: tuple[Name, ...] = ())` with `Name = Annotated[str, Field(min_length=1)]`; `SuiteDefaults(adapter: str | None = None, fail_on_missing_trace: bool = True, fixture: FixtureDefaults, compare: CompareDefaults, redact: RedactDefaults)` with `default_factory` sub-models; `Scenario(id: str, description: str | None = None, skip: str | None = None (min_length=1), input: dict[str, JsonValue], trace: str | None = None (min_length=1), assertions: tuple[AssertionConfig, ...] (min_length=1))` with `@field_validator("id")` → `validate_id(value, kind="scenario id")`, `@field_validator("skip", mode="before")` rejecting a present null or non-string ("skip needs a reason string"), and `@field_validator("assertions", mode="wrap")` that, over the raw list, fills missing ids with `f"{item['type']}-{index}"`, records duplicates as `duplicate_assertion_id` findings at `(index, "id")`, then runs the element validation and raises the findings merged with the element errors; `Suite(version: Literal[1], suite: str, description: str | None = None, defaults: SuiteDefaults, scenarios: tuple[Scenario, ...] (min_length=1))` with `@field_validator("version", mode="before")` (exact `int` only), `@field_validator("suite")` → the same id rule, and `@field_validator("scenarios", mode="wrap")` recording case-insensitive duplicates as `duplicate_scenario_id` findings at `(index, "id")` and merging them with the element errors; helpers `_pass_through` (re-emits nested line errors through `ValidationError.from_exception_data`, dropping pydantic-core's spurious tuple `too_short` when an element failed) and `_validate_with_findings`; module-level `validate_id(value: str, *, kind: str) -> str` (fullmatch `SCENARIO_ID_RE`, then `value.upper() in WINDOWS_DEVICE_NAMES`), the one implementation AD-14 names.
- `packages/python/src/agentproof/models/__init__.py` -- unchanged (no re-exports; AD-15 public API is a later story).
- `packages/python/tests/unit/models/test_assertions_config.py` -- new; criterion 1 and the assertion-level rows of criterion 4: every type constructs with its fields; `id` defaults to `None`; `case_sensitive` defaults `True`; each `tool_call_count` operator alone passes; zero and two operators fail naming the three fields; negative, string, float, and bool counts fail at `equals`; empty `arguments`, empty `tools`, empty `value`, empty tool name, malformed argument path fail; unknown field fails naming it; assignment raises; `ASSERTION_TYPES` equals the union's literals; `AssertionConfig` validated through a `TypeAdapter` picks the right class and rejects an unknown tag.
- `packages/python/tests/unit/models/test_suite.py` -- new; criteria 2 to 4: the spine seed (YAML text in the test, `yaml.safe_load`) validates to the expected `Suite`; the minimal suite gives the documented defaults; the `version` literal equals `SUPPORTED_VERSIONS["suite"]`; missing or wrong `version`, missing `scenarios`, `input`, `assertions`, empty lists; default ids and the positional index; duplicate assertion ids (explicit and explicit-versus-generated); charset, device-name, case-insensitive-duplicate, and `suite` id rules; unknown fields at each level with the full `loc`; frozen assignment on each model; NaN in `input`. Each failing test asserts the `loc` tuple and that the message names the id or field.
- Existing to respect: `.importlinter` layers (`models` above `constants` above `errors`); the purity checker and TID251 on `models`; the exception-taxonomy scan (no class named `*Error` outside `errors.py`); ruff `E, F, I, UP, B, TID` at line length 100; `mypy --strict` with the Pydantic plugin.

## Tasks & Acceptance

**Execution:**
- [x] `packages/python/src/agentproof/models/assertions.py` -- the six config models, `MODEL_CONFIG`, `AssertionConfig`, `ASSERTION_TYPES` -- criterion 1, 4
- [x] `packages/python/src/agentproof/models/suite.py` -- `FixtureDefaults`, `CompareDefaults`, `RedactDefaults`, `SuiteDefaults`, `Scenario`, `Suite`, `validate_id` -- criteria 2, 3, 4
- [x] `packages/python/tests/unit/models/test_assertions_config.py` -- one passing and one failing test per criterion-1 rule, assertion-level criterion-4 rows -- criteria 1, 4
- [x] `packages/python/tests/unit/models/test_suite.py` -- spine seed, defaults, ids, frozen and forbid rows -- criteria 2, 3, 4
- [x] local verification -- `uv run check` green; caches removed

**Acceptance Criteria:**
- Given `agentproof.models.assertions`, when imported, then six frozen config models with the PRD fields and an optional `id` exist, `AssertionConfig` is the discriminated union on `type`, and `tool_call_count` with zero or two operators raises a validation error naming the fields.
- Given the spine's Suite YAML seed loaded to a dict, when validated, then it yields the Suite described in the matrix with `version == 1` and every default and Scenario field in place.
- Given a Suite dict, when validated, then assertions without `id` receive `<type>-<0-based index>`, and case-insensitive duplicate scenario ids, ids outside `SCENARIO_ID_RE`, Windows device names, and duplicate assertion ids within a Scenario raise validation errors naming the id and the path.
- Given any model in this story, when an unknown field is supplied, validation fails naming the field path; when an attribute is assigned after construction, assignment raises.

## Implementation Notes

**2026-10-23, implementer (worktree `D:\AgentProof-wt-2-2`, branch `story/2-2-config-models`, baseline `05ed167`).**

Decisions taken where the plan left room:

- `version: Literal[1]` alone accepts `True` and `1.0` in Python mode, and Pydantic refuses `Strict()` on a literal schema (`RuntimeError: Unable to apply constraint 'strict' to schema of type 'literal'`). A `mode="before"` field validator on `Suite.version` rejects any input whose exact type is not `int` (message `version must be an integer schema version, got <value>`), and the literal then rejects other integers with `literal_error`. The `version` field's `get_args` equals `SUPPORTED_VERSIONS["suite"]` by test.
- `tool_call_count` operators are `Annotated[int, Field(strict=True, ge=0)]` (field-level, not model-level strict): `"1"`, `1.0`, and `true` all fail with `int_type` at `equals`; `-1` fails with `greater_than_equal`. The exactly-one rule is an after model validator raising `ValueError("tool_call_count takes exactly one of equals, greater_than, less_than; got <none | names>")`; inside a Suite its `loc` is `scenarios.<i>.assertions.<j>.tool_call_count` (the discriminator tag is part of the path for tagged unions). `ToolCallCount.operator` returns `(name, bound)` for the engine.
- Default assertion ids are filled in an after field validator on `Scenario.assertions` with `model_copy(update={"id": ...})`, which respects `frozen`; the index is the 0-based position in the Scenario list (not a per-type counter), so `[tool_called, tool_called, final_output_contains]` gets `tool_called-0`, `tool_called-1`, `final_output_contains-2`. An explicit id colliding with a generated one is a duplicate. The duplicate message is `scenario '<id>': duplicate assertion id '<x>' at assertions[<i>] and assertions[<j>]` with `loc` `scenarios.<n>.assertions`; the Scenario id comes from `info.data` (validated before `assertions` by field order).
- `validate_id(value, *, kind)` in `models.suite` is the one implementation AD-14 names; `Scenario.id` uses `kind="scenario id"` and `Suite.suite` uses `kind="suite id"` (spine seed: "same charset as scenario ids"). Messages quote the id and, for the charset, the regex pattern; the device-name message says "reserved Windows device name". Case-insensitive duplicate scenario ids compare `str.lower()` (the charset is ASCII) and the message names both ids and positions.
- `ArgumentPath` (shared by `tool_arguments_match.arguments` keys, `compare.include_arguments`, and `redact.paths`) is a non-empty string with no empty dotted segment; no further syntax check, since OQ-7 has no wildcards. Vacuous configurations are rejected: empty `arguments`, empty `tools`, empty `value`, empty tool name, empty assertion `id`, empty `skip`, `trace`, `adapter`, and empty `redact.keys`/`env` names.
- `MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)` lives in `models.assertions` and `models.suite` reuses it; `allow_inf_nan=False` makes NaN and infinity inside `input` fail with `finite_number` (epic R4), at no cost to this story. No new module was needed.
- Defaults chosen where the spine says only "all optional": `adapter=None` (the runner decides what an unset adapter means; the Report snapshot serializes `null`), `fixture.deterministic=False`, `fail_on_missing_trace=True` (Glossary), empty `compare.include_arguments` (AC-26.5), empty `redact` lists (the built-in key set lives in `redaction`, AD-10). `Scenario.input` is required (the story lists it without "optional").
- The spine seed is copied into `test_suite.py` as YAML text and parsed with `yaml.safe_load` in the test only; every key and value is verbatim, one trailing comment was shortened to fit the 100-column limit. The seed's inline comment "default tool_called-2 style" describes the shape, not the value: the third assertion has an explicit id, and the generated ids are `tool_not_called-0` and `tool_call_count-1`.
- `conin$` and `conout$` cannot be tested as device-name rejections: `$` is outside `SCENARIO_ID_RE`, so the charset rule rejects them first. The device test uses `con`, `CON`, `Nul`, `COM1`, `lpt9`, `com0`, `AUX`, `PRN`, and a near-miss test proves `con.txt`, `console`, `com10`, `nul-1`, `lpt` are accepted.

Observed:

- `uv sync` (uv 0.13.5) created this worktree's `.venv` on CPython 3.13.16 (29 packages; pydantic 2.14.1, pydantic-core 2.50.1).
- `uv run check`: `ruff check` "All checks passed!" and the purity checker silent; `ruff format --check` "40 files already formatted"; `mypy --strict` "Success: no issues found in 20 source files"; `lint-imports` "Contracts: 7 kept, 0 broken."; `pytest` 385 passed in 22.16s (was 231 before this story; +154: `test_assertions_config.py` 53, `test_suite.py` 101 minus the 22 canonical and 3 common already counted, i.e. 81 new in `test_suite.py`). Exit 0.
- `uv run python -m agentproof_devtools.purity src/agentproof/models` → no output, exit 0.
- `uv run python -c "...Suite.model_validate({...}).scenarios[0].assertions[0].id"` → `tool_called-0`.
- `uv run --python 3.12 --locked --isolated pytest tests/unit/models` → 159 passed under CPython 3.12 (`Self` import and the `type` alias exercised at the lowest CI version). 3.14 and 3.15 are not installed locally; CI covers them.
- `git status --short` shows only the four Code Map paths and this plan file, all untracked.
- Not done: no commit, no push (orchestrator's job). Caches created by the runs (`.ruff_cache`, `.mypy_cache`, `.pytest_cache`, `__pycache__`) were removed from the worktree; `.venv` was kept.

Risks and open points for the orchestrator:

- Four defaults are judgment calls the spine does not fix: `adapter=None`, `fixture.deterministic=False`, required `Scenario.input`, and vacuous-configuration rejection (`min_length=1` on `arguments`, `tools`, `value`). Each is a one-line change if the maintainer prefers otherwise, but a change after the schema is published is a version bump (AD-3).
- `redact.keys` are stored as given; AD-10 says matching is case-insensitive, which is the `redaction` module's job, not a model normalization.
- `Status` of the plan frontmatter `review` was set to `'full'` because the story's risk is high; the orchestrator may pin a different lens set.

**2026-10-23, review-pass-1 fixes (implementer, same worktree).** Eight findings from the coordinator's triage, each applied as asked, with these mechanics:

- Finding 1 and 6 (uniqueness rules beside element errors, per-item loc): the two uniqueness checks and the default-id fill moved to `mode="wrap"` field validators over the raw lists. A `mode="before"` validator alone cannot satisfy "all violations": raising from it skips the element validation, so the sibling's error would be lost. The wrap form collects findings over the raw dict items (`item.get("id")`, `item.get("type")`, non-mappings skipped), calls the inner handler, and when either side has errors raises `ValidationError.from_exception_data` with the findings and the pass-through of the inner line errors; pydantic-core prefixes the field loc. Findings are `PydanticCustomError`s typed `duplicate_assertion_id` / `duplicate_scenario_id` at `(index, "id")` of the later duplicate, with the messages unchanged in wording (values pre-quoted with `repr`, since the template language has no `!r`). Known error types are re-emitted with their `ctx` so their messages are rebuilt verbatim; unknown (our custom) types keep their rendered message. pydantic-core's tuple validator counts only validated items for `min_length`, so one invalid element also produced "at least 1 item after validation, not 0" at the field; `_pass_through` drops that line when an element error exists (a genuinely empty input keeps its `too_short`). `tool_order.tools: [""]` is outside the wrap and still shows both lines; noted for the loader.
- Finding 2 (shallow frozen): `scenarios`, `assertions`, `tools`, `include_arguments`, `redact.keys/paths/env` are tuples with the same `min_length` rules; JSON lists validate, `model_dump(mode="json")` emits arrays, `model_dump()` keeps tuples, `model_json_schema()` exports `type: array` with `minItems`. `input` and `arguments` stay dicts; both module docstrings say mapping fields are not deep-frozen. `hash(ToolOrder(...))` works; `suite.scenarios.append` raises `AttributeError`.
- Finding 3 (`skip`): implemented as `@field_validator("skip", mode="before")` rather than a model validator: a before field validator runs only when the key is present (defaults bypass it), so absent stays `None`, and the error lands at `scenarios.<i>.skip` instead of the Scenario root. Message: `skip needs a reason string; presence means skipped, got <value>`.
- Finding 4: `CompareArgumentPath` = the pattern plus an `AfterValidator` requiring a `.`; message `include_arguments entry 'amount' must be <tool>.<argument path>, for example approve_expense.amount`.
- Finding 5: `ArgumentPath = Annotated[str, Field(pattern=r"^[^.\s]+(\.[^.\s]+)*$")]`; `' a . b '`, `'a b'`, `'a\tb'`, `''`, `'a..b'`, `'.a'`, `'a.'` fail with `string_pattern_mismatch` (the loc carries the key and `input` the value). Pydantic exports a constrained dict key as `patternProperties` (not `propertyNames`), so the schema and the validator state the same grammar; story 2.4 should expect `patternProperties` on `arguments`. The non-empty-name rule on `redact.keys/env` became `Annotated[str, Field(min_length=1)]` items (error `string_too_short` at the index) for the same schema-agreement reason.
- Finding 7: `ASSERTION_TYPES = tuple(get_args(model.model_fields["type"].annotation)[0] for model in ASSERTION_MODELS)`; the existing test still asserts the literal six-tuple and now also `ASSERTION_MODELS == MODELS`.
- Finding 8: `Operator = Literal["equals", "greater_than", "less_than"]`, `OPERATORS` runtime tuple, `ToolCallCount.operator -> tuple[Operator, int]`.

Verified after the fixes: `uv run check` → `ruff check` "All checks passed!" and purity silent; `ruff format --check` "40 files already formatted"; `mypy --strict` "Success: no issues found in 20 source files"; `lint-imports` "Contracts: 7 kept, 0 broken."; `pytest` 409 passed in 18.45s (+24 over the first pass: `test_assertions_config.py` 60, `test_suite.py` 123 minus the 22 canonical and 3 common, i.e. 98 in the suite module; `tests/unit/models` totals 183). Exit 0. `uv run --python 3.12 --locked --isolated pytest tests/unit/models` → 183 passed. Caches removed again; `git status --short` still shows only the four Code Map paths and this plan.

## Plan Change Log

- 2026-10-23, review pass 1: the frozen Intent's delegated decision "default assertion ids are assigned in an after-validator on `Scenario.assertions` through `model_copy(update=...)`" is superseded by the wrap-validator-over-raw-items design (finding 1); sequence fields are tuples (finding 2); the matrix rows "C3 duplicate assertion id" and "C3 case-insensitive duplicate" now resolve to `loc == ("scenarios", i, "assertions", j, "id")` / `("scenarios", i, "id")` with types `duplicate_assertion_id` / `duplicate_scenario_id` instead of a `value_error` at the list. The frozen block itself is left as approved; this entry records the deltas.

## Review Triage Log

### Review pass 1 (coordinator triage), 2026-10-23

Eight findings, all accepted and patched in this worktree.

| # | Finding | Disposition | Where |
| --- | --- | --- | --- |
| 1 | Duplicate-id rules did not fire when a sibling item was invalid (after-validators are skipped on element failure), so the loader could not print all violations (AC-2.4) | patched: wrap validators over the raw lists collect findings and merge them with the element errors | `suite.py` `Scenario._assign_and_check_ids`, `Suite._unique_ids_case_insensitively`, `_pass_through`, `_validate_with_findings`; tests `test_duplicate_scenario_id_is_reported_even_when_that_scenario_is_invalid`, `test_duplicate_assertion_id_is_reported_even_when_a_sibling_is_invalid` |
| 2 | Models were frozen only at the top level; list fields stayed mutable and unhashable | patched: every sequence field is a tuple (shallow frozen), mapping fields documented as not deep-frozen | both modules and docstrings; tests `test_tool_order_is_hashable_and_dumps_tools_as_a_json_array`, `test_sequence_fields_are_tuples_that_cannot_be_appended_to`, `test_json_dump_writes_arrays_and_json_schema_exports_array_types` |
| 3 | `skip: null` validated as "not skipped" although presence means skipped | patched: a present null or non-string `skip` fails with "skip needs a reason string" (before field validator; absent stays `None`) | `Scenario._present_skip_is_a_reason`; tests `test_present_skip_must_be_a_reason_string`, `test_absent_skip_is_none_and_a_present_reason_is_kept` |
| 4 | `compare.include_arguments` accepted a bare argument path without the tool segment | patched: entries need two or more dotted segments, error names the entry | `CompareArgumentPath`, `_two_segments`; test `test_compare_include_arguments_are_tool_dot_argument_paths` |
| 5 | `ArgumentPath` was a Python-only `AfterValidator`, invisible to the exported JSON Schema | patched: `Field(pattern=ARGUMENT_PATH_PATTERN)`; whitespace now rejected too; dict keys export as `patternProperties` (documented for story 2.4) | `assertions.py`; tests `test_tool_arguments_match_rejects_a_malformed_path_naming_it`, `test_argument_path_pattern_is_in_the_exported_json_schema` |
| 6 | Duplicate errors were located at the list, not the offending item | resolved by 1: loc is `(…, index, "id")` of the later duplicate | tests `test_duplicate_assertion_ids_in_one_scenario_are_rejected_naming_id_and_path`, `test_scenario_ids_differing_only_by_case_are_rejected_naming_both` |
| 7 | `ASSERTION_TYPES` was a hand-copied tuple that could drift from the union | patched: derived at import time from the members' `type` literals | `assertions.py`; test `test_six_models_exist_with_their_type_literals_in_order` |
| 8 | `ToolCallCount.operator` returned `tuple[str, int]` | patched: `tuple[Operator, int]` with `Operator` a `Literal` and `OPERATORS` its runtime tuple | `assertions.py`; test `test_operators_tuple_matches_the_operator_literal_in_order` |

## Verification

**Commands:**
- `cd packages/python && uv run check` -- expected: gate green, `lint-imports` 7 kept, purity clean on `models`
- `cd packages/python && uv run python -c "from agentproof.models.suite import Suite; print(Suite.model_validate({'version': 1, 'suite': 's', 'scenarios': [{'id': 'a', 'input': {}, 'assertions': [{'type': 'tool_called', 'tool': 't'}]}]}).scenarios[0].assertions[0].id)"` -- expected: `tool_called-0`
- `cd packages/python && uv run python -m agentproof_devtools.purity src/agentproof/models` -- expected: no output, exit 0

**Manual checks (if no CLI):**
- `git status` shows only the Code Map paths plus this plan file.
