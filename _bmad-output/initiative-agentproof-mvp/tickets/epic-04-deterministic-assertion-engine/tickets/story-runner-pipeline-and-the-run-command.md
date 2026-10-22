---
id: 7
type: story
title: "Runner pipeline and the run command"
parent: epic-04-deterministic-assertion-engine
covers: [R5, R6]
after: [1, 4, 5, 6, "3.5", "3.6"]
hitl: false
risk: high
refined: true
---

# Runner pipeline and the run command

## Description

The imperative shell that drives everything: resolve the adapter, own run identity, call the adapter per Scenario, hand the Trace to the engine, print the summary. Redaction is an identity placeholder here that epic 5 replaces, and no files are written until epics 5 and 6 add those steps to the same pipeline.

## Requirements

1. **Pipeline and identity** (R5; spine AD-9, AD-13, AD-18)
   **Given** `runner.run_suite(suite, adapter=, output_dir=, clock=, env=)`
   **When** it runs the example Suite with the Fixture Agent
   **Then** it processes Scenarios sequentially in declared order in one thread, generates `run_id` and `started_at` from `clock`, overwrites `run_id`, `started_at`, `ended_at`, and `environment` on the returned Trace before re-validating it, and with `defaults.fixture.deterministic` true uses `run_id = "fixture-<scenario id>"` and the fixture file's timestamps.
2. **Failure handling** (R5; spine AD-6; PRD AC-21.3, AC-18.2)
   **Given** an adapter that raises `TraceMissingError` for one Scenario and `ValueError` for another
   **When** the Suite runs
   **Then** the first yields `trace=None` to the engine, the second yields `execution_error` and is wrapped as `AdapterRunError`, both Scenarios still report, the run continues, and a skipped Scenario never invokes the adapter.
3. **Redaction placeholder** (R5; spine AD-10)
   **Given** the pipeline
   **When** read
   **Then** one named step `redact` exists between obtaining the Trace and evaluating it, currently returning the Trace unchanged, with a test marked as replaced by epic 5.
4. **run command** (R6; spine AD-20; PRD AC-30.1, AC-27.2, AC-27.3)
   **Given** `agentproof run agentproof.yaml` after `init`
   **When** it runs
   **Then** it prints one line per Scenario with its status and one line per failed or errored Assertion with its id, message, and Evidence, then a counts line, and exits 1; `--adapter` overrides `defaults.adapter`; a Suite whose Scenarios are all skipped exits 1 naming the cause; an adapter raise exits 3; running twice prints identical output.

## Boundaries

- No file writes (epic 5 story 3, epic 6 story 1).
- Must not change: the engine's semantics; the runner calls `evaluate_scenario` and `fold` and nothing else computes status.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-04-deterministic-assertion-engine/epic-04-deterministic-assertion-engine.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-6, AD-9, AD-10, AD-13, AD-18, AD-20
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-18, FR-21, FR-27, FR-30, UJ-4

## Notes

- Files: `src/agentproof/runner/pipeline.py`, `src/agentproof/runner/clock.py`, `src/agentproof/cli/commands/run.py`, `src/agentproof/__init__.py` (`run_suite`).
- Tests: `tests/unit/runner/test_pipeline.py` (identity, deterministic, failure handling, sequential, skip), `tests/integration/cli/test_run.py` (subprocess, exit 0, 1, 3, identical output twice).
- Depends on: stories 1, 4, 5, 6 (the example Suite uses `tool_call_count`, so story 4 must exist), and 3.5, 3.6. Risk: high; OQ-3 (exit 3 on any adapter raise) is built as written.
- Done when: criteria 1 to 4 pass on both CI platforms.
