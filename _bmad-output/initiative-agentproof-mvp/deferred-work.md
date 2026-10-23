- source_plan: `_bmad-output/initiative-agentproof-mvp/tickets/epic-01-repository-foundation-and-ci/tickets/story-package-scaffold-installs-and-prints-its-version-plan.md`
  summary: AGENTS.md says no distribution name may be written before the OQ-1 decision, but the maintainer approved a provisional `name = "agentproof"` in pyproject.toml; reword the AGENTS.md policy line to allow the provisional name and forbid only install commands and publishing.
  evidence: Quick lens finding on 2026-10-22; the frozen plan Intent records the maintainer decision; a fix edits an agent-context file, so it goes through a bmad-project-context refresh rather than this build.
  status: closed 2026-10-23 by the bmad-project-context refresh after epic 1; the AGENTS.md
    policy line now allows the provisional name and forbids publishing and public
    install-by-name commands, and docs/decisions/0000-distribution-name.md quotes the new
    wording.

- source: `_bmad-output/initiative-agentproof-mvp/tickets/epic-01-repository-foundation-and-ci/epic-01-repository-foundation-and-ci-retrospective.md` (2026-10-23, verdict accepted-with-open-items)
  summary: `.importlinter` forbids `cli -> errors` although AD-2/AD-15 make `errors` public API, and no `runner` forbidden contract exists (AD-2 lets runner import adapters and io only); reconcile when story 3.1 first hits it.
  owner: story 3.1 (CLI skeleton); architect decides the contract wording.
- source: epic-01 retrospective, finding 4
  summary: AD-19 says pickle/marshal/eval/exec/yaml.load are banned by the AD-1 ruff list, but pyproject's TID251 list does not name them and shell packages are exempt; add the bans with a rule set that reaches shell packages, and amend AD-19's wording.
  owner: story 3.2 (safe YAML loader) for the bans; architecture update for AD-19.
- source: epic-01 retrospective, finding 7 and item 8
  summary: release-draft builds on any tag without gating on the check gate or `main` ancestry, would clobber assets of a published release, and the sdist cannot drive `uv lock --check` because pyproject names the excluded devtools member; decide uv.lock-in-sdist and add an in-suite bare `uv build` test.
  owner: epic 9 story 5 (publishing pipeline).
- source: epic-01 retrospective, items 9 and 10
  summary: the dependency audit runs only on PR/push, Linux-marker-only, with no schedule or dependabot; smoke installs the wheel at Python 3.12 only while epic R1 says 3.12 to 3.15.
  owner: epic 9 (schedule, per-platform audit, dependabot); PO decides the R1 smoke matrix scope.
- source: epic-01 retrospective, items 12 and 13
  summary: the AD-1 ban list is as narrow as AD-1's literal list (os module, shutil, tempfile, Path.resolve/cwd pass); the next sweep should add conftest fixtures for PACKAGE_ROOT/REPOSITORY_ROOT (duplicated in seven test files and check.py), a shared subprocess helper, and the shared version step.
  owner: architect (AD-1 list, spine and pyproject together); the epic-2 refactor sweep.
- source: epic-01 retrospective, finding 6
  summary: `backlog` is not protected; decide whether to protect it now that `backlog -> main` pull requests are opened at each epic close.
  owner: maintainer.
- source: story 2.4 quick-lens review, 2026-10-23, finding 7
  summary: `SuiteDefaults`, `FixtureDefaults`, `CompareDefaults`, and `RedactDefaults` (story 2.2) carry no `Field(description=...)`, so the generated Report and Suite schemas have $defs without descriptions; and `Timestamp` exports bare `type: string` with no `pattern`, so an external validator accepts naive timestamps the models reject. Both must be fixed before the schemas are published.
  owner: story 2.5 (generated JSON Schemas): add the descriptions to the 2.2 models and an ECMA-anchored RFC 3339 pattern via json_schema_extra on the Timestamp alias.
- source: story 3.2 quick-lens review, 2026-10-23, finding 7
  summary: the YAML loader fills `Violation.field` with `<line>:<column>` while `errors.py` documents it as the dotted model path; story 3.3 (parse_suite) mixes both in one list, so it must fix the convention (for example a separate `line` on Violation, or a documented rule that a field matching `\d+:\d+` is a position) and update the errors.py docstring.
  owner: story 3.3.
