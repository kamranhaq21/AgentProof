---
title: 'Refactor sweep'
type: 'feature'
ticket: '7'
created: '2026-10-23'
status: 'built'
baseline_revision: '39307b3b9675020011ab62dc231c05b36c6babd3'
route: 'full'
route_source: 'pinned'
risk: 'low'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Stories 1.x to 2.6 deferred a short list of pure cleanups (epic-01 retrospective item 13 and findings C9 and C10, story 2.6 finding F2's hoisting half): the same helpers are defined in several places, tests repeat `Path(__file__).resolve().parents[N]` and a copy of the same `subprocess.run` call, a dead skip mechanism sits in `check.py`, `purity.py` crashes on a non-UTF-8 file, and two workflows inline one `sed` line (story 2.7; epic 2 R5).

**Approach:** Do exactly the six items below, each with no change to any validation outcome, serialized field, generated schema, or test assertion. Scope is fixed here before work starts; anything that looks relevant but changes behavior is listed under "Considered and left out" and not touched.

## Boundaries & Constraints

**Always:** cleanup only; the generated `schemas/*.json` stay byte-identical; every model that called `_null_means_absent` or `MODEL_CONFIG` before still does, and no model gains either; test assertions keep their text and meaning; `uv run check` and the whole suite stay green.

**Never:** no change to any serialized model field, error code, or error shape; no new runtime dependency; no new behavior beyond the one `purity.py` guard (item 5), which routes a failure that previously escaped as a traceback into the documented exit-2 path.

## Scope (each item with its source finding)

1. Hoist `_null_means_absent` (from `models/trace.py`) and `MODEL_CONFIG` (from `models/assertions.py`) to `models/common.py`. Source: story 2.6 finding F2 (hoist half only), `trace.py` docstring ("the Suite models may hoist it later").
2. One shared definition of the package and repository roots for the tests, replacing the duplicated `Path(__file__).resolve().parents[N]` lines. Source: epic-01 retrospective item 13 and `deferred-work.md` ("duplicated in seven test files and check.py").
3. One shared subprocess helper for the test call sites. Source: epic-01 retrospective item 13.
4. Remove the `lint-imports` skip placeholder from `devtools/check.py`. Source: epic-01 retrospective C9, item 13.
5. Guard `purity.py` against a non-UTF-8 file. Source: epic-01 retrospective C10, item 13.
6. Share the version-extraction `sed` line between `ci.yml` and `release-draft.yml`. Source: epic-01 retrospective item 13.

## Considered and left out

7. `Scenario.skip` rejecting a present null that the model's own dump writes: a validation-outcome change on Suite, needs a dedicated story/decision (not 2.7, and not 3.3 either, since 3.3's boundary also forbids changing the models). `deferred-work.md`'s entry (story 2.5, `Scenario.skip`) routes it to "story 2.7 or story 3.3"; both halves are wrong, so the entry should be corrected to drop the 3.3 half and say "needs a new story".
8. Suite's `literal_error` versus Trace/Report's `unsupported_version` for an unsupported schema version: an explicit cross-model decision, not mechanical cleanup.
9. Applying `_null_means_absent` to Suite's defaults sub-models (as opposed to just hoisting its definition, item 1): flips a currently-failing strict-xfail property test to passing, a real validation-outcome change. (`deferred-work.md`'s story 2.6 F2 entry names story 2.7 as owner for this; that routing is also wrong and should say "needs a new story".)
10. Unifying the non-finite-number error shape between Trace's clean walk and Suite/Report's union-branch error list: changes asserted error shapes, a cross-model decision.

</frozen-after-approval>

## Code Map

Item 1 (hoist):
- `packages/python/src/agentproof/models/common.py` -- gains `MODEL_CONFIG` and `_null_means_absent` (and the Pydantic imports they need); module docstring updated (it said "No Pydantic here").
- `packages/python/src/agentproof/models/assertions.py` -- defines `MODEL_CONFIG` no more; imports it from `common` (still used by `AssertionConfigBase`); drops the unused `ConfigDict` import.
- `packages/python/src/agentproof/models/trace.py` -- defines `_null_means_absent` no more; imports it from `common` (still called by `TraceEvent` and `Trace`). Its models keep their own `ConfigDict(frozen=True, extra="forbid")`; that is not `MODEL_CONFIG` and is not changed.
- `packages/python/src/agentproof/models/result.py`, `report.py` -- import `MODEL_CONFIG` and `_null_means_absent` from `common` instead of `assertions` and `trace`.
- `packages/python/src/agentproof/models/suite.py` -- imports `MODEL_CONFIG` from `common`; does not gain `_null_means_absent` (item 9).
- `packages/python/tests/unit/models/test_assertions_config.py` -- imports `MODEL_CONFIG` from `common` (the only test that imported either name by its old path; `test_properties.py` mentions them in prose only).

