---
title: 'Generated JSON Schemas, drift test, and schema v1 fixtures'
type: 'feature'
ticket: '5'
created: '2026-10-23'
status: 'built'
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

**Problem:** Other stacks (the deferred viewer, CI consumers, anyone emitting a Trace from a non-Python agent) need a published contract for a Suite, a Trace, and a Report, and that contract must be the Pydantic models themselves, not a copy that can drift (spine AD-4; ADR-004). The repository has the models (stories 2.2 to 2.4) but no `schemas/` files, no exporter, no drift test, and no fixture archive for schema version 1, so nothing an old reader can be tested against when version 2 arrives (PRD NFR-8) and nothing proving the malformed-input classes of NFR-5 fail with the error class and field path the model promises.

**Approach:** Add `agentproof.models.export_schemas` with pure `schema_for(kind)` (the model's `model_json_schema()` plus `$schema` 2020-12 and an `$id` naming `<kind>-v<version>`) and `render(kind)` (Canonical form through `canonical.dumps`), and a `main(argv)` run by `python -m agentproof.models.export_schemas` that writes `suite-v1.schema.json`, `trace-v1.schema.json`, `report-v1.schema.json` as UTF-8, no BOM, LF. A drift test regenerates each schema in memory and compares to the committed file byte for byte, naming the file on a mismatch, and asserts every property (root and `$defs`) has a description and every `version` property its `enum`. A fixture archive under `tests/fixtures/schema/v1/valid/` and `invalid/` holds the spine seeds in completed form and one file per malformed-input class, invalid files named `<kind>__<error type>__<field path>.json`; every valid fixture validates with the model and with `jsonschema` (Draft 2020-12, `referencing.Registry()` with no retrieve hook), every invalid fixture fails the model with the named error type at the named path, and a per-fixture flag states whether `jsonschema` also rejects it. `jsonschema` and `referencing` enter the dev group only; a subprocess test proves importing `agentproof` and every `agentproof.models` module never imports them (AD-16). Where a schema is wrong the model is fixed, never the file: descriptions on the story-2.2 Suite and assertion-config models, an `enum` on `Suite.version`, and an anchored ECMA-262-compatible RFC 3339 `pattern` on `Timestamp` (deferred-work entries routed from the 2.4 review).

**Decisions delegated by the maintainer (2026-10-22, "approve all, you are the owner"):** where the spine fixes a shape it is followed; where it is silent the simplest shape is chosen and recorded under "Decisions for review".

## Boundaries & Constraints

**Always:** `export_schemas.py` imports only the standard library, Pydantic, `constants`, and sibling `models.*` modules (AD-2); `schema_for` and `render` are pure; the module's only I/O is the write in `main`, marked `# purity: ok`; schemas are draft 2020-12 in Canonical form; every property of every schema has a non-empty `description`; `jsonschema` and `referencing` are imported only under `tests/`; the fixture test never uses `RefResolver`; model changes are schema-only fixes that leave validation behaviour and every existing test unchanged; `mypy --strict` passes; the orchestrator commits and pushes.

**Never:** No hand edit of a `*.schema.json` (AD-4); no runtime dependency (AD-16); no change to which values a model accepts, its error types, or locations; no new exception class; no YAML in the fixture test; no network; no execution of fixture content.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Export writes three files (criterion 1) | `uv run python -m agentproof.models.export_schemas` from `packages/python` | three files, UTF-8 no BOM, LF only, byte-identical to `render(kind)` | exit 0; unknown kind to `schema_for` raises `KeyError`; two arguments exit 2 |
| Schema shape (criterion 1) | `schema_for("trace")` | `$schema` 2020-12, `$id` `urn:agentproof:schema:trace-v1`, `title` `Trace`, `version.enum == [1]`, `additionalProperties: false` | none |
| Descriptions everywhere (criterion 1) | every property of root and `$defs` | non-empty `description` | test names `<kind>: <Model>.<field>` |
| Drift (criterion 2) | committed files | byte-equal to `render(kind)` | test fails naming the file |
| Hand edit (criterion 2) | a copy with one byte changed | comparison fails, message names the file | `AssertionError` |
| Timestamp pattern | `started_at`, `ended_at`, `created_at`, event `timestamp` | anchored pattern equal to `^` + `RFC3339_WITH_OFFSET.pattern` + `$` | none |
| Valid fixtures (criterion 3) | every `valid/*.json` | validates with the model and with `jsonschema` | test names fixture |
| Invalid fixtures (criterion 3) | every `invalid/<kind>__<type>__<loc>.json` | `ValidationError` with that `type` at that `loc` | test lists errors found |
| jsonschema verdict | `JSONSCHEMA_REJECTS` flag per fixture | rejects exactly the `True` ones; `False` ones (duplicate ids, seq gap, counts mismatch) pass it; `None` (NaN) is not JSON | flag mismatch fails |
| Dev-only (criterion 4) | `python -I` subprocess importing `agentproof` and every models module | `jsonschema` and `referencing` not in `sys.modules`; both installed | test names module |
| Runtime deps unchanged | `pyproject.toml` | `test_runtime_dependencies_are_unchanged` passes | none |

</frozen-after-approval>

## Code Map

- `packages/python/src/agentproof/models/export_schemas.py` -- new, PURE: `SCHEMA_URI`, `KINDS`, `schema_version`, `schema_id`, `file_name`, `schema_for`, `render`. No `main`, no I/O, no purity markers.
- `schemas/{suite,trace,report}-v1.schema.json` (repository root) -- new; generated, never edited. Outside the wheel entirely.
- `packages/python/devtools/src/agentproof_devtools/export_schemas.py` -- new; `main(argv=None)`, `default_output_dir()`; resolves the repository root as `check.py` does and writes the three files (UTF-8, no BOM, LF). Run as `python -m agentproof_devtools.export_schemas`.
- `models/suite.py`, `models/assertions.py` -- `Field(description=...)` on every field (44 were missing); `Suite.version` `enum`. No validation change.
- `models/trace.py` -- `TIMESTAMP_PATTERN` via `Field(json_schema_extra=...)` on `Timestamp`; in `__all__`.
- `packages/python/tests/unit/test_schema_drift.py`, `test_fixtures_v1.py` -- new.
- `packages/python/tests/fixtures/schema/v1/valid/` (5 files) and `invalid/` (22 files).
- `packages/python/pyproject.toml`, `uv.lock` -- `jsonschema>=4.26` (the spine's dependency table), `referencing>=0.36` in the dev group.
- `.gitattributes` -- unchanged: the existing root rule `schemas/*.json text eol=lf` already covers `schemas/` at the repository root (an interim `packages/python/schemas` rule was removed with the move).
- `_bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md` -- **Code Map exception:** AD-4's Rule names the new invocation (see Plan Change Log).
- `_bmad-output/initiative-agentproof-mvp/deferred-work.md` -- **Code Map exception:** two entries (Scenario.skip null round trip; Suite version error code), routed to story 2.7 or 3.3.

**Decisions for review:**

1. **Schema location (review finding 1):** the repository root `schemas/`, as the spine's Structural Seed and the epic's touch point say. The files are outside `packages/python`, hence outside the wheel, which closes the "ships in the wheel" concern behind finding 2.
2. **`$id`:** `urn:agentproof:schema:<kind>-v<version>`, absolute, no domain or distribution name (ADR-000). `title` stays the model name. `jsonschema` 4.26.0 resolves `#/$defs/...` the same under a URN, relative, or absent `$id`.
3. **No purity markers (review finding 2; reverses the earlier maintainer-approved decision):** `models.export_schemas` is pure (no `main`, no I/O, nothing to mark). The writer is `agentproof_devtools.export_schemas`, in the devtools workspace member that never ships in the wheel. AD-4's invocation text is amended accordingly (Plan Change Log).
4. **Descriptions beyond the deferred entry:** all 44 undescribed Suite, Scenario, defaults, and assertion-config properties, since criterion 1 says every serialized field.
5. **`Suite.version` enum:** `Literal[1]` exports `const: 1`; the `enum` is added so all three `version` properties share one shape.
6. **Pattern via `json_schema_extra`, not `Field(pattern=)`:** the latter runs a second regex in pydantic-core and changes the error code from `timestamp_format`. The pattern derives from `RFC3339_WITH_OFFSET`, so there is one grammar.
7. **Fixture naming:** `<kind>__<error type>__<dotted loc>.json`; integer segments are list indexes.
8. **NaN fixture:** bare `NaN` token in a `.json`; `json.loads` accepts it by default, no schema validator can read it (flag `None`). Epic 3's loader must pass `parse_constant` to reject it.
9. **Suite `version: 2` is `literal_error`; Trace and Report give `unsupported_version`.** Recorded, not fixed (cross-model decision); in deferred-work.md routed to story 2.7.
10. **Known gap, not fixed:** `Scenario.skip` rejects a present `null` while `model_dump(mode="json")` writes `skip: null` and the schema accepts it (AD-19 defect from 2.2). Kept as strict `xfail` in `test_fixtures_v1.py`; in deferred-work.md routed to story 2.7 or 3.3. `valid/suite.json` is the dump with the null `skip` dropped.
11. **Dependency bounds (review finding 5):** `jsonschema>=4.26` per the spine's dependency table, `referencing>=0.36` (locked at 4.26.0 and 0.37.0).

## Tasks & Acceptance

**Execution:**
- [x] `models/suite.py`, `models/assertions.py`: descriptions; `Suite.version` enum -- criterion 1
- [x] `models/trace.py`: `TIMESTAMP_PATTERN` -- criterion 1, deferred work
- [x] pure `models/export_schemas.py`, devtools writer, and the generated root `schemas/*.schema.json` -- criterion 1
- [x] `tests/unit/test_schema_drift.py` -- criteria 1, 2, 4
- [x] `tests/fixtures/schema/v1/**` and `tests/unit/test_fixtures_v1.py` -- criterion 3
- [x] `pyproject.toml` dev group, `uv lock`; `.gitattributes`; `deferred-work.md` entries -- criterion 4
- [x] local verification (see Implementation Notes)

**Acceptance Criteria:**
- Given `python -m agentproof_devtools.export_schemas`, then three Canonical schema files are written under the repository's `schemas/`, every property has a description, and they equal `agentproof.models.export_schemas.render` byte for byte.
- Given the committed schemas, when regenerated in memory, then they match; a hand-edited copy fails naming the file.
- Given the fixture archive, then every valid fixture validates with the model and `jsonschema`, and every invalid fixture fails the model with the error type and path its name states.
- Given a subprocess importing `agentproof` and every `agentproof.models` module, then `jsonschema` and `referencing` are not in `sys.modules`, and runtime dependencies are unchanged.

## Implementation Notes

**2026-10-23, implementer (worktree `D:\AgentProof-wt-2-5`, branch `story/2-5-json-schemas`, baseline `fca6286`; rebuilt after an environment restart removed the first worktree).** Schemas generated with Pydantic 2.14.1 (pydantic-core 2.50.1) on CPython 3.13.16; jsonschema 4.26.0, referencing 0.37.0 (dev only).

- Findings and decisions are numbered 1 to 11 under "Decisions for review". Schema oddities seen: the discriminated assertion union exports `oneOf` plus `discriminator`; `JsonValue` is a recursive `$defs` entry; `arguments` exports `patternProperties`; Suite `version` exports both `const` and `enum`. The two real model defects found (null `skip` round trip; Suite `literal_error` vs `unsupported_version`) are NOT fixed and are in `deferred-work.md`.
- `uv run check` exit 0: `ruff check` "All checks passed!" (purity silent), `ruff format --check` "49 files already formatted", `mypy --strict` "Success: no issues found in 24 source files", `lint-imports` "Contracts: 7 kept, 0 broken.", `pytest` 866 passed, 3 xfailed (the xfails are decision 10).
- `uv run --python 3.12 --locked --isolated pytest tests/unit -q -p no:cacheprovider` -> 861 passed, 3 xfailed.
- Rerunning `uv run python -m agentproof.models.export_schemas` after the final code changed no file; the three schema files hold 0 CR bytes and no BOM (suite 19776, trace 15546, report 31045 bytes). `test_runtime_dependencies_are_unchanged` passes. `uv.lock` gained attrs, jsonschema, jsonschema-specifications, referencing, rpds-py (dev group).
- Fixtures were generated once by a scratchpad script (not committed); the files are the artifact. Caches removed outside `.venv`.
- Review round 1 re-verification: `uv run check` exit 0 (ruff "All checks passed!", format "50 files already formatted", mypy "Success: no issues found in 24 source files", `lint-imports` "Contracts: 7 kept, 0 broken.", pytest 867 passed, 3 xfailed); `uv run --python 3.12 --locked --isolated pytest tests/unit -q -p no:cacheprovider` 862 passed, 3 xfailed; regeneration changes no file; 0 CR bytes in the root `schemas/` files. Paths above that say `packages/python/schemas` or `agentproof.models.export_schemas` as a command are superseded by the Plan Change Log.
- Not done: no commit, push, or PR (the original brief said not to; the later coordinator message asked for them, but only the user can authorize that, so the orchestrator should do it).

## Plan Change Log

- 2026-10-23 (implementer): `.gitattributes` and `deferred-work.md` named as Code Map exceptions; descriptions extended to every Suite and assertion-config field.
- 2026-10-23 (review round 1, orchestrator-directed): **architecture amendment to AD-4.** The Rule text "produced by `python -m agentproof.models.export_schemas`" becomes "produced by `python -m agentproof_devtools.export_schemas` (a devtools script that writes the text of the pure `agentproof.models.export_schemas.render`)". Reason: AD-1 forbids file I/O in `models`; keeping the writer there needed `# purity: ok` exemptions, and the devtools member (never in the wheel, outside `.importlinter`) is the existing home for dev-time entry points. The pure functions stay in `models` so the drift test needs no I/O in core. The frozen Approach/Matrix text above still quotes the old command; this entry supersedes it. Schemas moved to the repository root (finding 1).
- 2026-10-23: the first worktree was lost to an environment restart before anything was committed; the story was rebuilt from scratch in a recreated worktree on the same branch, to the same design.

## Review Triage Log

### Review round 1 (coordinator), 2026-10-23

| # | Finding | Disposition | Evidence |
| --- | --- | --- | --- |
| 1 | Schemas placed under `packages/python/`; spine and epic say repository root | patched: `schemas/` at the root; `.gitattributes` extra rule removed (root rule exists) | `test_committed_schema_equals_the_regenerated_schema_byte_for_byte` |
| 2 | Core module had I/O behind `# purity: ok`; ships in the wheel | patched: pure models module plus devtools writer; AD-4 amended | `test_the_pure_module_has_no_writer_and_no_purity_exemption`, `test_main_writes_the_three_files_as_utf8_lf_without_bom` |
| 3 | jsonschema `True` flags only asserted `errors != []` | patched: each flag is the exact (keyword, JSON pointer) list | `test_jsonschema_verdict_on_an_invalid_fixture_matches_the_stated_flag` |
| 4 | Drift failure read as a hand edit after a dependency bump | patched: message names the installed Pydantic version | `test_a_hand_edited_schema_fails_the_comparison_naming_the_file` |
| 5 | jsonschema bound `>=4.23` vs spine `>=4.26` | patched, relocked | `pyproject.toml`, `uv.lock` |
| 6 | `discriminator` keyword undocumented in the union schema | patched: docstring on `AssertionConfig` | `models/assertions.py` |
| 7 | `Scenario.skip` null round trip (AD-19 defect from 2.2) | deferred, unchanged | `deferred-work.md`; strict xfails |
| 8 | Suite `literal_error` vs Trace/Report `unsupported_version` | deferred, unchanged | `deferred-work.md` |

## Verification

**Commands:**
- `cd packages/python && uv run check` -- expected: gate green
- `cd packages/python && uv run python -m agentproof_devtools.export_schemas && git status --short ../../schemas` -- expected: regeneration changes nothing
- `cd packages/python && uv run --python 3.12 --locked --isolated pytest tests/unit -q -p no:cacheprovider` -- expected: passes
- `git status --short` -- expected: only the Code Map paths
