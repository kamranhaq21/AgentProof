---
id: 2
type: story
title: "parse_trace, load_trace, and the trace validate command"
parent: epic-04-deterministic-assertion-engine
covers: [R2]
after: ["2.3", "3.1", "3.3"]
hitl: false
risk: medium
refined: true
---

# parse_trace, load_trace, and the trace validate command

## Description

The import side of the Trace contract. The Fixture Agent (story 6) and Replay (epic 5) both read Traces through this function, so every path into a Trace object enforces the same rules.

## Requirements

1. **parse_trace** (R2; spine AD-3, AD-15; PRD AC-7.1 to AC-7.3)
   **Given** `parse_trace(data, source=)`
   **When** given bytes or text
   **Then** it parses with `json.loads`, raises `TraceFormatError` naming the source and position on invalid JSON, raises `UnsupportedVersionError` naming both versions when `version` is not in `SUPPORTED_VERSIONS["trace"]`, and otherwise returns the validated Trace with every model violation listed.
2. **load_trace** (R2; spine AD-14)
   **Given** `load_trace(path)`
   **When** the file exceeds `MAX_TRACE_BYTES`
   **Then** it raises `PathError` naming the limit before parsing; otherwise it returns `parse_trace` of the file's bytes.
3. **trace validate command** (R2; spine AD-20; PRD AC-7.4)
   **Given** `agentproof trace validate TRACE_PATH`
   **When** run on each example fixture Trace
   **Then** it exits 0 printing the Scenario id and Event count; on an unsupported version, a seq gap, a 6 MB file, and invalid JSON it exits 2 with one line per violation and no traceback.
4. **Public API** (R2; spine AD-15)
   **Given** `agentproof.__all__`
   **When** read
   **Then** it contains `parse_trace` and `load_trace`.

## Boundaries

- No export (epic 5 story 3).
- Must not change: the Trace model.

## References

- parent — _bmad-output/initiative-agentproof-mvp/tickets/epic-04-deterministic-assertion-engine/epic-04-deterministic-assertion-engine.md, section Requirements
- architecture — _bmad-output/initiative-agentproof-mvp/architecture-agentproof/architecture-agentproof.md, AD-3, AD-14, AD-15, AD-20
- prd — _bmad-output/initiative-agentproof-mvp/prd-agentproof/prd-agentproof.md, FR-7, AC-7.1 to AC-7.4

## Notes

- Files: `src/agentproof/loading/trace.py`, `src/agentproof/cli/commands/trace.py` (the `trace` group with `validate`), `src/agentproof/__init__.py`.
- Tests: `tests/unit/loading/test_parse_trace.py`, `tests/integration/cli/test_trace_validate.py` (subprocess) over `tests/fixtures/schema/v1/`.
- Depends on: 2.3, 3.1, 3.3. Risk: medium.
- Done when: criteria 1 to 4 pass on both CI platforms.
