---
id: 6
type: story
title: "init scaffolds the expense-agent example"
parent: epic-03-scenario-loader-and-cli
covers: [R2, R4]
after: [4, "2.3"]
hitl: false
risk: medium
refined: true
---

# init scaffolds the expense-agent example

## Description

The five-minute quick start starts here: one command produces a Suite and the fixture Trace files that the rest of the initiative runs, replays, reports on, and compares. The Trace files are hand-written against the epic 2 model and will be read by epic 4's Fixture Agent.

## Requirements

1. **Scaffold** (R2; PRD AC-4.1; spine Schemas seed)
   **Given** an empty directory
   **When** `agentproof init` runs
   **Then** it writes `agentproof.yaml` (the spine's Suite seed with two Scenarios: `reject-over-limit`, which will fail on `tool_not_called`, and `approve-under-limit`, which passes), `traces/reject-over-limit.trace.json`, and `traces/approve-under-limit.trace.json`, and nothing else; `defaults.adapter` is `fixture` and `defaults.fixture.deterministic` is true.
2. **Validates** (R2, R4)
   **Given** the scaffold
   **When** `agentproof validate agentproof.yaml` runs and each Trace file is loaded with `json.loads` and validated with the epic 2 Trace model in the test
   **Then** both succeed; the `reject-over-limit` Trace contains a `tool_call` to `approve_expense` at seq 1 and an `agent_finished` output containing "rejected", and it plants a fixture `api_key` argument so later epics can prove Redaction.
3. **Refuses to overwrite** (R2; PRD AC-4.2)
   **Given** a directory where `agentproof.yaml` exists
   **When** `agentproof init` runs
   **Then** it exits 2 naming `agentproof.yaml` and writes nothing.
4. **Template source** (R2)
   **Given** `examples/expense-agent/`
   **When** compared with the scaffold output
   **Then** they are identical; the command copies from the packaged template.

## Boundaries

- No `--force` (OQ-17 assumed no).
- Must not change: the Trace model; a Trace file that cannot be expressed raises a `Source conflict:` in epic 2.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-03-scenario-loader-and-cli/epic-03-scenario-loader-and-cli.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, Schemas (seed), AD-20
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-4, FR-20, UJ-4

## Notes

- Files: `examples/expense-agent/agentproof.yaml`, `examples/expense-agent/traces/*.trace.json`, `src/agentproof/cli/commands/init.py`, package data configuration in `pyproject.toml`.
- Tests: `tests/integration/cli/test_init.py` (scaffold, refuse, validate, trace model validation).
- Depends on: story 4 and 2.3. Risk: medium; package data must ship in the wheel, verified by the smoke install.
- Done when: criteria 1 to 4 pass on both CI platforms.