- source: story 2.5 (generated JSON Schemas), 2026-10-23, found by the schema v1 fixtures
  summary: AD-19 defect from story 2.2: `Scenario.skip` rejects a present `null` ("presence means skipped"), but `model_dump(mode="json")` writes `skip: null` for an unskipped Scenario and the generated Suite schema accepts null, so a Suite does not read back from its own dump (null must equal absent). Held as strict xfail in `tests/unit/test_fixtures_v1.py` (`SUITE_DUMP_GAP`); remove the marks when fixed.
  owner: story 2.7 (refactor sweep) or story 3.3 (parse_suite).
- source: story 2.5 (generated JSON Schemas), 2026-10-23
  summary: an unsupported `version` is `literal_error` for a Suite (story 2.2 chose `Literal[1]`) but `unsupported_version` for a Trace and a Report, so the loaders cannot key on one code; decide one code across the three models (a validation change, hence a cross-model decision). The fixtures `suite__literal_error__version` and `trace__unsupported_version__version` name what each model raises today.
  owner: story 2.7 (refactor sweep).
- source: story 3.1 review, 2026-10-23
  summary: the CLI error handler prints `str(exc)` for exit 3 and 4, the traceback under `--verbose`, and unwrapped violation messages without running `scrub_text`, so a secret value inside an exception message reaches stderr. Strict `xfail` tests (`test_a_planted_secret_never_reaches_the_output` in `tests/unit/cli/test_error_handler.py`) pin the gap; when `io.console` scrubs every print they XPASS and fail, and must be flipped to plain tests.
  owner: story 3.5 (console scrubber and logging filter).
- source: story 3.2 (safe YAML loader), 2026-10-23
  summary: AGENTS.md's managed block still says "Parse YAML with yaml.safe_load only (the one SafeLoader subclass of ADR-019)"; the actual entry point is loading.yaml_safe.load, never yaml.safe_load directly. Reword to "Parse YAML only through agentproof.loading.yaml_safe.load (one SafeLoader subclass); never yaml.safe_load or yaml.load directly" at the next bmad-project-context refresh.
  owner: maintainer / next AGENTS.md refresh.
- source: story 2.6 property tests, 2026-10-23, finding F2
  summary: `_null_means_absent` (AD-19: null reads as absent) is applied only to `Trace`, `TraceEvent`, and the result/report models; nested models with non-null defaults reject an explicit null (`Trace.capture.tool_calls`, `redaction.applied/paths/env_names`, and every `Suite.defaults` field and sub-model: `fail_on_missing_trace`, `fixture.deterministic`, `compare.include_arguments`, `redact.keys/paths/env`). The serializer never writes these nulls, so round trips hold; it is an input-leniency gap. Tracked by the xfail(strict) property `test_explicit_null_for_a_nested_field_with_a_default_reads_as_absent`.
  owner: story 2.7 (refactor sweep: hoist `_null_means_absent` and `MODEL_CONFIG`, apply it to every model with defaults); the property then flips to a pass and its xfail is removed.
- source: story 2.6 property tests, 2026-10-23, finding F3
  summary: `JsonValue` fields (tool arguments, event payloads, Suite input, Final Output, result detail) reject finite, valid JSON nested more than about 90 levels (passes at 90, fails at 100 on Windows/CPython 3.13) with `recursion_loop` plus one error per union branch (about 500 lines), while `json.loads` and `canonical.dumps` handle 150+ levels. A deep Trace from an adapter therefore cannot be loaded, and the message does not say "too deeply nested". CI then showed the threshold is itself platform-dependent: the same 150-level payload validates fine on Linux/CPython 3.12.3, almost certainly because pydantic-core's recursive-validation limit rides on the native C stack (POSIX default stack size is larger than Windows'). Either bound the depth deliberately with a limit enforced the same way on every platform (a documented, explicit check rather than relying on the native stack) and one clear error, or make validation iterative. Tracked by the non-strict xfail test `test_finite_json_one_hundred_and_fifty_levels_deep_is_accepted` (made non-strict after the platform-dependence surfaced on CI, so a passing CI run on one platform isn't itself treated as the regression).
  owner: story 3.3 (parse_suite/parse_trace/parse_report turn it into one InputError with a depth message) and the architect (decide the limit beside the AD-19 size limits).
