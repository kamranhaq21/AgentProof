---
id: 3
type: story
title: "Trace, event, capture, redaction-state, and environment models"
parent: epic-02-data-contracts-and-schema-validation
covers: [R1, R5]
after: [1]
hitl: false
risk: high
refined: true
---

# Trace, event, capture, redaction-state, and environment models

## Description

The integration surface for every stack: the Trace and its Events. Everything an adapter, the Fixture Agent, or a user's exported file produces is validated by these models, so the contiguity, timestamp, and allowlist rules live here, not in a loader.

## Requirements

1. **Trace shape** (R1; spine AD-5, Schemas seed; PRD FR-5)
   **Given** the spine's Trace JSON seed
   **When** it is validated
   **Then** it yields a Trace with `version == 1`, `run_id`, `scenario_id`, `started_at`, `ended_at`, `agent`, `adapter`, optional `model` with optional `provider` and `name`, `capture`, `environment`, `redaction`, and `events`; a Trace without `model` values validates (PRD AC-5.1).
2. **Events** (R1; spine AD-5; PRD AC-5.2, AC-7.2)
   **Given** an events list
   **When** it is validated
   **Then** each event has `seq`, `type` from the eleven-value literal, and optional `timestamp`, `duration_ms`, `tool` (`name`, optional `call_id`), `arguments`, `result`, `status`, `error` (`type`, `message`, `unhandled`), `output`, `redacted` default false, `metadata` default empty; `seq` must run 0, 1, 2, ... with no gap, duplicate, or disorder, and an unknown `type` or a gap raises naming the index.
3. **Timestamps** (R1; spine AD-3; PRD AC-5.3)
   **Given** `started_at`, `ended_at`, or an event `timestamp`
   **When** validated
   **Then** a string matching `RFC3339_WITH_OFFSET` (including a trailing `Z`) is accepted and stored unchanged, and a naive timestamp or a non-string is rejected.
4. **Capture, redaction state, environment** (R1; spine AD-5, AD-9, AD-10; PRD AC-5.5, AC-5.6, AC-31.2)
   **Given** a Trace dict
   **When** validated
   **Then** `capture` defaults to `Capture(tool_calls="unknown")` when absent, `redaction` is `RedactionState(applied, paths, env_names)` defaulting to not applied, and `environment` accepts only `package_version`, `python_version`, `os`, `source_revision`, rejecting any other key naming it.

## Boundaries

- No file reading; no redaction logic (epic 5).
- Must not change: `constants`, `common`.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-02-data-contracts-and-schema-validation/epic-02-data-contracts-and-schema-validation.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-3, AD-5, AD-9, AD-10, Schemas (seed)
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-5, FR-7, FR-8, AC-5.1 to AC-5.6

## Notes

- Files: `src/agentproof/models/trace.py`.
- Tests: `tests/unit/models/test_trace.py` with a case per rule, including the eleven event types and the `Z` timestamp.
- Depends on: story 1. Risk: high; ARCH-3 (contiguous seq) is stricter than the PRD and may be relaxed later without a schema bump.
- Done when: criteria 1 to 4 pass and the spine's Trace seed validates.
