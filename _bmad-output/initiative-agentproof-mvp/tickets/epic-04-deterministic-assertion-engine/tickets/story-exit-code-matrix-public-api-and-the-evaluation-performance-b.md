---
id: 8
type: story
title: "Exit-code matrix, public API, and the evaluation performance bound"
parent: epic-04-deterministic-assertion-engine
covers: [R6, R7, R8]
after: [7]
hitl: false
risk: medium
refined: true
---

# Exit-code matrix, public API, and the evaluation performance bound

## Description

Closes the epic's claims with the tests that CI consumers depend on: every exit code reachable through the real CLI, the public API as the only thing the CLI touches, and the performance bound measured rather than asserted.

## Requirements

1. **Exit-code matrix** (R6; PRD AC-27.1, AC-27.4)
   **Given** `tests/integration/cli/test_exit_matrix.py`
   **When** it drives `agentproof` as a subprocess
   **Then** it reaches 0 (all passed), 1 (a failed Assertion; an all-skipped Suite), 2 (malformed Suite), 3 (adapter raise; absent Trace with `fail_on_missing_trace` true), and 4 (fault injection), and asserts the precedence case where an adapter raise and an Assertion failure coexist yields 3.
2. **Public API** (R7; spine AD-15; PRD AC-34.1, AC-34.2)
   **Given** `agentproof.__all__`
   **When** read
   **Then** it contains every AD-15 name that exists by this epic (`parse_suite`, `parse_trace`, `load_suite`, `load_trace`, `evaluate_scenario`, `evaluate_suite`, `run_suite`, the models, `Adapter`, `RunContext`, `testing`, `SUPPORTED_VERSIONS`, `__version__`, `errors`); importing `agentproof` imports no framework SDK and makes no network call; and a test asserts `cli` imports only the public API plus `io` and `runner`.
3. **API equals CLI** (R7; PRD AC-34.2)
   **Given** the example Suite and its fixture Traces
   **When** `evaluate_suite(suite, traces)` runs through the API and `run_suite` runs through the runner
   **Then** both produce equal `SuiteOutcome` values.
4. **Performance bound** (R8; PRD NFR-10)
   **Given** a generated Trace with 10,000 Events and a Scenario with 20 Assertions
   **When** `evaluate_scenario` runs on the CI runner
   **Then** it completes in under two seconds, measured in a test marked `performance` that runs in CI.

## Boundaries

- No Report or HTML performance (epic 6).

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-04-deterministic-assertion-engine/epic-04-deterministic-assertion-engine.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-6, AD-15, AD-17
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-27, FR-34, NFR-10

## Notes

- Files: `tests/integration/cli/test_exit_matrix.py`, `tests/unit/test_public_api.py`, `tests/unit/test_cli_imports.py`, `tests/performance/test_evaluate_bound.py`, `src/agentproof/__init__.py`.
- Tests: as listed.
- Depends on: story 7. Risk: medium; the two-second bound is a judgment (OQ-12); if the CI runner misses it, record the measurement and raise the question rather than loosening silently.
- Done when: criteria 1 to 4 pass on both CI platforms.