Items 2 and 3 (shared test support):
- `packages/python/tests/testsupport.py` -- new; `PACKAGE_ROOT`, `REPOSITORY_ROOT`, and `run_captured(argv, *, timeout, cwd=None, env=None, check=False)`. A module rather than conftest fixtures because `test_errors_taxonomy`, `test_fixtures_v1`, `test_workflow_pins`, `test_repo_hygiene` and `test_schema_drift` need the roots at collection time (`parametrize`, module-level constants), which fixtures cannot serve; and importlib import mode puts nothing from `tests/` on `sys.path`.
- `packages/python/pyproject.toml` -- `pythonpath = ["tests"]` under `[tool.pytest.ini_options]` so `testsupport` imports by name; `"tests"` added to ruff's `src` so it sorts as first-party.
- Roots (item 2): `tests/unit/cli/test_single_exit_site.py`, `tests/unit/test_errors_taxonomy.py`, `tests/unit/test_fixtures_v1.py`, `tests/unit/test_import_contracts.py`, `tests/unit/test_repo_hygiene.py`, `tests/unit/test_schema_drift.py`, `tests/unit/test_tooling_config.py`, `tests/unit/test_version.py`, `tests/unit/test_workflow_pins.py`, `tests/integration/cli/test_version_and_errors.py`, `tests/integration/test_install_smoke.py`.
- Subprocess (item 3): `tests/unit/test_import_contracts.py`, `tests/unit/test_schema_drift.py`, `tests/integration/cli/test_version_and_errors.py`, `tests/integration/test_install_smoke.py`. `tests/unit/test_check_entry_point.py` spawns nothing (it injects a recording runner and only names `subprocess.CompletedProcess`), so it has no call site to switch. `devtools/check.py` keeps `subprocess.run` as its injected default: devtools is installed code and must not import from `tests`, and a test helper importing devtools would invert the layering; likewise `check.py` and `export_schemas.py` keep their own `PACKAGE_ROOT` and `REPOSITORY_ROOT` (they are not under pytest).
- Left alone because outside the listed files: `tests/unit/cli/test_exit_codes.py`, `test_fault_hook_reach.py`, `tests/unit/loading/test_yaml_safe.py`, `tests/unit/models/test_canonical.py` also use `parents[N]` for a path below the roots; not in the item's list, so not touched.

Item 4:
- `packages/python/devtools/src/agentproof_devtools/check.py` -- `Step.skip_reason`, `import_linter_skip_reason()`, and the skip branch in `run_steps` removed (`skip_reason` served only `lint-imports`).
- `packages/python/tests/unit/test_check_entry_point.py` -- the two skip tests and `test_repository_importlinter_exists_so_lint_imports_is_not_skipped` removed; the "runs when config present" test now asserts the step always runs with `--config <root>/.importlinter`.

Item 5:
- `packages/python/devtools/src/agentproof_devtools/purity.py` -- `main` catches `UnicodeDecodeError` beside `SyntaxError` on the existing "cannot parse" exit-2 path; docstring says so. `find_violations` itself is unchanged (it returns a list; the documented error path lives in `main`).
- `packages/python/tests/unit/test_purity.py` -- new test writing Latin-1 bytes directly and asserting exit 2, "cannot parse" naming the file on stderr, nothing on stdout.

Item 6:
- `.github/scripts/pyproject-version.sh` -- new; the one `tr | sed` extraction, path resolved relative to the script. Chosen over a composite action: the pin tests allow exactly four actions and require every `uses:` to be a SHA pin, so a local `uses: ./.github/actions/...` would break both rules; `.gitattributes` already pins `*.sh` to LF.
- `.github/workflows/ci.yml` (`smoke`), `.github/workflows/release-draft.yml` (version guard) -- `expected="$(bash .github/scripts/pyproject-version.sh)"`; the rest of each step is unchanged.
- `packages/python/tests/unit/test_workflow_pins.py` -- the two assertions on the inlined text now assert the script call; a new test asserts the script is LF, holds exactly the one command, and that no workflow inlines `sed -nE`.

## Tasks & Acceptance

**Execution:**
- [x] Item 1 -- hoist `MODEL_CONFIG` and `_null_means_absent` to `models/common.py`
- [x] Item 2 -- `tests/testsupport.py` roots; replace the duplicated definitions
- [x] Item 3 -- `run_captured`; switch the four spawning call sites
- [x] Item 4 -- remove the `lint-imports` skip mechanism
- [x] Item 5 -- guard `purity.py` against non-UTF-8, with a test
- [x] Item 6 -- shared version script; update the workflow-pin tests
- [x] `uv run check` green (see Implementation Notes for the final run)
- [x] `uv run --python 3.12 --locked --isolated pytest -q -p no:cacheprovider` green

