---
id: 6
type: story
title: "Adapter protocol, Fixture Agent, adapter resolution, and conformance check"
parent: epic-04-deterministic-assertion-engine
covers: [R4]
after: [2, "3.6"]
hitl: false
risk: high
refined: true
---

# Adapter protocol, Fixture Agent, adapter resolution, and conformance check

## Description

The port through which real agents will enter, and the built-in Adapter that makes every example and test credential-free. The conformance check ships publicly so third-party adapter authors can run it.

## Requirements

1. **Protocol and context** (R4; spine AD-9)
   **Given** `adapters.protocol`
   **When** imported
   **Then** `Adapter` is a `Protocol` with `name`, `version`, and `run(scenario, context) -> Trace`, and `RunContext` is a frozen dataclass with `run_id`, `started_at`, `suite_dir`, `output_dir`, `deterministic`, `logger`; both are in `agentproof.__all__`.
2. **Fixture Agent** (R4; PRD AC-20.1; spine AD-9)
   **Given** a Scenario with `trace: traces/reject-over-limit.trace.json`
   **When** the Fixture Agent runs it with `suite_dir` set
   **Then** it reads the file through `io.read_limited` relative to `suite_dir`, returns `parse_trace` of it, and raises `TraceMissingError` naming the path when `scenario.trace` is absent or the file is missing; it never reads environment variables.
3. **Resolution** (R4; spine AD-9, ARCH-7)
   **Given** `adapters.resolve(name)`
   **When** called with `fixture`, an entry-point name registered under `agentproof.adapters`, or `tests.helpers.adapters:StubAdapter`
   **Then** each returns an instance; an unknown name raises `AdapterLoadError` listing what was tried.
4. **Conformance check** (R4; PRD AC-21.5)
   **Given** `testing.adapter_conformance.check(adapter, suite)`
   **When** run against the Fixture Agent
   **Then** it passes; against a stub returning a Trace with a seq gap, a missing Capture declaration, or raising a non-taxonomy exception it fails naming the rule; it is importable from the installed wheel.

## Boundaries

- No runner (story 7); no real framework adapter (epic 11).
- Must not change: the Trace model or `parse_trace`.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-04-deterministic-assertion-engine/epic-04-deterministic-assertion-engine.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-9, AD-15
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-20, FR-21, AC-20.1, AC-21.1, AC-21.5

## Notes

- Files: `src/agentproof/adapters/protocol.py`, `src/agentproof/adapters/fixture.py`, `src/agentproof/adapters/resolve.py`, `src/agentproof/testing/adapter_conformance.py`, `pyproject.toml` (entry-point group declaration), `tests/helpers/adapters.py`.
- Tests: `tests/unit/adapters/test_fixture.py`, `tests/unit/adapters/test_resolve.py`, `tests/unit/testing/test_adapter_conformance.py`.
- Depends on: story 2 and 3.6 (the example Trace files the Fixture Agent reads, and `pyproject.toml` package data, which 3.6 edits before this story adds the entry-point group). Risk: high; ARCH-2 (sync-only) and ARCH-7 (dotted path) are built as the spine's defaults.
- Done when: criteria 1 to 4 pass.
