---
id: 1
type: story
title: "Engine: evaluate_scenario, status fold, and the SuiteOutcome constructor"
parent: epic-04-deterministic-assertion-engine
covers: [R1]
after: ["2.4"]
hitl: false
risk: high
refined: true
---

# Engine: evaluate_scenario, status fold, and the SuiteOutcome constructor

## Description

The tracer bullet of the engine: the one function that decides what a Scenario's results are, the one fold, and the one `SuiteOutcome` constructor, built against a stub evaluator so the semantics are tested before any real Assertion exists. Demoable as a test that prints a `SuiteOutcome`.

## Requirements

1. **Precedence and fan-out** (R1; spine AD-6; PRD AC-18.1 to AC-18.5)
   **Given** `evaluate_scenario(scenario, trace, defaults, execution_error=None)`
   **When** the Scenario has `skip`
   **Then** every Assertion yields `skipped` with the reason and nothing else is consulted; when `execution_error` is given, every Assertion yields `error` with the message and `ScenarioResult.execution_error` is set; when `trace is None` with `fail_on_missing_trace` true, every Assertion yields `error` and `execution_error == "trace missing"`, with it false every Assertion yields `skipped`; otherwise every Assertion is evaluated in declared order even after a failure.
2. **Fold** (R1; spine AD-6)
   **Given** `status.combine(statuses)`
   **When** called
   **Then** it returns `failed` if any `failed`, else `error` if any `error`, else `skipped` if all `skipped`, else `passed`; a Scenario with one skipped and nine passed Assertions is `passed`.
3. **SuiteOutcome constructor** (R1; spine AD-6)
   **Given** `engine.fold(results)`
   **When** called with ScenarioResults
   **Then** it is the only constructor of `SuiteOutcome`, sets `suite_status` through `combine`, `execution_failed = any(r.execution_error is not None)`, and `evaluated_assertions` as the count of results whose status is not `skipped`; `evaluate_suite(suite, traces)` calls `evaluate_scenario` per Scenario in declared order and ends in `fold`.
4. **Evaluator exceptions** (R1; spine AD-7; PRD AC-17.3)
   **Given** a stub evaluator that raises
   **When** `evaluate_scenario` runs
   **Then** the result is `error` with message `<ExceptionType>: <message>` and no exception propagates.

## Boundaries

- No real evaluators (stories 3 to 5); the registry holds a stub for this story's tests only.
- Must not change: the result models from epic 2.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-04-deterministic-assertion-engine/epic-04-deterministic-assertion-engine.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-6, AD-7
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-18, AC-18.1 to AC-18.5, AC-17.3

## Notes

- Files: `src/agentproof/engine/status.py`, `src/agentproof/engine/evaluate.py`, `src/agentproof/assertions/base.py` (Evaluator type), `src/agentproof/assertions/registry.py` (empty dict for now).
- Tests: `tests/unit/engine/test_status.py`, `tests/unit/engine/test_evaluate_scenario.py` covering every branch of criterion 1 and the exception path.
- Depends on: 2.4. Risk: high; this is the semantics every exit code rests on.
- Done when: criteria 1 to 4 pass.
