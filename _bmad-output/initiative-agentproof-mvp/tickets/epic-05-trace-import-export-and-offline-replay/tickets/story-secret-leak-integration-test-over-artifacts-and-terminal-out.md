---
id: 6
type: story
title: "Secret-leak integration test over artifacts and terminal output"
parent: epic-05-trace-import-export-and-offline-replay
covers: [R6]
after: [4]
hitl: false
risk: medium
refined: true
---

# Secret-leak integration test over artifacts and terminal output

## Description

One test that proves the privacy promise end to end, on both platforms, and fails the moment someone removes the runner's redaction call.

## Requirements

1. **Planting** (R6; PRD AC-31.3, AC-28.2)
   **Given** a Suite with `redact.env: [TEST_SECRET]` and a fixture Trace holding `KEYVALUE-1` under an `api_key` argument and the value of `TEST_SECRET` inside Final Output and a tool result, plus a stub adapter whose exception message contains the `TEST_SECRET` value
   **When** `run` and `trace replay` execute with `TEST_SECRET` set
   **Then** neither value appears in any file under the Output Directory nor in captured stdout or stderr, at default and `--verbose` verbosity.
2. **Key-only values and exceptions** (R6; PRD AC-28.2 as finalized)
   **Given** the same setup
   **When** the exception message contains `KEYVALUE-1` only (not declared under `redact.env`)
   **Then** the test documents that key-based redaction does not reach free-text exception messages and asserts the documented statement is printed, not the absence of the value.
3. **Mutation check** (R6)
   **Given** the runner's `redact` call commented out in a temporary copy
   **When** the test runs against it
   **Then** it fails.

## Boundaries

- Must not change: Redaction semantics; a gap found here is a bug ticket against story 2.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-05-trace-import-export-and-offline-replay/epic-05-trace-import-export-and-offline-replay.md, section Requirements
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, AC-28.2, AC-31.3, AC-31.4
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-10, AD-17

## Notes

- Files: `tests/integration/test_secret_leak.py`, `tests/fixtures/suites/secret-leak/`, `tests/helpers/adapters.py` (raising stub).
- Tests: as listed, run on both CI platforms.
- Depends on: story 4. Risk: medium.
- Done when: criteria 1 to 3 pass.
