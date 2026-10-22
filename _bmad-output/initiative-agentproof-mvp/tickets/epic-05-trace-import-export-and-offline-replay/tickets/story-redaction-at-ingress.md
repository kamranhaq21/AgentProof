---
id: 2
type: story
title: "Redaction at ingress"
parent: epic-05-trace-import-export-and-offline-replay
covers: [R2]
after: [1, "4.7"]
hitl: false
risk: high
refined: true
---

# Redaction at ingress

## Description

The tracer bullet of the epic: the one `redact` function, wired into the runner's placeholder so a run's summary already shows `[REDACTED]` for the fixture's planted key before any file is written. The core never reads the environment; the runner resolves declared variable values and passes them in.

## Requirements

1. **Rules and marker** (R2; spine AD-10; PRD AC-31.1)
   **Given** `redaction.redact(trace, rules, secret_values)`
   **When** a Trace has `api_key`, `Token`, or `AUTHORIZATION` keys at any depth of `arguments`, `result`, `metadata`, or `output`, or a value at a user dotted path
   **Then** those values become `[REDACTED]`, matching case-insensitively; `redact.keys` extends the default set and cannot remove from it.
2. **Declared values** (R2; PRD FR-31, AC-31.3)
   **Given** `secret_values` holding the current values of `redact.env` names
   **When** a value occurs inside Final Output text or a tool result string
   **Then** every occurrence is replaced, longest value first; an unset or empty variable contributes nothing; no minimum length applies (ARCH-6 default).
3. **State, markers, idempotence** (R2; PRD AC-31.2)
   **Given** a redacted Trace
   **When** inspected
   **Then** each affected Event has `redacted: true`, `redaction.applied` is true, `paths` lists the configured rule strings that matched, `env_names` lists the declared names; redacting again changes nothing; redacting a Trace that already records `env_names` unions them.
4. **Runner integration and equivalence** (R2; spine AD-10, AD-13; PRD AC-19.2, AC-34.2)
   **Given** `run` on the example with the planted `api_key` and `OPENAI_API_KEY` set to a known value present in a fixture output
   **When** it runs
   **Then** the summary shows `[REDACTED]` in both places; and `evaluate_scenario(scenario, redact_trace(trace, rules, secret_values), defaults)` through the API equals the runner's `ScenarioResult`.

## Boundaries

- No file writes (story 3).
- Must not change: `scrub_text` from epic 3; the console filter reuses the same `secret_values`.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-05-trace-import-export-and-offline-replay/epic-05-trace-import-export-and-offline-replay.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-10, AD-13
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-31, AC-31.1 to AC-31.4, AC-19.2

## Notes

- Files: `src/agentproof/redaction/rules.py`, `src/agentproof/redaction/apply.py` (`redact`), `src/agentproof/runner/pipeline.py` (replace the placeholder; resolve `redact.env`), `src/agentproof/__init__.py` (`redact_trace`).
- Tests: `tests/unit/redaction/test_redact.py` (keys, paths, env values, markers, state, idempotence, merge), `tests/integration/test_run_redacts.py`.
- Depends on: story 1 (gate) and 4.7 (pipeline). Risk: high; this is the privacy promise.
- Done when: criteria 1 to 4 pass.
