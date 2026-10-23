---
type: epic
title: "Deterministic assertion engine: agentproof run with the Fixture Agent exits 1 on the example's failing Scenario and 0 on the passing one"
parent: initiative-agentproof-mvp
covers: ["R5", "R7", "R8", "R9", "R10", "R12", "R13", "R17", "R22", "R30", "C3", "C4", "C5"]
sources: ['_bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md']
companions: []
after: []
refined: true
risk: high
---

# Deterministic assertion engine

## Description

The core promise becomes runnable: the engine's fan-out evaluation, status fold, and `SuiteOutcome` constructor; `parse_trace`, `load_trace`, and `trace validate`; the six built-in Assertions and the evaluator registry; the Adapter protocol, `RunContext`, the Fixture Agent, adapter resolution, and the conformance check; the runner's `run_suite` pipeline that owns run identity, handles adapter failures, and runs sequentially; and the `run` command with every exit code reachable. Redaction and Trace export are placeholders this epic leaves for epic 5.

## Outcome

For an engineer, `agentproof run` on the scaffolded example prints a summary showing the forbidden tool call as Evidence and exits 1, and the same inputs give the same result every time (PRD UJ-4 second half; spec Week 1 exit gate).

## Requirements

- R1 (parent R10): `engine.evaluate_scenario` applies the precedence skip, execution error, absent Trace, evaluate; fans out one result per Assertion; evaluates every Assertion in declared order; `engine.status.combine` folds `failed` over `error` over all-`skipped` over `passed`; `engine.fold` is the only `SuiteOutcome` constructor.
- R2 (parent R5): `parse_trace(data, source=)` and `load_trace(path)` validate version, ordering, size, and format, raising `TraceFormatError` or `UnsupportedVersionError` with context; `agentproof trace validate TRACE_PATH` exits 0 or 2.
- R3 (parent R7, R8, R9): `assertions.registry.EVALUATORS` maps the six types to pure evaluators; each evaluator's pass, fail, invalid-configuration, and missing-evidence behavior matches PRD AC-11.1 to AC-16.3; negative results state the Capture declaration; an exception inside an evaluator becomes an `error` result.
- R4 (parent R12, R13): `adapters.protocol` defines `Adapter` and `RunContext`; `adapters.fixture` reads `scenario.trace` relative to `suite_dir` through `io.read_limited` and raises `TraceMissingError` when absent; `adapters.resolve` finds `fixture`, an entry point, or a dotted path; `testing.adapter_conformance.check` validates what a generic test can observe.
- R5 (parent C5): `runner.run_suite` resolves the adapter, generates `run_id` and `started_at`, overwrites identity fields after `run`, applies deterministic fixture identity, catches `TraceMissingError` and other exceptions per AD-6, never calls an adapter for a skipped Scenario, runs sequentially, and leaves a named redaction step that epic 5 fills.
- R6 (parent R17): `agentproof run SUITE_PATH [--adapter] [--output DIR]` exits 0, 1, 3, or 4 per AD-6; a run with zero evaluated Assertions exits 1; every code has a subprocess integration test.
- R7 (parent R22): `agentproof.__all__` exports the AD-15 names that exist by the end of this epic, imports no framework SDK, and a test asserts the CLI imports only the public API plus `io`.
- R8 (parent R30): a 10,000-Event Trace evaluates against a 20-Assertion Scenario in under two seconds on the CI runner.

## Constraints

- Covered parent constraints: C3 (one fold, one exit module), C4 (config models in `models.assertions`, evaluators in `assertions.builtin`, one YAML form), C5 (runner owns identity, sequential, sole pipeline caller); the lines below say how.
- Spine AD-1: evaluators and the engine are pure; the runner is the only caller of adapters and the clock.
- Spine AD-8: no new YAML form; evaluators take the config models from epic 2.
- Spine AD-9: synchronous adapters; the runner never creates threads or event loops.
- PRD OQ-3 and OQ-7 are built as the spine's defaults.

## Done when

- `agentproof run agentproof.yaml` after `init` exits 1, the summary names `tool_not_called-0` as failed with Evidence `[1]`, and running it again gives identical output (R1, R3, R5, R6).
- Each of the six Assertions has four passing tests (pass, fail, invalid configuration, missing evidence) and the `EVALUATORS` key-set test passes (R3).
- The exit-code matrix test drives the CLI as a subprocess to codes 0, 1, 2, 3, and 4 (R6).
- `agentproof trace validate` accepts the example fixture Traces and rejects each malformed Trace fixture with exit 2 (R2).
- The conformance check passes for the Fixture Agent and fails for a test adapter that returns a Trace with a seq gap (R4).
- Production delivery: the CI matrix runs the `run` integration tests on Linux and Windows (R6, R8).

## Boundaries

- No redaction (epic 5): the pipeline's redaction step is an identity placeholder named `redact` so epic 5 replaces one line; no Trace or Report file is written yet (epic 5, epic 6): `run` prints its summary only.
- Must not change: the Suite and Trace models; a needed change is a `Source conflict:` in epic 2.
- Touch point: the `agentproof.adapters` entry-point group declared in `pyproject.toml`; owner: this epic.

## References

- parent — _bmad-output/initiative-agentproof-mvp/initiative-agentproof-mvp.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-6, AD-8, AD-9, AD-13, AD-15, AD-18
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-7, FR-10 to FR-21, FR-27, FR-34, NFR-10
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/adr-log.md, ADR-006, ADR-008, ADR-009

## Notes

- Decision (2026-10-22): tracer bullet is story 1, the engine evaluating a Scenario with one stub evaluator through `evaluate_scenario` and `fold`, demoable as a unit test that prints a `SuiteOutcome`.
- Decision (2026-10-22): `parse_trace` and `trace validate` live here, not in epic 5, because the Fixture Agent reads Trace files; epic 5 owns export and Replay.
- Decision (2026-10-22): `run` writes no files in this epic; Trace export (epic 5) and the Report (epic 6) add the writes to the same pipeline.
- Open question: OQ-3; story 7 builds exit 3 on any adapter raise as AD-6 says.
- Open question: OQ-7; story 5 builds dotted paths with list indexes.
