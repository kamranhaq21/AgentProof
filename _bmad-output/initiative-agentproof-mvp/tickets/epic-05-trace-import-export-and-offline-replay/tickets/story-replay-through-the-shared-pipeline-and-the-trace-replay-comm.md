---
id: 4
type: story
title: "Replay through the shared pipeline and the trace replay command"
parent: epic-05-trace-import-export-and-offline-replay
covers: [R4]
after: [3]
hitl: false
risk: high
refined: true
---

# Replay through the shared pipeline and the trace replay command

## Description

Offline re-evaluation of a saved Trace, built as a second entry into the same pipeline so run and Replay cannot diverge on redaction, capture, or evaluation. Until epic 6 provides `build_report`, Replay prints its summary; epic 6 story 1 adds the Report write.

## Requirements

1. **runner.replay** (R4; spine AD-13; PRD AC-19.1 to AC-19.3)
   **Given** `runner.replay(suite, scenario_id, trace_bytes, output_dir=, env=)`
   **When** called with an exported Trace
   **Then** it resolves `secret_values`, installs the console scrub, parses the Trace, redacts, evaluates, and folds through the same private pipeline as `run_suite`, calling no adapter, and returns a `SuiteOutcome` equal to the run's for that Scenario.
2. **Command** (R4; spine AD-20; PRD FR-19)
   **Given** `agentproof trace replay TRACE_PATH --suite SUITE_PATH --scenario SCENARIO_ID [--output DIR]`
   **When** run on an exported Trace with no environment variables set and network blocked
   **Then** it prints the same Assertion Results and exits with the same code as the run; an unknown `--scenario` exits 2 naming the id; a missing `TRACE_PATH` exits 2.
3. **Never overwrites run output** (R4; spine AD-14; PRD AC-19.4)
   **Given** an Output Directory holding a run's files
   **When** Replay runs into it
   **Then** `scenario-*.trace.json` and `report.json` are byte-identical afterwards; the Replay's own artifact name is reserved as `replay-<id>.report.json` for epic 6.
4. **Public API** (R4; spine AD-15)
   **Given** `agentproof.__all__`
   **When** read
   **Then** it contains `replay`.

## Boundaries

- No Report write yet (epic 6 story 1).
- Must not change: the run pipeline's steps; Replay reuses them.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-05-trace-import-export-and-offline-replay/epic-05-trace-import-export-and-offline-replay.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-13, AD-14, AD-15, AD-20
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-19, AC-19.1 to AC-19.4, UJ-2

## Notes

- Files: `src/agentproof/runner/pipeline.py` (`replay`), `src/agentproof/cli/commands/trace.py` (`replay` subcommand), `src/agentproof/__init__.py`.
- Tests: `tests/unit/runner/test_replay.py` (equality with run), `tests/integration/cli/test_trace_replay.py` (subprocess with a cleared environment and the socket guard active).
- Depends on: story 3. Risk: high; the equivalence claim is the product's headline.
- Done when: criteria 1 to 4 pass on both CI platforms.