**Acceptance Criteria:**
- Given the plans and review findings of stories 1 to 6, when this story starts, then this plan lists each cleanup item with its source finding and nothing else is touched.
- Given the sweep's diff, when `uv run check` runs, then it passes, the drift test passes (generated schemas byte-identical), and the diff touches only the listed items.

## Implementation Notes

**2026-10-23, implementer (worktree `D:\AgentProof-wt-2-7`, branch `story/2-7-refactor-sweep`, baseline `39307b3`).**

Importer lists, confirmed by grep before editing:
- `_null_means_absent`: defined in `trace.py`; called by `TraceEvent` and `Trace` (trace.py), two models in `result.py`, and one model in `report.py`. Imported by `result.py` and `report.py`. Same call sites after the move; `suite.py` still does not call it. No test imported it by name (`test_properties.py` mentions it in prose only).
- `MODEL_CONFIG`: defined in `assertions.py`; used by `AssertionConfigBase`, `result.py`, `report.py`, and `suite.py`. The Trace models keep their own `ConfigDict(frozen=True, extra="forbid")` (no `allow_inf_nan`), unchanged. One test imported it from the old path (`test_assertions_config.py`); updated rather than re-exported.
- `parents[N]` duplicates: found in all 11 listed test modules; also in four unlisted ones (left alone, see Code Map).

Decisions and surprises:
- Fixtures were not workable for item 2 as written: five modules use the roots at import time (`parametrize` lists, module constants), and importlib import mode does not make `conftest` or any `tests/` module importable by name. Landed on `tests/testsupport.py` plus `pythonpath = ["tests"]`; no `package_root`/`repository_root` fixtures were added because nothing would use them.
- Item 3: `test_check_entry_point.py` has no real subprocess call (injected runner), and `check.py` cannot share the helper without a devtools-to-tests or tests-to-devtools dependency; both stay as they are. `run_captured` reproduces each site's previous `subprocess.run` keyword set exactly (`capture_output`, `text`, UTF-8, `timeout`, `check`); the sites that passed `env` still build it themselves.
- Item 5: the guard is in `main` (the documented exit-2 path, `except SyntaxError`), not inside `find_violations`, because `find_violations` returns a list and has no error channel; `main` now catches `(SyntaxError, UnicodeDecodeError)`. Message: `purity: cannot parse <file>: <error>` on stderr, exit 2.
- Item 6: a composite action is incompatible with `test_only_the_four_agreed_actions` and the full-SHA pin rule (a local `uses: ./...` is neither), so a shell script is used. The script resolves the pyproject path from its own location, so the call works from any directory; verified `bash .github/scripts/pyproject-version.sh` prints `0.1.0.dev0`, equal to the `version` line in `pyproject.toml`. The `smoke` and release guards keep the same `test -n "$expected" && ...` comparison as before. Not exercised on a real GitHub runner (the Windows `smoke` cell runs the script through Git Bash with an LF checkout, pinned by `.gitattributes` `*.sh text eol=lf`); the first CI run on the PR is the proof.
- Models: the diff of the five model modules is import lines, the two hoisted definitions, and docstrings; `git status` shows no change to `schemas/*.json` and `test_schema_drift.py` passes.
- Not touched but noted: `deferred-work.md` entries for `Scenario.skip` (owner "story 2.7 or 3.3") and for story 2.6 F2 (owner "story 2.7") should be corrected per items 7 and 9; epic-01 retrospective item 13 is now fully done. Those edits are outside the sweep's file list and are left to the orchestrator.

Commands run (all from `packages/python`, 2026-10-23):
- Baseline, clean `origin/backlog` (changes stashed): `uv run pytest -q -p no:cacheprovider` -> 1172 passed, 14 xfailed.
- `uv run check` after all six items -> ruff check, ruff format --check, mypy --strict (28 source files), lint-imports (7 kept, 0 broken), pytest all green: 1172 passed, 14 xfailed. (Earlier runs failed on a missing import I introduced and on `ruff format` of one new test; both fixed before the green run.)
- `uv run --python 3.12 --locked --isolated pytest -q -p no:cacheprovider` -> 1172 passed, 14 xfailed.
- Test count is unchanged: three skip tests removed; one "lint-imports always runs" test, one non-UTF-8 purity test, and one version-script test added.
- Caches (`__pycache__`, `.pytest_cache`, `.ruff_cache`, `.mypy_cache`, `.hypothesis`, `.import_linter_cache`, `dist`) removed; `.venv` kept.
